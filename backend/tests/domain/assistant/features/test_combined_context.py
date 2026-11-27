"""Step definitions for the ``@service`` and ``@acceptance`` combined-context scenarios (T-001).

Acceptance scenarios are checked here through the inputs the recording model receives. The
wording of a real Gemini answer is reviewed manually or by eval (T-012), outside CI.
"""

from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from domain.assistant.models.value_objects import DocumentRefId
from tests.domain.assistant.features.combined_context_support import (
    NO_MATCH,
    OMITTED,
    RELEVANCE_THRESHOLD,
    RELEVANT,
    UNAVAILABLE,
    CombinedContextHarness,
    Passage,
    quoted,
)

FEATURE = Path(__file__).resolve().parents[5] / "specs/assistant/combined_context/gherkin.feature"

scenarios(str(FEATURE))

GENERIC_CLAIM = "The treatment shortens recovery."
CAPACITY_SOURCES = ("Alpha", "Beta", "Gamma")


@pytest.fixture
def ctx() -> CombinedContextHarness:
    """Provide a fresh project, library and conversation for each scenario."""
    return CombinedContextHarness()


def excerpt_sources(ctx: CombinedContextHarness) -> set[str]:
    """Return the titles of the sources whose passages the model received."""
    return ctx.titles({ref for ref, _ in ctx.model.last.excerpts})


def excerpts_from(ctx: CombinedContextHarness, title: str) -> list[str]:
    """Return the passage texts the model received from one source."""
    ref = ctx.ref(title)
    return [text for source, text in ctx.model.last.excerpts if source == ref]


def outcome(ctx: CombinedContextHarness, title: str) -> str | None:
    """Return the outcome status the model received for one source."""
    return ctx.model.last.outcomes.get(ctx.ref(title))


# ---- Background ----


@given("I have a manuscript open in the editor with the Assistant chat panel")
def manuscript_open(ctx: CombinedContextHarness) -> None:
    assert ctx.draft


@given(parsers.re(r"my project has indexed library sources (?P<names>.+)"))
def indexed_sources(ctx: CombinedContextHarness, names: str) -> None:
    for title in quoted(names):
        ctx.add_source(title)


# ---- Given: draft and passages ----


@given("my manuscript says the trial enrolled 18 participants")
def draft_enrollment(ctx: CombinedContextHarness) -> None:
    ctx.draft = "The trial enrolled 18 participants."


@given('"Methods" reports 18 participants and "Replication" reports 24 for the same trial')
def enrollment_reports(ctx: CombinedContextHarness) -> None:
    ctx.set_passages("Methods", Passage("The trial enrolled 18 participants.", RELEVANT))
    ctx.set_passages("Replication", Passage("The same trial enrolled 24 participants.", RELEVANT))


@given('the unselected source "Pilot" also reports 18 participants')
def pilot_enrollment(ctx: CombinedContextHarness) -> None:
    ctx.set_passages("Pilot", Passage("The pilot enrolled 18 participants.", 0.99))


@given(parsers.re(r'my draft says "(?P<first>[^"]+)" and "(?P<second>[^"]+)"'))
def draft_two_claims(ctx: CombinedContextHarness, first: str, second: str) -> None:
    ctx.draft = f"{first}. {second}."


@given('"Methods" reports that children recovered in 7 days')
def methods_recovery(ctx: CombinedContextHarness) -> None:
    ctx.set_passages("Methods", Passage("Children recovered in 7 days.", RELEVANT))


@given("the manuscript contains a claim about sample size")
def draft_sample_size(ctx: CombinedContextHarness) -> None:
    ctx.draft = "We analysed 12 samples."


@given('"Methods" and "Pilot" each contain a matching passage')
def methods_and_pilot_match(ctx: CombinedContextHarness) -> None:
    for title in ("Methods", "Pilot"):
        ctx.set_passages(title, Passage(f"{title} analysed 12 samples.", RELEVANT))


@given(parsers.re(r'"(?P<name>[^"]+)" has a passage supporting the claim'))
def supporting_passage(ctx: CombinedContextHarness, name: str) -> None:
    ctx.draft = GENERIC_CLAIM
    ctx.set_passages(name, Passage(f"{name}: the treatment shortened recovery.", RELEVANT))


@given(parsers.re(r'"(?P<name>[^"]+)" became unavailable before the search'))
def became_unavailable(ctx: CombinedContextHarness, name: str) -> None:
    ctx.make_unavailable(name)


@given(parsers.re(r'"(?P<name>[^"]+)" was searched and had no relevant result'))
def searched_no_result(ctx: CombinedContextHarness, name: str) -> None:
    ctx.no_match(name)


@given(
    parsers.re(
        r'"(?P<missing>[^"]+)" is unavailable and "(?P<unmatched>[^"]+)" '
        r"(?:has|returns) no relevant passage"
    )
)
def unavailable_and_unmatched(ctx: CombinedContextHarness, missing: str, unmatched: str) -> None:
    ctx.make_unavailable(missing)
    ctx.no_match(unmatched)


@given(parsers.re(r'unselected "(?P<name>[^"]+)" contains a matching passage'))
def unselected_match(ctx: CombinedContextHarness, name: str) -> None:
    ctx.set_passages(name, Passage(f"{name}: the treatment shortened recovery.", 0.99))


@given("my manuscript says the treatment works for all adults")
def draft_all_adults(ctx: CombinedContextHarness) -> None:
    ctx.draft = "The treatment works for all adults."


@given('"Methods" reports the effect only in adults under 40')
def methods_under_40(ctx: CombinedContextHarness) -> None:
    ctx.set_passages("Methods", Passage("The effect appeared only in adults under 40.", RELEVANT))


@given(parsers.re(r'"(?P<name>[^"]+)" is searched and returns no relevant passage'))
def searched_returns_nothing(ctx: CombinedContextHarness, name: str) -> None:
    ctx.no_match(name)


@given(parsers.re(r'"(?P<name>[^"]+)" has many relevant passages'))
def many_passages(ctx: CombinedContextHarness, name: str) -> None:
    passages = [Passage(f"{name} finding {index}.", 0.95) for index in range(10)]
    ctx.set_passages(name, *passages)
    for passage in passages:
        ctx.tokens.costs[passage.text] = 30


@given(parsers.re(r'"(?P<name>[^"]+)" has one relevant passage'))
def one_passage(ctx: CombinedContextHarness, name: str) -> None:
    passage = Passage(f"{name} single finding.", 0.8)
    ctx.set_passages(name, passage)
    ctx.tokens.costs[passage.text] = 30


@given("the available context window has room for a relevant passage from each source")
def room_for_each(ctx: CombinedContextHarness) -> None:
    ctx.configure_budget(window=70)


@given(
    parsers.re(
        r'the highest cosine similarity score in "(?P<name>[^"]+)" for my question '
        r"is below the configured relevance threshold"
    )
)
def below_threshold(ctx: CombinedContextHarness, name: str) -> None:
    ctx.set_passages(name, Passage(f"{name} near miss.", RELEVANCE_THRESHOLD - 0.01))
    ctx.options["relevance_threshold"] = RELEVANCE_THRESHOLD


@given("each selected source has one relevant passage")
def each_one_passage(ctx: CombinedContextHarness) -> None:
    for title in ctx.selected:
        ctx.set_passages(title, Passage(f"{title} relevant finding.", RELEVANT))


@given(
    parsers.re(
        r'the remaining evidence budget fits the passage from "(?P<fits>[^"]+)" '
        r'but the passage from "(?P<exceeds>[^"]+)" exceeds it'
    )
)
def budget_fits_one(ctx: CombinedContextHarness, fits: str, exceeds: str) -> None:
    ctx.tokens.costs[f"{fits} relevant finding."] = 40
    ctx.tokens.costs[f"{exceeds} relevant finding."] = 150
    ctx.configure_budget(window=100)


@given(
    "three selected sources have matching passages that cannot fit alongside "
    "a fourth source's admitted passage"
)
def capacity_sources(ctx: CombinedContextHarness) -> None:
    for title in (*CAPACITY_SOURCES, "Delta"):
        ctx.add_source(title)
        text = f"{title} matching passage."
        ctx.set_passages(title, Passage(text, RELEVANT if title == "Delta" else 0.85))
        ctx.tokens.costs[text] = 50 if title == "Delta" else 200
    ctx.check_only(["Delta", *CAPACITY_SOURCES])


@given(
    parsers.re(
        r"the remaining input budget fits (?P<records>\d+) of their three named outcome records"
    )
)
def outcome_budget(ctx: CombinedContextHarness, records: str) -> None:
    for title in CAPACITY_SOURCES:
        ctx.tokens.costs[title] = 10
    ctx.configure_budget(window=50 + 10 * int(records) + 5, reserve=5)


# ---- Given: selection ----


@given(parsers.re(r'I selected (?P<names>.+?)(?P<web_off> with "Web" unchecked)?'))
def selected(ctx: CombinedContextHarness, names: str, web_off: str | None) -> None:
    ctx.select(quoted(names), web_off=bool(web_off))


@given(parsers.re(r'(?P<names>"[^"]+"(?:, "[^"]+")*(?: and "[^"]+")?) are checked'))
def are_checked(ctx: CombinedContextHarness, names: str) -> None:
    ctx.check_only(quoted(names))


@given(
    parsers.re(
        r'(?P<names>"[^"]+"(?:, "[^"]+")*(?: and "[^"]+")?) are checked '
        r'and "(?P<off>[^"]+)" is unchecked'
    )
)
def checked_and_unchecked(ctx: CombinedContextHarness, names: str, off: str) -> None:
    checked = quoted(names)
    assert off not in checked
    ctx.check_only(checked)


@given(parsers.re(r'(?P<names>"[^"]+"(?:, "[^"]+")*(?: and "[^"]+")?) are selected'))
def are_selected(ctx: CombinedContextHarness, names: str) -> None:
    ctx.check_only(quoted(names))


@given(parsers.re(r'I quoted "(?P<quote>[^"]+)" from the editor'))
def quoted_passage(ctx: CombinedContextHarness, quote: str) -> None:
    ctx.quote_from_editor(quote)


@given("the request also names a source ID that belongs to another project")
def foreign_source(ctx: CombinedContextHarness) -> None:
    other_project = DocumentRefId.new().value
    ref = ctx.add_source("Foreign", project_id=other_project)
    ctx.vectors.passages[ref] = [Passage("Foreign project: 12 samples.", 0.99)]
    ctx.extra_ids.append(str(ref.value))


@given('the project has 1,001 indexed sources including "Methods", "Replication" and "Pilot"')
def large_library(ctx: CombinedContextHarness) -> None:
    for index in range(1001 - len(ctx.ids)):
        ctx.add_source(f"Source {index:04d}")
    assert len(ctx.ids) == 1001


@given('I chose "All indexed sources"')
def chose_all(ctx: CombinedContextHarness) -> None:
    ctx.choose_all_indexed()


@given(parsers.re(r'a new source "(?P<name>[^"]+)" finishes indexing afterward'))
def indexed_afterward(ctx: CombinedContextHarness, name: str) -> None:
    ctx.add_source(name)


# ---- When ----


@when(parsers.re(r'I ask "(?P<question>[^"]+)"'))
def ask_quoted(ctx: CombinedContextHarness, question: str) -> None:
    ctx.ask(question)


@when(parsers.re(r"I ask about sample size with (?P<selection>.+)"))
def ask_with_selection(ctx: CombinedContextHarness, selection: str) -> None:
    selections = {
        "Manuscript alone": ["Manuscript"],
        "only Methods selected": ["Methods"],
        "only Web selected": ["Web"],
    }
    ctx.check_only(selections[selection])
    ctx.ask("What sample size does the study use?")


@when("I ask about sample size")
def ask_sample_size(ctx: CombinedContextHarness) -> None:
    ctx.ask("What sample size does the study use?")


@when(parsers.re(r"I ask (?P<question>(?:which|whether) .+)"))
def ask_generic(ctx: CombinedContextHarness, question: str) -> None:
    ctx.ask(question[0].upper() + question[1:] + "?")


@when('I uncheck "Web" and ask whether my claim is supported')
def uncheck_web_and_ask(ctx: CombinedContextHarness) -> None:
    ctx.web = False
    ctx.ask("Is my claim supported?")


@when('I choose "All indexed sources" and ask about sample size')
def choose_all_and_ask(ctx: CombinedContextHarness) -> None:
    ctx.choose_all_indexed()
    ctx.ask("What sample size does the study use?")


@when(parsers.re(r'the Assistant completes the search of "(?P<name>[^"]+)" for my question'))
def complete_search(ctx: CombinedContextHarness, name: str) -> None:
    ctx.ask(f"What does {name} report about my claim?")
    assert ctx.ref(name) in ctx.vectors.searched


# ---- Then: answer inputs ----


@then(
    parsers.re(
        r'one answer identifies "(?P<name>[^"]+)" as supporting the draft\'s figure of '
        r"(?P<figure>\d+)"
    )
)
def identifies_support(ctx: CombinedContextHarness, name: str, figure: str) -> None:
    assert len(ctx.model.calls) == 1
    assert f"{figure} participants" in ctx.model.last.draft
    assert any(figure in text for text in excerpts_from(ctx, name))


@then(parsers.re(r'it explains that "(?P<name>[^"]+)" reports (?P<figure>\d+) for the same trial'))
def explains_conflict(ctx: CombinedContextHarness, name: str, figure: str) -> None:
    assert any(figure in text for text in excerpts_from(ctx, name))


@then(
    parsers.re(r'no passage from "(?P<name>[^"]+)" is supplied to the model or used in the answer')
)
def nothing_from_unselected(ctx: CombinedContextHarness, name: str) -> None:
    assert name not in excerpt_sources(ctx)
    assert str(ctx.ref(name).value) not in ctx.cited_sources()


@then(
    parsers.re(
        r"the answer compares the quoted (?P<quoted_days>\d+) days for children with the "
        r'(?P<reported>\d+) days reported by "(?P<name>[^"]+)"'
    )
)
def compares_quote(ctx: CombinedContextHarness, quoted_days: str, reported: str, name: str) -> None:
    assert f"{quoted_days} days" in ctx.model.last.quote
    assert any(f"{reported} days" in text for text in excerpts_from(ctx, name))


@then(parsers.re(r"it attributes the (?P<days>\d+)-day figure to the quoted passage"))
def attributes_quote(ctx: CombinedContextHarness, days: str) -> None:
    assert ctx.quote is not None
    assert ctx.model.last.quote == ctx.quote
    assert f"{days} days" not in ctx.model.last.question


@then(
    parsers.re(
        r"the model receives (?P<draft>the current draft|no text) as new manuscript material"
    )
)
def receives_draft(ctx: CombinedContextHarness, draft: str) -> None:
    expected = ctx.draft if draft == "the current draft" else ""
    assert ctx.model.last.draft == expected


@then(parsers.re(r"library retrieval (?P<behavior>is skipped|searches only \w+)"))
def retrieval_behavior(ctx: CombinedContextHarness, behavior: str) -> None:
    if behavior == "is skipped":
        assert ctx.vectors.searched == set()
    else:
        assert ctx.titles(ctx.vectors.searched) == {behavior.removeprefix("searches only ")}


@then(parsers.re(r'the answer cites the supporting passage from "(?P<name>[^"]+)"'))
def cites_support(ctx: CombinedContextHarness, name: str) -> None:
    assert excerpts_from(ctx, name)
    assert str(ctx.ref(name).value) in ctx.cited_sources()


@then(parsers.re(r"it tells me (?P<explanation>.+)"))
def tells_gap(ctx: CombinedContextHarness, explanation: str) -> None:
    expected = {
        "Replication could not be checked": UNAVAILABLE,
        "no relevant passage was found in Replication": NO_MATCH,
    }
    assert outcome(ctx, "Replication") == expected[explanation]


@then(parsers.re(r'the Assistant uses no evidence from "(?P<name>[^"]+)"'))
def no_evidence_from(ctx: CombinedContextHarness, name: str) -> None:
    assert name not in excerpt_sources(ctx)
    assert ctx.ref(name) not in ctx.vectors.searched


@then("the answer says the claim could not be verified from the selection")
def cannot_verify(ctx: CombinedContextHarness) -> None:
    assert ctx.model.last.excerpts == []
    assert set(ctx.model.last.outcomes) == {ctx.ref(title) for title in ctx.selected}


@then("it identifies the unavailable source and the source searched without a match")
def identifies_gaps(ctx: CombinedContextHarness) -> None:
    assert sorted(ctx.model.last.outcomes.values()) == sorted([UNAVAILABLE, NO_MATCH])


@then(
    parsers.re(r'it neither labels the claim contradicted nor uses evidence from "(?P<name>[^"]+)"')
)
def no_contradiction(ctx: CombinedContextHarness, name: str) -> None:
    assert name not in excerpt_sources(ctx)
    assert ctx.ref(name) not in ctx.vectors.searched


@then(parsers.re(r'the exchange carries the quote "(?P<quote>[^"]+)" exactly as written'))
def carries_quote(ctx: CombinedContextHarness, quote: str) -> None:
    assert ctx.model.last.quote == quote


@then("the quote is separate from the question text")
def quote_separate(ctx: CombinedContextHarness) -> None:
    assert ctx.quote is not None
    assert ctx.model.last.quote == ctx.quote
    assert ctx.quote not in ctx.model.last.question


@then("the other project's source is not searched")
def foreign_not_searched(ctx: CombinedContextHarness) -> None:
    foreign = {DocumentRefId.from_str(value) for value in ctx.extra_ids}
    assert not foreign & ctx.vectors.searched


@then("no passage from it is supplied to the model")
def nothing_from_foreign(ctx: CombinedContextHarness) -> None:
    foreign = {DocumentRefId.from_str(value) for value in ctx.extra_ids}
    assert not foreign & {ref for ref, _ in ctx.model.last.excerpts}


@then(parsers.re(r'the answer says "(?P<name>[^"]+)" supports the claim only for adults under 40'))
def qualifies(ctx: CombinedContextHarness, name: str) -> None:
    assert "all adults" in ctx.model.last.draft
    assert any("adults under 40" in text for text in excerpts_from(ctx, name))


@then(parsers.re(r'it does not describe "(?P<name>[^"]+)" as contradicting the claim'))
def not_contradicting(ctx: CombinedContextHarness, name: str) -> None:
    assert outcome(ctx, name) is None
    assert excerpts_from(ctx, name)


@then(parsers.re(r'the model receives "(?P<name>[^"]+)" marked unavailable'))
def marked_unavailable(ctx: CombinedContextHarness, name: str) -> None:
    assert outcome(ctx, name) == UNAVAILABLE


@then(parsers.re(r'the model receives "(?P<name>[^"]+)" marked as searched without a match'))
def marked_no_match(ctx: CombinedContextHarness, name: str) -> None:
    assert outcome(ctx, name) == NO_MATCH


@then(parsers.re(r'the model receives no passage from "(?P<name>[^"]+)"'))
def no_passage_from(ctx: CombinedContextHarness, name: str) -> None:
    assert not excerpts_from(ctx, name)


@then("the answer draws only on the manuscript and selected source for its factual findings")
def web_off_grounding(ctx: CombinedContextHarness) -> None:
    assert ctx.model.last.web is False
    assert ctx.model.last.draft == ctx.draft
    assert excerpt_sources(ctx) <= set(ctx.selected)


@then(parsers.re(r'the selection still includes "(?P<first>[^"]+)" and "(?P<second>[^"]+)"'))
def selection_kept(ctx: CombinedContextHarness, first: str, second: str) -> None:
    saved = ctx.saved_conversation()
    source_ids = saved.get("source_ids")
    assert isinstance(source_ids, list)
    for name in (first, second):
        if name == "Manuscript":
            assert saved.get("manuscript") is True
        else:
            assert str(ctx.ref(name).value) in source_ids


@then(
    parsers.re(r'the answer names "(?P<name>[^"]+)" and reports that no relevant passage was found')
)
def names_no_match(ctx: CombinedContextHarness, name: str) -> None:
    assert outcome(ctx, name) == NO_MATCH


@then("it says the claim could not be verified from the selection")
def says_cannot_verify(ctx: CombinedContextHarness) -> None:
    assert ctx.model.last.excerpts == []


@then(parsers.re(r'any general explanation is distinguished from evidence from "(?P<name>[^"]+)"'))
def web_knowledge_labelled(ctx: CombinedContextHarness, name: str) -> None:
    assert ctx.model.last.web is True
    assert not excerpts_from(ctx, name)


@then("the exchange carries no other manuscript text")
def no_other_draft(ctx: CombinedContextHarness) -> None:
    assert ctx.model.last.draft == ""
    for sentence in ctx.draft.split(". "):
        if sentence.strip(". ") != ctx.quote:
            assert sentence.strip(". ") not in ctx.model.last.question


# ---- Then: retrieval coverage and budget ----


@then("the exchange selects all 1,001 sources")
def selects_all(ctx: CombinedContextHarness) -> None:
    source_ids = ctx.saved_conversation().get("source_ids")
    assert isinstance(source_ids, list)
    assert len(source_ids) == 1001


@then("retrieval attempts to check all 1,001 sources")
def searches_all(ctx: CombinedContextHarness) -> None:
    assert ctx.vectors.searched == set(ctx.ids.values())


@then("no selected source is silently dropped")
def none_dropped(ctx: CombinedContextHarness) -> None:
    reported = {ref for ref, _ in ctx.model.last.excerpts} | set(ctx.model.last.outcomes)
    assert reported == {ctx.ref(title) for title in ctx.selected}


@then(parsers.re(r'"(?P<name>[^"]+)" is unchecked and is not searched'))
def not_selected_or_searched(ctx: CombinedContextHarness, name: str) -> None:
    assert name not in ctx.selected
    assert ctx.ref(name) not in ctx.vectors.searched


@then(parsers.re(r"(?P<names>.+) are still searched"))
def still_searched(ctx: CombinedContextHarness, names: str) -> None:
    assert set(quoted(names)) <= ctx.titles(ctx.vectors.searched)


@then(parsers.re(r'checking "(?P<name>[^"]+)" makes it searchable in my next exchange'))
def searchable_next(ctx: CombinedContextHarness, name: str) -> None:
    ctx.selected.append(name)
    ctx.vectors.queries.clear()
    ctx.ask("What sample size does the study use?")
    assert ctx.ref(name) in ctx.vectors.searched


@then(parsers.re(r'both "(?P<first>[^"]+)" and "(?P<second>[^"]+)" are searched'))
def both_searched(ctx: CombinedContextHarness, first: str, second: str) -> None:
    assert {first, second} <= ctx.titles(ctx.vectors.searched)


@then(parsers.re(r'the model receives the relevant passage from "(?P<name>[^"]+)"'))
def receives_passage(ctx: CombinedContextHarness, name: str) -> None:
    assert excerpts_from(ctx, name)


@then("both sources are searched")
def both_sources_searched(ctx: CombinedContextHarness) -> None:
    assert set(ctx.selected) <= ctx.titles(ctx.vectors.searched)


def admitted_cost(ctx: CombinedContextHarness) -> int:
    """Return the scripted token cost of the excerpts and outcome records the model received."""
    excerpt_cost = sum(ctx.tokens.count(text) for _, text in ctx.model.last.excerpts)
    record_cost = sum(ctx.tokens.count(title) for title in ctx.titles(set(ctx.model.last.outcomes)))
    return excerpt_cost + record_cost


@then(
    parsers.re(
        r"the model request stays within budget and includes only the passage from "
        r'"(?P<name>[^"]+)" as library evidence'
    )
)
def within_budget(ctx: CombinedContextHarness, name: str) -> None:
    window = ctx.options["context_window"]
    assert isinstance(window, int)
    assert admitted_cost(ctx) <= window
    assert excerpt_sources(ctx) == {name}


@then(parsers.re(r'the answer names "(?P<name>[^"]+)" as a match whose evidence could not fit'))
def names_omitted(ctx: CombinedContextHarness, name: str) -> None:
    assert outcome(ctx, name) == OMITTED
    assert not excerpts_from(ctx, name)


@then("the model request including the reserved response stays within the context window")
def within_window(ctx: CombinedContextHarness) -> None:
    window, reserve = ctx.options["context_window"], ctx.options["response_reserve"]
    assert isinstance(window, int) and isinstance(reserve, int)
    assert admitted_cost(ctx) + reserve <= window


@then(
    parsers.re(
        r"the model receives (?P<records>\d+) complete outcome records and the admitted passage"
    )
)
def receives_records(ctx: CombinedContextHarness, records: str) -> None:
    received = ctx.model.last.outcomes
    assert len(received) == int(records)
    assert all(status == OMITTED for status in received.values())
    assert excerpt_sources(ctx) == {"Delta"}


@then("the answer names all three omitted sources with the capacity reason and cites none of them")
def gap_report(ctx: CombinedContextHarness) -> None:
    answer = ctx.last.json.get("answer")
    assert isinstance(answer, str)
    lines = answer.splitlines()
    cited = ctx.cited_sources()
    for title in CAPACITY_SOURCES:
        assert any(title in line and ("space" in line or "fit" in line) for line in lines), title
        assert str(ctx.ref(title).value) not in cited


COLORS = "What colors are honeybees typically?"
LEGS = "How many legs does a honeybee have?"


def prepare_architecture(ctx: CombinedContextHarness) -> None:
    ctx.add_source("Architecture")
    ctx.no_match("Architecture")
    ctx.options["answer_validator"] = None
    ctx.model.answers.update(
        {
            COLORS: "Honeybees are typically golden brown with dark bands.",
            LEGS: "A honeybee has six legs.",
        }
    )


@given(
    "I asked a question with Web alone and then another with Web and Manuscript in the same chat"
)
def previous_web_turns(ctx: CombinedContextHarness) -> None:
    prepare_architecture(ctx)
    ctx.ask("What is a manuscript?")
    ctx.check_only(["Web", "Manuscript"])
    ctx.ask("Summarize my manuscript.")


@given(
    "I uncheck Manuscript and select a library source about architecture while keeping Web checked"
)
def select_architecture(ctx: CombinedContextHarness) -> None:
    ctx.check_only(["Web", "Architecture"])


@given("I selected only a library source about architecture with Web unchecked")
def only_architecture(ctx: CombinedContextHarness) -> None:
    prepare_architecture(ctx)
    ctx.check_only(["Architecture"])


@when(
    "I ask what colors honeybees typically are and the selected source yields no matching passage"
)
def ask_colors(ctx: CombinedContextHarness) -> None:
    ctx.ask(COLORS)


@then("the answer describes typical honeybee colors as general knowledge")
def answers_colors(ctx: CombinedContextHarness) -> None:
    assert "**General knowledge**" in str(ctx.last.json["answer"])
    assert ctx.model.answers[COLORS] in str(ctx.last.json["answer"])
    assert ctx.model.last.web and not ctx.model.last.excerpts


@then("it names the source that yielded no match and includes no library citation")
@then("the answer names the source and says the selection could not verify the answer")
def names_architecture_gap(ctx: CombinedContextHarness) -> None:
    assert "Architecture: was searched and no relevant passage was found" in str(
        ctx.last.json["answer"]
    )
    assert not ctx.cited_sources()


@when("I uncheck that source and ask how many legs a honeybee has in the same chat")
def back_to_web(ctx: CombinedContextHarness) -> None:
    ctx.check_only(["Web"])
    ctx.ask(LEGS)


@then("the answer says a honeybee has six legs without a library citation or a source gap report")
def answers_legs(ctx: CombinedContextHarness) -> None:
    assert ctx.last.json["answer"] == ctx.model.answers[LEGS]
    assert not ctx.cited_sources()
    assert ctx.model.last.web and not ctx.model.last.outcomes


@then("it supplies no general-knowledge answer or library citation")
def no_general_answer(ctx: CombinedContextHarness) -> None:
    assert not ctx.model.calls
    assert not ctx.cited_sources()
