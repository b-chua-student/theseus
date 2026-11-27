"""Unit tests for the assistant AskRequest validation model."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from domain.assistant.api.requests import MAX_SOURCE_IDS, AskRequest


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


def test_accepts_more_than_1000_source_ids_without_truncating() -> None:
    ids = [str(uuid4()) for _ in range(1001)]

    request = AskRequest.model_validate({"query": "Hi", "source_ids": ids})

    assert request.source_ids is not None
    assert len(request.source_ids) == 1001
    assert request.context().source_ids == tuple(ids)


def test_rejects_a_selection_beyond_the_safety_limit() -> None:
    ids = [str(uuid4())] * (MAX_SOURCE_IDS + 1)

    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "Hi", "source_ids": ids})


def test_web_alone_keeps_scope_none_with_empty_draft_and_no_source_ids() -> None:
    request = AskRequest.model_validate(
        {"query": "Hi", "context_scope": "none", "web": True, "manuscript": False}
    )

    context = request.context()

    assert (context.scope, context.web, context.manuscript) == ("none", True, False)
    assert context.manuscript_text is None
    assert context.search_library is False


def test_web_and_manuscript_flags_are_independent_of_the_source_ids() -> None:
    source_id = str(uuid4())
    request = AskRequest.model_validate(
        {
            "query": "Hi",
            "context_scope": "source_library",
            "web": False,
            "manuscript": True,
            "manuscript_text": "Draft",
            "source_ids": [source_id],
        }
    )

    context = request.context()

    assert (context.web, context.manuscript, context.manuscript_text) == (False, True, "Draft")
    assert context.source_ids == (source_id,)
    assert context.search_library is True


def test_manuscript_flag_off_sends_no_draft_text() -> None:
    request = AskRequest.model_validate(
        {
            "query": "Hi",
            "context_scope": "source_library",
            "manuscript": False,
            "manuscript_text": "Draft",
            "source_ids": [str(uuid4())],
        }
    )

    assert request.context().manuscript_text is None


@pytest.mark.parametrize(
    ("scope", "web", "manuscript"),
    [("none", True, False), ("manuscript", False, True), ("source_library", False, False)],
)
def test_legacy_requests_without_flags_decode_from_their_scope(
    scope: str, *, web: bool, manuscript: bool
) -> None:
    context = AskRequest.model_validate(
        {"query": "Hi", "context_scope": scope, "manuscript_text": ""}
    ).context()

    assert (context.web, context.manuscript) == (web, manuscript)


def test_combined_request_uses_the_draft_and_the_selected_sources() -> None:
    source_id = uuid4()

    context = AskRequest.model_validate(
        {
            "query": "Which studies support my claim?",
            "context_scope": "source_library",
            "manuscript_text": "The trial enrolled 18 participants.",
            "source_ids": [str(source_id)],
        }
    ).context()

    assert context.manuscript_text == "The trial enrolled 18 participants."
    assert context.search_library is True
    assert context.source_ids == (str(source_id),)
    assert context.quote is None


def test_quote_travels_exactly_as_written_and_apart_from_the_question() -> None:
    quote = "  Children recovered in 5 days  "

    request = AskRequest.model_validate({"query": "How does this compare?", "quote": quote})

    assert request.context().quote == quote
    assert quote.strip() not in request.query


def test_quote_without_manuscript_shares_no_other_draft_text() -> None:
    context = AskRequest.model_validate(
        {
            "query": "How does this compare?",
            "context_scope": "source_library",
            "source_ids": [str(uuid4())],
            "quote": "Children recovered in 5 days",
        }
    ).context()

    assert context.quote == "Children recovered in 5 days"
    assert context.manuscript_text is None


@pytest.mark.parametrize("quote", [None, "", "   "])
def test_missing_or_blank_quote_means_no_quote(quote: str | None) -> None:
    assert AskRequest.model_validate({"query": "Hi", "quote": quote}).context().quote is None


def test_rejects_quote_over_limit() -> None:
    with pytest.raises(ValidationError):
        AskRequest.model_validate({"query": "Hi", "quote": "a" * 20_001})


def test_legacy_none_scope_uses_neither_draft_nor_library() -> None:
    context = AskRequest.model_validate(
        {
            "query": "Hi",
            "context_scope": "none",
            "manuscript_text": "ignored",
            "source_ids": [str(uuid4())],
        }
    ).context()

    assert context.scope == "none"
    assert context.manuscript_text is None
    assert context.search_library is False


def test_legacy_manuscript_scope_uses_the_draft_alone() -> None:
    context = AskRequest.model_validate(
        {
            "query": "Hi",
            "context_scope": "manuscript",
            "manuscript_text": "Chapter one.",
            "source_ids": [str(uuid4())],
        }
    ).context()

    assert context.scope == "manuscript"
    assert context.manuscript_text == "Chapter one."
    assert context.search_library is False


def test_legacy_source_library_scope_without_ids_searches_every_source() -> None:
    context = AskRequest.model_validate(
        {"query": "Hi", "context_scope": "source_library"}
    ).context()

    assert context.search_library is True
    assert context.source_ids is None
    assert context.manuscript_text is None
