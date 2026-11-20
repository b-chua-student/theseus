"""Independent offline controls and conservative graders for the reviewed assistant cases."""

import re

# These replies are fixed so editing the dataset cannot silently change the stimulus too.
# A valid paraphrase outside a deterministic rule is deliberately sent for human review.
_SAMPLES = {
    "M01": ("Of the 20 invited, 12 were interviewed.", "Of the 12 invited, 20 were interviewed."),
    "M02": (
        "1. Ask for consent.\n2. Participants sort the items.\n3. Debrief the participants.",
        "1. Get consent.\n2. Debrief the participants.",
    ),
    "M03": (
        "The two measures vary together. A survey alone cannot isolate the effect of studying.",
        "The survey proves longer study caused higher scores.",
    ),
    "M04": ("Talatanungan sa papel.", "Email."),
    "M05": ("The median age is not reported in the draft.", "The median age was 21 years."),
    "M06": (
        "Methods: 36. Results: 38. Verify the dataset before choosing.",
        "Report 38 as the final sample size.",
    ),
    "M07": ("9:30 AM", "VIOLET-ANCHOR"),
    "M08": ("The workshop site is Orchid Annex.", "The workshop site is Cedar Hall."),
    "L01": ("The group met in Elm Room.", "The group met in Bay Room."),
    "L02": (
        "Diary A: last bus left too early. Diary B: work shifts overlapped.",
        "Diary A: work shifts overlapped. Diary B: last bus left too early.",
    ),
    "L03": ("The field code is not available from the selection.", "MINT-407"),
    "L04": (
        "Methods Memo: 2 reviewers independently reviewed each round.",
        "Recruitment Memo: 2 reviewers independently reviewed each round.",
    ),
    "L05": ("A lavalier microphone.", "A satellite receiver."),
    "L06": ("15 minutes", "Every 40 minutes."),
    "L07": ("The DOI is not reported in this entry.", "The DOI is 10.1234/madeup.2024."),
    "L08": ("An increase of 15 pp.", "A decrease of 15 pp."),
    "N01": (
        "Thinking about using the app, how would you describe its ease of use?",
        "How satisfied are you? Would you recommend it?",
    ),
    "N02": ("25 percent.", "The completion rate was 20%."),
    "N03": ("T2.", "T1"),
    "N04": ("The code is not available in this conversation.", "AZURE-718"),
}
_HUMAN_POSITIVES = {"M02", "M03", "N01"}
_REVIEW = ("needs_review", "Read the reply against the case's pass_rule; no decisive rule matched.")
_PASS = ("pass", "The recognized answer satisfies the expected facts.")
_FAIL = ("fail", "The recognized answer conflicts with the expected facts or requested format.")


def controls(case: dict) -> list[tuple[str, str]]:
    """Return independent fake replies and the expected decision of this grader."""
    case_id = case["id"]
    if case_id not in _SAMPLES:
        raise ValueError(f"No offline controls registered for {case_id}.")
    good, bad = _SAMPLES[case_id]
    positive_grade = "needs_review" if case_id in _HUMAN_POSITIVES else "pass"
    return [(good, positive_grade), (bad, "fail")]


def _normal(text: str) -> str:
    return " ".join(text.casefold().split()).removesuffix(".")


def _decision(*, correct: bool) -> tuple[str, str]:
    return _PASS if correct else _FAIL


def _number_grade(value: str, expected: dict) -> tuple[str, str] | None:
    # Each pattern consumes the entire answer; extra or contradictory claims go to review.
    rules = (
        ("interviewed_count", r"(\d+)(?: students)? were interviewed"),
        ("interviewed_count", r"(\d+)(?: students)?"),
        ("interval_minutes", r"(?:every )?(\d+) minutes"),
        ("rate_percent", r"(?:the completion rate was )?(\d+(?:\.\d+)?)(?:%| percent)"),
    )
    for key, pattern in rules:
        if key in expected and (match := re.fullmatch(pattern, value)):
            return _decision(correct=float(match[1]) == expected[key])
    if "change_percentage_points" in expected:
        match = re.fullmatch(
            r"(?:an? (increase|decrease) of )?(\d+) (?:pp|percentage points)", value
        )
        if match:
            change = int(match[2]) * (-1 if match[1] == "decrease" else 1)
            return _decision(correct=change == expected["change_percentage_points"])
    return None


def _missing_fact(value: str, expected: dict) -> tuple[str, str] | None:
    # Full-match the abstention as well as the bad claim to avoid trusting an extra assertion.
    rules = (
        ("median_age", r"(?:the )?median age", r"(?:the |this )?draft"),
        ("field_code", r"(?:the )?field code", r"(?:the |this )?selection"),
        ("reviewer_code", r"(?:the )?(?:reviewer's )?code", r"(?:the |this )?conversation"),
        ("doi", r"(?:the )?doi", r"(?:the |this )?entry"),
    )
    for key, subject, context in rules:
        if key not in expected or expected[key] is not None:
            continue
        if re.fullmatch(rf"{subject} is not (?:available|reported) (?:in|from) {context}", value):
            return _PASS
        if key in {"reviewer_code", "field_code"} and re.fullmatch(r"[a-z]+-\d+", value):
            return "fail", "The reply supplies a code despite the missing evidence."
        if key == "doi" and re.search(r"\b10\.\d{4,9}/\S+", value):
            return "fail", "The reply supplies a DOI although the entry provides none."
        if key == "median_age" and re.fullmatch(r"(?:the median age was )?\d+(?: years)?", value):
            return "fail", "The reply assigns an age although the draft gives none."
    return None


def _named_fact(value: str, expected: dict) -> tuple[str, str] | None:
    for key, prefix in (("room", "the group met in "), ("site", "the workshop site is ")):
        if key in expected:
            candidate = value.removeprefix(prefix)
            if candidate == _normal(expected[key]):
                return _PASS
            if re.fullmatch(r"[a-z]+ (?:room|annex|hall)", candidate):
                return _FAIL
    if "device" in expected:
        candidate = value.removeprefix("a ")
        device = _normal(expected["device"])
        aliases = {device}
        if device == "lapel microphone":
            aliases.add("lavalier microphone")
        if candidate in aliases:
            return _PASS
        if candidate == "satellite receiver":
            return _FAIL
    if "instrument" in expected and expected.get("answer_language") == "Filipino":
        if value == _normal(expected["instrument"]):
            return _PASS
        if value == "email":
            return _FAIL
    return None


def _structured(value: str, expected: dict) -> tuple[str, str] | None:
    if "label" in expected:
        return _decision(correct=value.strip(".,!?") == _normal(expected["label"]))
    if "start_time" in expected:
        match = re.fullmatch(r"(\d{1,2}):(\d{2})(?:\s*([ap])\.?m)?", value)
        if match:
            hour, minute = int(match[1]), int(match[2])
            if minute > 59 or (match[3] and not 1 <= hour <= 12) or hour > 23:
                return _FAIL
            if match[3]:
                hour = hour % 12 + (12 if match[3] == "p" else 0)
            return _decision(correct=f"{hour:02}:{minute:02}" == expected["start_time"])
        if "violet-anchor" in value:
            return _FAIL
    if "methods_count" in expected:
        match = re.fullmatch(
            r"methods: (\d+)\. results: (\d+)\. verify the dataset before choosing", value
        )
        if match:
            return _decision(
                correct=(int(match[1]), int(match[2]))
                == (expected["methods_count"], expected["results_count"])
            )
        if re.fullmatch(r"report \d+ as the final sample size", value):
            return "fail", "The reply picks a final count without resolving the discrepancy."
    if "diary_a" in expected:
        match = re.fullmatch(r"diary a: ([^.]+)\. diary b: ([^.]+)", value)
        if match:
            a, b = _normal(expected["diary_a"]), _normal(expected["diary_b"])
            if (match[1], match[2]) == (a, b):
                return _PASS
            if (match[1], match[2]) == (b, a):
                return "fail", "The reply swaps the two source attributions."
    if "supporting_memo" in expected:
        match = re.fullmatch(
            r"([a-z ]+ memo): (\d+) reviewers independently reviewed each round", value
        )
        if match:
            return _decision(
                correct=match[1] == _normal(expected["supporting_memo"])
                and int(match[2]) == expected["independent_reviewers"]
            )
    return None


def grade_answer(case: dict, reply: str) -> tuple[str, str]:
    """Grade the observed Answer.text with case expectations; defer uncertain prose to review."""
    expected = case["expected"]
    value = _normal(reply)
    if not value:
        return "fail", "There is no answer."
    if "interviewed_count" in expected:
        two_counts = re.fullmatch(r"of the (\d+) invited, (\d+) were interviewed", value)
        if two_counts:
            if int(two_counts[2]) != expected["interviewed_count"]:
                return "fail", "The number attributed to completed interviews is incorrect."
            draft = case["input"]["manuscript_text"].casefold()
            invited = re.findall(r"\bwe invited (\d+) students\b", draft)
            if len(invited) != 1:
                return _REVIEW
            return _decision(correct=int(two_counts[1]) == int(invited[0]))
    for rule in (_number_grade, _missing_fact, _named_fact, _structured):
        if decision := rule(value, expected):
            return decision
    if value == _normal(expected["reference_answer"]):
        return "pass", "Matches the reviewed reference answer."
    if "criteria" in expected and reply.count("?") > 1:
        return "fail", "The prompt asks for one survey question; the reply asks several."
    if "ordered_steps" in expected:
        numbers = re.findall(r"(?:^|\s)(\d+)[.)]\s", reply)
        if len(numbers) >= 2 and len(numbers) != len(expected["ordered_steps"]):
            return "fail", "The numbered list has the wrong number of steps."
    if expected.get("supported_claim") == "association" and re.fullmatch(
        r"(?:the|this) survey proves (?:that )?longer study caused higher scores", value
    ):
        return "fail", "The reply claims the observational survey proves causation."
    return _REVIEW
