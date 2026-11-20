"""Run the Theseus offline evaluation cases using the backend development environment."""

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from grade_answers import controls, grade_answer

EVAL_DIR = Path(__file__).resolve().parent
CASE_STATUSES = ("passed", "failed", "needs_review", "not_run", "error")


def load_cases(path: Path) -> tuple[dict[str, dict], str]:
    """Load the reviewed dataset and reject ambiguous case IDs."""
    payload = path.read_bytes()
    dataset = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(dataset, list) or not dataset:
        raise ValueError("The dataset must be a nonempty JSON array.")
    cases = {}
    for case in dataset:
        case_id = case.get("id") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("A case is missing its string id.")
        if case_id in cases:
            raise ValueError(f"Duplicate case ID: {case_id}")
        cases[case_id] = case
    return cases, hashlib.sha256(payload).hexdigest()


def load_answers(path: Path, cases: dict[str, dict]) -> dict[str, str]:
    """Read offline answer text keyed by case ID."""
    answers = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(answers, dict) or not all(isinstance(v, str) for v in answers.values()):
        raise ValueError("Answers must be a JSON object mapping case IDs to reply strings.")
    unknown = answers.keys() - cases.keys()
    if unknown:
        raise ValueError(f"Unknown answer IDs: {sorted(unknown)}")
    return answers


def check_controls(case: dict, probe: Callable[[dict, str], dict]) -> dict:
    """Run independent synthetic replies through fresh service instances for one case."""
    observations = []
    issues = []
    errors = []
    samples = controls(case)
    if not samples:
        return {"status": "not_run", "reason": "No mock controls defined for this case."}

    for reply, wanted in samples:
        try:
            observation = probe(case, reply)
            actual, reason = grade_answer(case, observation["answer"])
            observation.update(
                expected_grade=wanted,
                actual_grade=actual,
                grade_reason=reason,
                control_reply=reply,
            )
            for check in ("routing", "retrieval"):
                if not observation[check]["passed"]:
                    issues.append(f"{check}: {observation[check]['reason']}")
            if observation["answer"] != reply.strip():
                issues.append("Returned answer differs from the supplied fake reply.")
            if actual != wanted:
                issues.append(f"Expected grade {wanted}, observed {actual}: {reason}")
            observations.append(observation)
        except Exception as exc:
            # A broken fixture must remain visible without hiding the other cases.
            message = f"{type(exc).__name__}: {exc}"
            errors.append(message)
            observations.append(
                {"control_reply": reply, "expected_grade": wanted, "error": message}
            )

    return {
        "status": "error" if errors else ("failed" if issues else "passed"),
        "reason": " ".join(dict.fromkeys(errors + issues)) or "All controls matched.",
        "observations": observations,
    }


def check_saved_answer(case: dict, answers: dict[str, str]) -> dict:
    """Grade supplied text only; no retrieval trace is available in this mode."""
    if case["id"] not in answers:
        return {"status": "not_run", "reason": "No answer supplied."}
    reply = answers[case["id"]]
    grade, reason = grade_answer(case, reply)
    return {
        "status": {"pass": "passed", "fail": "failed", "needs_review": "needs_review"}[grade],
        "reason": reason,
        "answer": reply,
        "pass_rule": case["pass_rule"],
    }


def main() -> int:
    """Run the selected cases, print counts, and save the observed results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", action="append", dest="ids", help="Run one ID (repeatable).")
    parser.add_argument("--answers", type=Path, help='Grade saved replies, e.g. {"M01": "12"}.')
    parser.add_argument("--results-dir", type=Path, default=EVAL_DIR / "results")
    args = parser.parse_args()
    try:
        cases, digest = load_cases(EVAL_DIR / "cases.json")
        selected = list(dict.fromkeys(args.ids or cases))
        unknown = set(selected) - cases.keys()
        if unknown:
            raise ValueError(f"Unknown case IDs: {sorted(unknown)}")
        if args.answers is not None:
            answers = load_answers(args.answers, cases)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    mode = "saved_answer_grades" if args.answers is not None else "mock_controls"
    if mode == "mock_controls":
        # Pytest config normally adds backend to the import path; this CLI runs directly.
        sys.path.insert(0, str(EVAL_DIR.parent / "backend"))
        from assistant_probe import probe

    rows = []
    sys.stdout.write(f"Mode: {mode}\n")
    if mode == "mock_controls":
        sys.stdout.write("case   control check   routing  retrieval  observed answer grades\n")
    for case_id in selected:
        case = cases[case_id]
        try:
            if args.answers is None:
                result = check_controls(case, probe)
            else:
                result = check_saved_answer(case, answers)
        except Exception as exc:
            result = {"status": "error", "reason": f"{type(exc).__name__}: {exc}"}
        rows.append({"id": case_id, **result})
        line = f"{case_id:<6} {result['status']:<13}"
        if observations := result.get("observations"):
            for check in ("routing", "retrieval"):
                passed = sum(item.get(check, {}).get("passed", False) for item in observations)
                line += f" {passed}/{len(observations):<8}"
            line += ", ".join(item.get("actual_grade", "error") for item in observations)
        if result["status"] != "passed" or mode == "saved_answer_grades":
            line += f"  {result['reason']}"
        sys.stdout.write(line + "\n")

    counts = Counter(row["status"] for row in rows)
    executed = len(rows) - counts["not_run"]
    rate = counts["passed"] / executed if executed else None
    summary = {status: counts[status] for status in CASE_STATUSES}
    summary.update(total=len(rows), executed=executed, pass_rate=rate)
    now = datetime.now(UTC)
    report = {
        "created_at_utc": now.isoformat(),
        "mode": mode,
        "dataset_sha256": digest,
        "summary": summary,
        "cases": rows,
    }
    args.results_dir.mkdir(parents=True, exist_ok=True)
    path = args.results_dir / f"{mode}-{now:%Y%m%dT%H%M%S}-{uuid4().hex[:8]}.json"
    with path.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2, ensure_ascii=False)
        output.write("\n")
    sys.stdout.write("\n" + "  ".join(f"{k}: {summary[k]}" for k in ("total", *CASE_STATUSES)))
    rate_label = f"{rate:.1%}" if rate is not None else "n/a"
    sys.stdout.write(f"  pass rate over executed: {rate_label}\nReport: {path.resolve()}\n")
    if counts["failed"] or counts["error"]:
        return 1
    return 2 if counts["needs_review"] or counts["not_run"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
