"""Route tests for validated exchanges: JSON response, progress and terminal stream events.

Covers S-004, S-007, S-008, S-009, S-011 and S-013 through the exchange endpoint, with a real
``ChatService`` wired to the scripted fakes in ``validation_support``. The stream is negotiated
with ``Accept: application/x-ndjson``. Records are ``{"type": "status", "message"}``,
``{"type": "answer", "answer", "citations"}`` and ``{"type": "error", "error"}``. Without that
header the endpoint keeps returning one JSON body, now with ``citations`` next to ``answer``.
"""

import json
import time
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from flask import Flask
from flask.testing import FlaskClient

from bootstrap.error_handlers import register_error_handlers
from domain.assistant.api.routes import conversation_bp
from tests.domain.assistant.validation_support import (
    DEADLINE,
    INTERRUPTED_MESSAGE,
    PROGRESS_MESSAGE,
    QUESTION,
    TIMEOUT_MESSAGE,
    CheckStep,
    Env,
    Finding,
    QueryStep,
    Verdict,
    build,
    passage,
)

pytestmark = pytest.mark.integration

NDJSON = "application/x-ndjson"
P1 = passage("P1", "The pilot started in May.")
P2 = passage("P2", "The pilot ended in July.")
MAY = Finding("The pilot started in May", 1)
SUPPORTED = "The pilot started in May [1] and ended in July [2]."
OVERSTATED = "The pilot started in May [1] and ended on July 12 [1]."
PROGRESS_DELAY_SECONDS = 5.0


@dataclass
class Outcome:
    """What a client sees, whichever response format it asked for."""

    kind: str
    message: str
    citations: list[tuple[int, str]]
    statuses: list[str]


def make_client(env: Env) -> FlaskClient:
    app = Flask(__name__)
    app.config.update(TESTING=True, SECRET_KEY="test-secret")
    user_id = str(uuid4())
    project = SimpleNamespace(owner=SimpleNamespace(id=SimpleNamespace(value=user_id)), members=[])
    app.extensions["container"] = SimpleNamespace(
        project=SimpleNamespace(
            get=SimpleNamespace(
                execute=lambda project_id: project if project_id == env.project_id else None
            )
        ),
        assistant=SimpleNamespace(chat=env.service),
    )
    register_error_handlers(app)
    app.register_blueprint(conversation_bp, url_prefix="/api/projects/<project_id>/conversations")
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    return client


def exchange_request(env: Env, fmt: str) -> dict[str, Any]:
    return dict(
        path=f"/api/projects/{env.project_id}/conversations/{env.conversation_id}/exchanges",
        json={"query": QUESTION, "context_scope": "source_library"},
        headers={"Accept": NDJSON} if fmt == "stream" else {},
    )


def pairs(citations: list[dict[str, Any]]) -> list[tuple[int, str]]:
    return [(c["key"], c["location"]) for c in citations]


def outcome(env: Env, fmt: str) -> Outcome:
    response = make_client(env).post(**exchange_request(env, fmt))
    if fmt == "json":
        body = response.get_json()
        if response.status_code == 201:
            return Outcome("answer", body["answer"], pairs(body["citations"]), [])
        return Outcome("error", body["error"], [], [])
    assert response.content_type.startswith(NDJSON)
    records = [json.loads(line) for line in response.get_data(as_text=True).splitlines() if line]
    *progress, terminal = records
    assert all(r["type"] == "status" for r in progress)
    statuses = [r["message"] for r in progress]
    if terminal["type"] == "answer":
        return Outcome("answer", terminal["answer"], pairs(terminal["citations"]), statuses)
    assert terminal["type"] == "error"
    return Outcome("error", terminal["error"], [], statuses)


formats = pytest.mark.parametrize("fmt", ["json", "stream"])


@formats
def test_s004_success_carries_only_the_corrected_answers_citations(fmt: str) -> None:
    mismatched = "The pilot started in May [1] and ended in July [1]."
    corrected = "The pilot started in May [1] and ended in July [2]."
    env = build(
        drafts=[mismatched],
        searches=[QueryStep([P1, P2])],
        checks=[
            CheckStep(Verdict(verified=(MAY,), unresolved=("July end cites P1, not P2",))),
            CheckStep(Verdict()),
        ],
        revisions=[corrected],
    )

    result = outcome(env, fmt)

    assert result == Outcome("answer", corrected, [(1, "P1"), (2, "P2")], [])


@formats
def test_s008_returns_verified_findings_at_the_deadline(fmt: str) -> None:
    env = build(
        drafts=[OVERSTATED],
        searches=[QueryStep([P1]), QueryStep([P1, P2], at=DEADLINE + 1)],
        checks=[
            CheckStep(
                Verdict(verified=(MAY,), unresolved=("end date",), missing_evidence="when it ended")
            )
        ],
    )

    result = outcome(env, fmt)

    assert result.kind == "answer"
    assert result.citations == [(1, "P1")]
    assert "May" in result.message
    assert "end date" in result.message.lower()
    assert "July 12" not in result.message


@formats
def test_s009_reports_a_timeout_when_nothing_was_verified(fmt: str) -> None:
    env = build(
        drafts=[SUPPORTED],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(Verdict(), at=DEADLINE + 1)],
    )

    result = outcome(env, fmt)

    assert result == Outcome("answer", TIMEOUT_MESSAGE, [], [])


@formats
def test_s011_reports_an_interrupted_validation_as_an_error(fmt: str) -> None:
    env = build(
        drafts=[SUPPORTED],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(error=RuntimeError("validator down"))],
    )

    result = outcome(env, fmt)

    assert result == Outcome("error", INTERRUPTED_MESSAGE, [], [])


def test_s011_json_error_uses_an_error_status() -> None:
    env = build(
        drafts=[SUPPORTED],
        searches=[QueryStep([P1, P2])],
        checks=[CheckStep(error=RuntimeError("validator down"))],
    )

    response = make_client(env).post(**exchange_request(env, "json"))

    assert response.status_code >= 500
    assert SUPPORTED not in response.get_data(as_text=True)


@pytest.mark.parametrize("fmt", ["json", "stream"])
@pytest.mark.parametrize("with_findings", [True, False], ids=["findings", "no-findings"])
def test_s013_a_service_error_at_the_deadline_gets_the_deadline_response(
    fmt: str,
    with_findings: bool,  # noqa: FBT001
) -> None:
    failing = CheckStep(error=RuntimeError("validator down"), at=DEADLINE)
    if with_findings:
        checks = [CheckStep(Verdict(verified=(MAY,), unresolved=("end date",))), failing]
        revisions = ["The pilot started in May [1] and ended in July."]
    else:
        checks, revisions = [failing], []
    env = build(drafts=[OVERSTATED], searches=[QueryStep([P1])], checks=checks, revisions=revisions)

    result = outcome(env, fmt)

    assert result.kind == "answer"
    assert "July 12" not in result.message
    if with_findings:
        assert result.citations == [(1, "P1")]
        assert "May" in result.message
        assert "in time" in result.message
    else:
        assert (result.message, result.citations) == (TIMEOUT_MESSAGE, [])


def test_s007_progress_arrives_after_five_seconds_while_validation_is_pending() -> None:
    env = build(drafts=[SUPPORTED], searches=[QueryStep([P1, P2])], checks=[CheckStep(Verdict())])
    check = env.validator.check

    def slow_check(**kwargs: Any) -> Verdict:  # noqa: ANN401
        time.sleep(PROGRESS_DELAY_SECONDS + 0.6)
        return check(**kwargs)

    env.validator.check = slow_check  # type: ignore[method-assign]
    client = make_client(env)

    started = time.monotonic()
    response = client.post(**exchange_request(env, "stream"), buffered=False)
    arrivals: list[tuple[float, dict[str, Any]]] = []
    for chunk in response.iter_encoded():
        for line in chunk.decode().splitlines():
            if line:
                arrivals.append((time.monotonic() - started, json.loads(line)))

    [(status_at, status), (answer_at, answer)] = arrivals
    assert status == {"type": "status", "message": PROGRESS_MESSAGE}
    assert status_at >= PROGRESS_DELAY_SECONDS
    assert status_at < answer_at
    assert answer_at >= PROGRESS_DELAY_SECONDS + 0.6
    assert answer["type"] == "answer"
    assert answer["answer"] == SUPPORTED
    assert "pilot" not in json.dumps(status)
