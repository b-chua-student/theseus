"""Pull request and revision argument scenarios S-012 through S-020."""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FEATURE = Path("specs/devops/spec-file-check-workflow")
TICKET = Path("tickets/spec-file-checking.md")


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True)


def commit(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@example.com", "commit", "-qm", message)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / FEATURE, tmp_path / FEATURE)
    shutil.copytree(ROOT / "specs/templates", tmp_path / "specs/templates")
    (tmp_path / TICKET.parent).mkdir()
    shutil.copyfile(ROOT / TICKET, tmp_path / TICKET)
    git(tmp_path, "init", "-q")
    commit(tmp_path, "Base")
    return tmp_path


def replace(file: Path, old: str, new: str) -> None:
    original = file.read_text()
    assert old in original
    file.write_text(original.replace(old, new))


def check(repo: Path, *revisions: str) -> subprocess.CompletedProcess[str]:
    git(repo, "add", "-A")
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/spec_check.py"), *(revisions or ("HEAD",))],
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_passes(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode == 0, result.stderr
    assert "Checked 1 feature directory" in result.stdout


@pytest.mark.parametrize("include_head", [False, True], ids=["base", "base-and-head"])
def test_s019_valid_revisions_select_changes(repo: Path, *, include_head: bool) -> None:
    replace(repo / FEATURE / "design.md", "Spec check workflow", "PR spec workflow")
    if include_head:
        commit(repo, "Pull request")
        result = check(repo, "HEAD^", "HEAD")
    else:
        result = check(repo, "HEAD")
    assert_passes(result)


@pytest.mark.parametrize(
    "argument,revisions",
    [("base", ("-invalid-revision", "HEAD")), ("head", ("HEAD", "-invalid-revision"))],
    ids=["base", "head"],
)
def test_s020_option_like_revision_is_rejected(
    repo: Path, argument: str, revisions: tuple[str, ...]
) -> None:
    result = check(repo, "--", *revisions)
    assert result.returncode == 2, result.stderr
    assert f"argument {argument}: revision must not start with '-'" in result.stderr


def assert_invalid(repo: Path, path: Path, old: str, new: str, rule: str) -> None:
    replace(repo / path, old, new)
    result = check(repo)
    assert result.returncode == 1, result.stderr
    assert f"{path}: {rule}" in result.stderr


def test_s012_conforming_specs_and_existing_checks(repo: Path) -> None:
    replace(repo / FEATURE / "design.md", "Spec check workflow", "PR spec workflow")
    commit(repo, "Pull request")
    assert_passes(check(repo, "HEAD^", "HEAD"))
    workflow = (ROOT / ".github/workflows/check-intake-gherkin.yaml").read_text()
    for entry in ("pull_request:", "  intake:", "  gherkin:"):
        assert entry in workflow


def test_s013_unrelated_legacy_errors(repo: Path) -> None:
    legacy = repo / "specs/devops/legacy/requirements.md"
    legacy.parent.mkdir()
    legacy.write_text("Invalid")
    commit(repo, "Legacy")
    replace(repo / FEATURE / "design.md", "Spec check workflow", "PR spec workflow")
    assert_passes(check(repo))


@pytest.mark.parametrize(
    "path",
    [Path("specs/templates/design.md"), TICKET, FEATURE / "gherkin.feature"],
    ids=["template", "ticket", "gherkin"],
)
def test_s014_unrelated_changes(repo: Path, path: Path) -> None:
    file = repo / path
    file.write_text(file.read_text() + "\n")
    result = check(repo)
    assert result.returncode == 0, result.stderr
    assert "No affected feature directories" in result.stdout


def test_added_specs_deduplicate_and_deleted_specs_leave_check_idle(repo: Path) -> None:
    new_feature = FEATURE.with_name("new-feature")
    shutil.copytree(repo / FEATURE, repo / new_feature)
    assert_passes(check(repo))

    shutil.rmtree(repo / new_feature)
    (repo / FEATURE / "requirements.md").unlink()
    result = check(repo)
    assert result.returncode == 0, result.stderr
    assert "No affected feature directories" in result.stdout


@pytest.mark.parametrize(
    "filename,prefix", [("requirements.md", "R"), ("design.md", "D"), ("tasks.md", "T")]
)
@pytest.mark.parametrize(
    "old,new,rule",
    [
        ("| ID |", "| Key |", "missing required column"),
        ("| {prefix}-001 |", "| {prefix}-01 |", "malformed ID"),
        ("| {prefix}-002 |", "| {prefix}-001 |", "duplicate ID"),
    ],
    ids=["column", "malformed-id", "duplicate-id"],
)
def test_s015_structure(
    repo: Path, filename: str, prefix: str, old: str, new: str, rule: str
) -> None:
    assert_invalid(
        repo, FEATURE / filename, old.format(prefix=prefix), new.format(prefix=prefix), rule
    )


def test_s015_required_heading(repo: Path) -> None:
    assert_invalid(
        repo,
        FEATURE / "requirements.md",
        "## Open Questions",
        "## Questions",
        "missing required heading",
    )


@pytest.mark.parametrize(
    "old,new,rule",
    [
        ("- Ticket: `tickets/spec-file-checking.md`", "", "ticket source"),
        ("| 13, 40 |", "| 999 |", "ticket line"),
        ("| 13, 40 |", "| 2 |", "ticket line"),
        ("| S-012, S-014 |", "| S-999 |", "scenario reference"),
    ],
    ids=["ticket-source", "out-of-range-line", "blank-line", "scenario-reference"],
)
def test_s016_requirement_references(repo: Path, old: str, new: str, rule: str) -> None:
    assert_invalid(repo, FEATURE / "requirements.md", old, new, rule)


@pytest.mark.parametrize(
    "filename,old,new,rule",
    [
        ("design.md", "| R-001, R-002, R-008 |", "| R-999 |", "requirement reference"),
        ("design.md", ", R-008 |", " |", "requirement coverage"),
        ("tasks.md", "| D-002 |", "| D-999 |", "task reference"),
        ("tasks.md", "| D-002 |", "| R-003 |", "design coverage"),
        ("tasks.md", ", S-018", "", "scenario coverage"),
    ],
    ids=[
        "requirement-reference",
        "requirement-coverage",
        "task-reference",
        "design-coverage",
        "scenario-coverage",
    ],
)
def test_s017_traceability(repo: Path, filename: str, old: str, new: str, rule: str) -> None:
    assert_invalid(repo, FEATURE / filename, old, new, rule)


@pytest.mark.parametrize(
    "old,new,rule",
    [
        ("T001 --> T002", "T002 --> T001", "graph edges"),
        ('    T008["T-008 Standalone task"]\n', "", "graph nodes"),
        ("| D-002 | T-001 |", "| D-002 | T-002 |", "dependency cycle"),
        ("S-018 | 1 |", "S-018 | 2 |", "task wave"),
        ("| - | 4 |", "| - | 3 |", "task wave"),
    ],
    ids=["edges", "nodes", "cycle", "independent-wave", "dependent-wave"],
)
def test_s018_task_dependencies(repo: Path, old: str, new: str, rule: str) -> None:
    # A standalone task must be declared explicitly because it has no incident edges.
    path = FEATURE / "tasks.md"
    with (repo / path).open("a") as file:
        file.write("| T-008 | Standalone task | R-001 | - | Check task | - | 1 |\n")
    replace(
        repo / path, "    T001 --> T002", '    T008["T-008 Standalone task"]\n    T001 --> T002'
    )
    assert_passes(check(repo))
    assert_invalid(repo, path, old, new, rule)
