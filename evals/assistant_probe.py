"""Exercise Theseus through its real chat service using isolated, in-memory test adapters."""

from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from domain.assistant.api.requests import AskRequest
from domain.assistant.infrastructure.adapters.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from domain.assistant.models.entities import Exchange
from domain.assistant.models.value_objects import Query, RetrievedChunk
from domain.assistant.services.chat import ChatService
from tests.domain.assistant.services.test_chat_service import FakeChatModel, Library


class _Fixture(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Source(_Fixture):
    id: UUID
    text: str = Field(min_length=1)
    active: StrictBool
    indexed: StrictBool


class _Turn(_Fixture):
    query: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class _Setup(_Fixture):
    sources: list[_Source]
    prior_exchanges: list[_Turn]


class _RetrievalRule(_Fixture):
    required_source_ids: list[UUID]
    excluded_source_ids: list[UUID]
    expect_empty: StrictBool


def _routing(
    calls: list[tuple[list[Exchange], Query, list[RetrievedChunk] | None]],
    request: AskRequest,
    prior: list[_Turn],
) -> dict:
    """Check the final turn and prior exchanges actually delivered to the fake."""
    issues = []
    question = request.query.strip()
    observed_query = calls[-1][1].text if calls else None
    if len(calls) != 1:
        issues.append(f"expected one model call, observed {len(calls)}")
    if request.context_scope == "manuscript":
        draft = request.manuscript_text.strip() or "(empty manuscript)"
        suffix = f"Current manuscript:\n{draft}\n\nQuestion: {question}"
        if observed_query is None or not observed_query.endswith(suffix):
            issues.append("current manuscript or question missing from the model query")
    elif observed_query != question:
        issues.append("expected the plain user question")

    history = [
        {"query": turn.query.text, "answer": turn.answer.text if turn.answer else None}
        for turn in (calls[-1][0] if calls else [])
    ]
    expected_history = [{"query": t.query.strip(), "answer": t.answer.strip()} for t in prior]
    if history != expected_history:
        issues.append("prior exchanges differ from the seeded history")
    return {
        "passed": not issues,
        "reason": "; ".join(issues) or "The model received the intended query and history.",
        "evidence": {"calls": len(calls), "model_query": observed_query, "history": history},
    }


def _retrieval(
    context: list[RetrievedChunk] | None,
    sources_by_runtime_id: dict[UUID, _Source],
    rule: _RetrievalRule,
) -> dict:
    """Map retrieved chunks back to fixture IDs and evaluate inclusion and exclusion."""
    observed = []
    ids = set()
    issues = []
    for chunk in context or []:
        source = sources_by_runtime_id.get(chunk.doc_ref_id.value)
        if source is None:
            issues.append(f"unexpected source outside the case: {chunk.doc_ref_id.value}")
        else:
            ids.add(source.id)
            if chunk.text != source.text:
                issues.append(f"chunk text differs from the indexed passage for {source.id}")
        observed.append({"source_id": str(source.id) if source else None, "text": chunk.text})

    if context is None:
        issues.append("model did not receive a chunk list")
    elif (len(context) == 0) != rule.expect_empty:
        issues.append("unexpected empty/nonempty chunk list")
    missing = sorted(set(rule.required_source_ids) - ids)
    excluded = sorted(set(rule.excluded_source_ids) & ids)
    if missing:
        issues.append("missing required source IDs: " + ", ".join(map(str, missing)))
    if excluded:
        issues.append("received excluded source IDs: " + ", ".join(map(str, excluded)))
    return {
        "passed": not issues,
        "reason": "; ".join(issues) or "Retrieved passages satisfy the source-ID expectations.",
        "evidence": {"chunks": observed if context is not None else None},
    }


def probe(case: dict, reply: str) -> dict:
    """Run one control in a fresh project, with the answer key kept out of model inputs."""
    raw_request = case["input"]
    request = AskRequest.model_validate(raw_request)
    unknown_fields = set(raw_request) - set(AskRequest.model_fields)
    if unknown_fields:
        raise ValueError(f"Unknown input fields: {sorted(unknown_fields)}")
    setup = _Setup.model_validate(case["setup"])
    rule = _RetrievalRule.model_validate(case["expected"]["retrieval"])

    declared = {source.id for source in setup.sources}
    if len(declared) != len(setup.sources):
        raise ValueError("Duplicate fixture source IDs.")
    required, excluded = set(rule.required_source_ids), set(rule.excluded_source_ids)
    if not (required | excluded | set(request.source_ids or [])) <= declared:
        raise ValueError("Source selection or expectations reference an undeclared fixture ID.")
    if required & excluded or (rule.expect_empty and required):
        raise ValueError("Conflicting retrieval expectations.")

    project = str(uuid4())
    library = Library(project)
    runtime_ids = {}
    sources_by_runtime_id = {}
    for source in setup.sources:
        ref = library.add_source(source.text, indexed=source.indexed, active=source.active)
        runtime_ids[source.id] = str(ref.value)
        sources_by_runtime_id[ref.value] = source

    model = FakeChatModel()
    service = ChatService(
        InMemoryConversationRepository(),
        model,
        embedding_generator=library.embedder,
        vector_store=library.vectors,
        document_repository=library.documents,
        source_ids=lambda _project: list(library.active),
    )
    conversation_id = str(service.start(project).value)
    for turn in setup.prior_exchanges:
        model.answer = turn.answer
        service.ask(conversation_id, turn.query, context_scope="none")
    model.calls.clear()
    model.answer = reply
    selected = request.source_ids
    answer = service.ask(
        conversation_id,
        request.query,
        context_scope=request.context_scope,
        manuscript_text=request.manuscript_text,
        source_ids=None if selected is None else [runtime_ids[sid] for sid in selected],
        project_id=project,
    )
    context = model.calls[-1][2] if model.calls else None
    return {
        "answer": answer.text,
        "routing": _routing(model.calls, request, setup.prior_exchanges),
        "retrieval": _retrieval(context, sources_by_runtime_id, rule),
    }
