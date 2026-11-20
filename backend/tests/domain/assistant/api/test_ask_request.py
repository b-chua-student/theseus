"""Unit tests for the assistant AskRequest validation model."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from domain.assistant.api.requests import AskRequest


def test_defaults_to_source_library_scope() -> None:
    request = AskRequest.model_validate({"query": "Hello?"})

    assert request.context_scope == "source_library"
    assert request.source_ids is None
    assert request.manuscript_text == ""


def test_accepts_every_supported_scope() -> None:
    for scope in ("none", "manuscript", "source_library"):
        assert AskRequest.model_validate({"query": "Hi", "context_scope": scope}).context_scope == (
            scope
        )


def test_rejects_unknown_scope() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "Hi", "context_scope": "web"})


@pytest.mark.parametrize("query", ["", "   ", "\n"])
def test_rejects_empty_or_blank_query(query: str) -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": query})


def test_rejects_missing_query() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({})


def test_rejects_query_over_4000_characters() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "a" * 4001})


def test_accepts_query_of_exactly_4000_characters() -> None:
    AskRequest.model_validate({"query": "a" * 4000})


def test_rejects_manuscript_text_over_limit() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "Hi", "manuscript_text": "a" * 500_001})


def test_rejects_source_ids_that_are_not_uuids() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "Hi", "source_ids": ["not-a-uuid"]})


def test_parses_source_ids_as_uuids() -> None:
    source_id = uuid4()

    request = AskRequest.model_validate({"query": "Hi", "source_ids": [str(source_id)]})

    assert request.source_ids == [source_id]


def test_rejects_more_than_1000_source_ids() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "Hi", "source_ids": [str(uuid4())] * 1001})
