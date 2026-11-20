from datetime import UTC

from domain.manuscript.api.errors import ManuscriptNotFoundError
from flask import Blueprint, current_app, jsonify, request, session
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from domain.assistant.models.aggregates import Conversation
from domain.assistant.models.errors import ChatUnavailableError
from domain.assistant.services.chat import ChatService
from domain.identity.api.auth.routes import login_required

from .requests import AskRequest


def _chat() -> ChatService:
    chat = current_app.extensions["container"].assistant.chat
    if chat is None:
        raise ChatUnavailableError("The assistant is not configured.")
    return chat


conversation_bp = Blueprint("conversation", __name__)
indexing_bp = Blueprint("indexing", __name__)


@conversation_bp.before_request
def check_project_access() -> ResponseReturnValue | None:
    """Require a signed-in user who owns or belongs to the project."""
    if "user_id" not in session:
        return jsonify(error="Unauthorized"), 401
    project_id = (request.view_args or {})["project_id"]
    project = current_app.extensions["container"].project.get.execute(project_id=project_id)
    if project is None or not any(
        str(member.id.value) == session["user_id"] for member in [project.owner, *project.members]
    ):
        return jsonify(error="Project not found"), 404

    return None


def _conversation_json(
    conversation: Conversation, *, include_exchanges: bool = False
) -> dict[str, object]:
    result: dict[str, object] = dict(
        id=str(conversation.id.value),
        title=conversation.exchanges[0].query.text[:100]
        if conversation.exchanges
        else "New conversation",
        started_at=conversation.started_at.replace(tzinfo=UTC).isoformat(),
        context_scope=conversation.context_scope,
        source_ids=conversation.source_ids,
    )
    if include_exchanges:
        result["exchanges"] = [
            dict(
                id=str(e.id.value),
                query=e.query.text,
                answer=e.answer.text if e.answer else None,
                asked_at=e.asked_at.replace(tzinfo=UTC).isoformat(),
            )
            for e in conversation.history
        ]
    return result


@conversation_bp.get("")
@login_required
def list_conversations(project_id: str) -> ResponseReturnValue:
    """List conversations for the given project."""
    return jsonify([_conversation_json(c) for c in _chat().list(project_id)]), 200


@conversation_bp.get("/<conversation_id>")
@login_required
def get_conversation(project_id: str, conversation_id: str) -> ResponseReturnValue:
    """Return a conversation in the given project, including its exchanges."""
    return jsonify(
        _conversation_json(_chat().get(project_id, conversation_id), include_exchanges=True)
    ), 200


@conversation_bp.post("")
@login_required
def start_conversation(project_id: str) -> ResponseReturnValue:
    """Start a new conversation in the project and return its id."""
    conversation_id = _chat().start(project_id=project_id)

    return jsonify(id=str(conversation_id.value)), 201


@conversation_bp.post("/<conversation_id>/exchanges")
@login_required
def ask(project_id: str, conversation_id: str) -> ResponseReturnValue:
    """Submit a query to a conversation and return the assistant's answer."""
    try:
        body = AskRequest.model_validate(request.get_json(silent=True) or {})
    except ValidationError as e:
        return jsonify(
            error="Invalid request", details=e.errors(include_url=False, include_context=False)
        ), 400

    answer = _chat().ask(
        project_id=project_id,
        conversation_id=conversation_id,
        text=body.query,
        context_scope=body.context_scope,
        manuscript_text=body.manuscript_text,
        source_ids=(
            [str(value) for value in body.source_ids] if body.source_ids is not None else None
        ),
    )

    return jsonify(answer=answer.text), 201


@indexing_bp.get("/<manuscript_id>/indexing-status")
@login_required
def indexing_status(project_id: str, manuscript_id: str) -> ResponseReturnValue:
    """Report the indexing status of a manuscript."""
    container = current_app.extensions["container"]

    manuscript = container.manuscript.get.execute(manuscript_id=manuscript_id)
    if manuscript is None:
        raise ManuscriptNotFoundError(f"Manuscript '{manuscript_id}' not found")

    document = container.assistant.indexing_status.execute(manuscript_id=manuscript_id)

    # A manuscript that was never saved has no IndexedDocument yet.
    if document is None:
        return jsonify(status="not_indexed", chunk_count=0, searchable=False), 200

    return jsonify(
        status=document.status.name.lower(),
        chunk_count=len(document.chunks),
        searchable=document.is_searchable,
    ), 200
