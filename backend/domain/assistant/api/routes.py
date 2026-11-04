from flask import Blueprint, current_app, jsonify, request
from flask.typing import ResponseReturnValue
from pydantic import ValidationError

from domain.assistant.models.errors import ChatUnavailableError
from domain.assistant.services.chat import ChatService
from domain.identity.api.auth.routes import login_required
from domain.manuscript.api.errors import ManuscriptNotFoundError

from .requests import AskRequest


def _chat() -> ChatService:
    chat = current_app.extensions["container"].assistant.chat
    if chat is None:
        raise ChatUnavailableError("The assistant is not configured.")
    return chat


conversation_bp = Blueprint("conversation", __name__)
indexing_bp = Blueprint("indexing", __name__)


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
        conversation_id=conversation_id,
        text=body.query,
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
