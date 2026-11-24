"""Validate spec files in the feature directories affected by a Git diff."""

import argparse
from graphlib import CycleError, TopologicalSorter
from pathlib import Path
import re
import subprocess
import sys


SPEC_FILES = {
    "requirements.md": ("Requirements", "R"),
    "design.md": ("Design", "D"),
    "tasks.md": ("Tasks", "T"),
}
SPEC_PATH = re.compile(r"specs/(?!templates/)[^/]+/[^/]+/(?:requirements|design|tasks)\.md")
HEADING = re.compile(r"(#{1,6}) +([^ \n].*| )")
TABLE_SEPARATOR = re.compile(r":?-{3,}:?")
NODE = re.compile(r'(?P<alias>[A-Za-z_][\w-]*)(?:\["(?P<label>T-[0-9]{3})(?:\s[^"]*)?"\])?')
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")


def markdown_parts(text):
    """Return headings, unfenced lines, and fenced Mermaid blocks by section."""
    headings = set()
    sections = {}
    graphs = {}
    section = ""
    fence = None
    graph = None
    for line in text.splitlines():
        marker = FENCE.match(line)
        if fence:
            if (marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence)
                    and not line[marker.end():].strip()):
                fence = graph = None
            elif graph is not None:
                graph.append(line)
            continue
        if marker:
            fence = marker[1]
            if line[marker.end():].strip() == "mermaid":
                graph = []
                graphs.setdefault(section, []).append(graph)
            continue
        heading = HEADING.fullmatch(line)
        if heading:
            level, title = heading.groups()
            # Trim optional closing hashes and spaces while keeping a nonempty title.
            title = title.rstrip(" ").rstrip("#").rstrip(" ") or title[0]
            headings.add((level, title))
            section = title if level == "##" else ""
        sections.setdefault(section, []).append(line)
    return headings, sections, graphs


def table_cells(line):
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def tables(lines):
    for index, (header, separator) in enumerate(zip(lines, lines[1:])):
        if "|" not in header or "|" not in separator:
            continue
        columns = table_cells(header)
        separators = table_cells(separator)
        if len(columns) != len(separators) or not all(
            TABLE_SEPARATOR.fullmatch(cell) for cell in separators
        ):
            continue
        rows = []
        for line in lines[index + 2:]:
            if "|" not in line or HEADING.fullmatch(line):
                break
            rows.append(table_cells(line))
        yield columns, rows


class FeatureCheck:
    def __init__(self, directory):
        self.directory = directory
        self.errors = []

    def report(self, file, rule, detail):
        self.errors.append(f"{file}: {rule}: {detail}")

    def read(self, path):
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            self.report(path, "read file", str(error))
            return None

    def structure(self, filename):
        path = self.directory / filename
        template = Path("specs/templates") / filename
        expected_text = self.read(template)
        actual_text = self.read(path)
        if expected_text is None or actual_text is None:
            return {}, {}, {}
        section, prefix = SPEC_FILES[filename]
        expected_headings, expected_sections, _ = markdown_parts(expected_text)
        headings, sections, graphs = markdown_parts(actual_text)
        for level, heading in sorted(expected_headings):
            if "[Feature name]" in heading:
                title_prefix = heading.split("[Feature name]", 1)[0]
                present = any(
                    actual_level == level and actual_heading.startswith(title_prefix)
                    and actual_heading[len(title_prefix):].strip()
                    for actual_level, actual_heading in headings
                )
            else:
                present = (level, heading) in headings
            if not present:
                self.report(path, "missing required heading", f"{level} {heading}")

        expected_tables = list(tables(expected_sections.get(section, [])))
        if len(expected_tables) != 1:
            self.report(template, "template table", f"expected one table in {section}")
            return {}, sections, graphs
        required_columns, _ = expected_tables[0]
        actual_tables = list(tables(sections.get(section, [])))
        if len(actual_tables) != 1:
            self.report(path, "required table", f"expected one table in {section}")
            return {}, sections, graphs
        columns, rows = actual_tables[0]
        for column in required_columns:
            if column not in columns:
                self.report(path, "missing required column", column)
        if len(set(columns)) != len(columns):
            self.report(path, "duplicate column", section)
        if set(required_columns) - set(columns) or len(set(columns)) != len(columns):
            return {}, sections, graphs

        entries = {}
        for cells in rows:
            if len(cells) != len(columns):
                self.report(path, "table row", f"expected {len(columns)} cells: {cells}")
                continue
            row = dict(zip(columns, cells))
            identifier = row["ID"]
            if not re.fullmatch(fr"{prefix}-[0-9]{{3}}", identifier):
                self.report(path, "malformed ID", repr(identifier))
            elif identifier in entries:
                self.report(path, "duplicate ID", identifier)
            else:
                entries[identifier] = row
        return entries, sections, graphs

    def references(self, path, owner, value, allowed, rule, optional=False):
        if optional and value == "-":
            return set()
        identifiers = {part.strip() for part in value.split(",")}
        for identifier in sorted(identifiers - allowed):
            self.report(path, rule, f"{owner} references unknown ID {identifier!r}")
        return identifiers & allowed

    def traceability(self, requirements, design, tasks, sections):
        req_path = self.directory / "requirements.md"
        design_path = self.directory / "design.md"
        task_path = self.directory / "tasks.md"

        entries = [
            line.strip() for lines in sections.values() for line in lines
            if re.match(r"\s*-\s+Ticket\s*:", line)
        ]
        ticket = re.fullmatch(r"- Ticket: `(tickets/[^\x60]+\.md)`", entries[0]) if len(entries) == 1 else None
        ticket_lines = None
        if not ticket or not Path(ticket[1]).resolve().is_relative_to(Path("tickets").resolve()):
            self.report(req_path, "ticket source", "expected one ticket entry under tickets/")
        else:
            ticket_text = self.read(Path(ticket[1]))
            if ticket_text is None:
                self.report(req_path, "ticket source", f"cannot read {ticket[1]}")
            else:
                ticket_lines = ticket_text.splitlines()

        gherkin = self.read(self.directory / "gherkin.feature")
        scenarios = scenario_tags(gherkin or "")
        for identifier, row in requirements.items():
            if row["Source"] != "from ticket":
                self.report(req_path, "ticket source", f"{identifier} must use 'from ticket'")
            if ticket_lines is not None:
                for citation in row["Ticket lines"].split(","):
                    citation = citation.strip()
                    digits = citation.lstrip("0")
                    if (not re.fullmatch(r"[0-9]+", citation) or len(digits) > len(str(len(ticket_lines)))
                            or not digits
                            or not 1 <= int(digits) <= len(ticket_lines)
                            or not ticket_lines[int(digits) - 1].strip()):
                        self.report(req_path, "ticket line", f"{identifier} cites invalid line {citation!r}")
            if gherkin is not None:
                self.references(req_path, identifier, row["Scenarios"], scenarios,
                                "scenario reference", optional=True)

        covered_requirements = set()
        for identifier, row in design.items():
            covered_requirements.update(self.references(
                design_path, identifier, row["Requirements"], requirements.keys(), "requirement reference"
            ))
        for identifier in sorted(requirements.keys() - covered_requirements):
            self.report(design_path, "requirement coverage", f"{identifier} has no design decision")

        covered_design = set()
        covered_scenarios = set()
        for identifier, row in tasks.items():
            covered_design.update(self.references(
                task_path, identifier, row["References"], requirements.keys() | design.keys(), "task reference"
            ) & design.keys())
            scenario_refs = self.references(
                task_path, identifier, row["Scenarios"], scenarios, "scenario reference", optional=True
            ) if gherkin is not None else set()
            if row["Verification"] not in ("", "-"):
                covered_scenarios.update(scenario_refs)
        for identifier in sorted(design.keys() - covered_design):
            self.report(task_path, "design coverage", f"{identifier} has no task")
        for identifier in sorted(scenarios - covered_scenarios):
            self.report(task_path, "scenario coverage", f"{identifier} has no verification task")

    def dependencies(self, tasks, graphs):
        path = self.directory / "tasks.md"
        prerequisites = {
            identifier: self.references(path, identifier, row["Depends on"], tasks.keys(),
                                        "dependency reference", optional=True)
            for identifier, row in tasks.items()
        }
        expected_edges = {(parent, task) for task, parents in prerequisites.items() for parent in parents}
        if len(graphs) != 1:
            self.report(path, "dependency graph", "expected one Mermaid block in Dependency graph")
        else:
            try:
                nodes, edges = graph_sets(graphs[0])
            except ValueError as error:
                self.report(path, "dependency graph", str(error))
            else:
                for rule, expected, actual in (
                    ("graph nodes", set(tasks), nodes),
                    ("graph edges", expected_edges, edges),
                ):
                    if expected != actual:
                        self.report(path, rule, f"missing {sorted(expected - actual)}, unexpected {sorted(actual - expected)}")

        try:
            order = list(TopologicalSorter(prerequisites).static_order())
        except CycleError as error:
            self.report(path, "dependency cycle", " -> ".join(error.args[1]))
            return
        waves = {}
        for task in order:
            wave = 1 + max((waves[parent] for parent in prerequisites[task]), default=0)
            waves[task] = wave
            if tasks[task]["Wave"] != str(wave):
                self.report(path, "task wave", f"{task} expected wave {wave}, found {tasks[task]['Wave']!r}")

    def validate(self):
        requirements, sections, _ = self.structure("requirements.md")
        design, _, _ = self.structure("design.md")
        tasks, _, graphs = self.structure("tasks.md")
        if not self.errors:
            self.traceability(requirements, design, tasks, sections)
            self.dependencies(tasks, graphs.get("Dependency graph", []))
        return self.errors


def scenario_tags(text):
    scenarios = set()
    pending = set()
    doc_string = None
    for line in text.splitlines():
        line = line.strip()
        if doc_string:
            if line == doc_string:
                doc_string = None
        elif line.startswith(('"""', "```")):
            doc_string = line[:3]
        elif line.startswith("@"):
            pending.update(tag[1:] for tag in line.split() if re.fullmatch(r"@S-[0-9]{3}", tag))
        elif line and not line.startswith("#"):
            if re.match(r"(?:Scenario(?: Outline| Template)?|Example):", line):
                scenarios.update(pending)
            pending.clear()
    return scenarios


def graph_sets(lines):
    statements = [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("%%")]
    if not statements or not re.fullmatch(r"(?:flowchart|graph) +(?:TD|TB|BT|RL|LR)", statements[0]):
        raise ValueError("expected a Mermaid flowchart declaration")
    aliases = {}
    nodes = set()
    edges = set()
    for statement in statements[1:]:
        chain = []
        for token in re.split(r'-->(?=(?:[^"]*"[^"]*")*[^"]*$)', statement):
            match = NODE.fullmatch(token.strip())
            if not match:
                raise ValueError(f"invalid task node or edge: {statement}")
            alias, label = match.groups()
            if label and aliases.setdefault(alias, label) != label:
                raise ValueError(f"conflicting task IDs for {alias}")
            nodes.add(alias)
            chain.append(alias)
        edges.update(zip(chain, chain[1:]))

    resolved = {alias: aliases.get(alias, re.sub(r"^T([0-9]{3})$", r"T-\1", alias)) for alias in nodes}
    if len(set(resolved.values())) != len(resolved):
        raise ValueError("multiple Mermaid nodes refer to the same task")
    return set(resolved.values()), {(resolved[start], resolved[end]) for start, end in edges}


def revision_argument(value):
    if value.startswith("-"):
        raise argparse.ArgumentTypeError("revision must not start with '-'")
    return value


def resolve_revision(parser, argument, value):
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", "--end-of-options", f"{value}^{{object}}"],
        check=False, stdout=subprocess.PIPE,
    )
    # Only full Git object IDs can reach the diff command.
    object_id = re.fullmatch(rb"([0-9a-f]{40}|[0-9a-f]{64})\n", result.stdout)
    if result.returncode == 0 and object_id is not None:
        return object_id[1].decode("ascii")
    parser.error(f"argument {argument}: expected a Git revision that resolves to one object")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=revision_argument, help="base Git revision")
    parser.add_argument(
        "head", nargs="?", type=revision_argument, help="head Git revision (defaults to the working tree)"
    )
    args = parser.parse_args()
    revision = resolve_revision(parser, "base", args.base)
    if args.head:
        head = resolve_revision(parser, "head", args.head)
        revision = f"{revision}...{head}"
    diff = subprocess.run(
        ["git", "diff", "--name-only", "-z", "--no-renames", "--diff-filter=AM", revision, "--"],
        check=False, stdout=subprocess.PIPE,
    )
    if diff.returncode:
        return 1
    paths = diff.stdout.decode("utf-8", errors="surrogateescape").split("\0")
    directories = sorted({Path(path).parent for path in paths if SPEC_PATH.fullmatch(path)})
    if not directories:
        print("No affected feature directories")
        return 0

    errors = [error for directory in directories for error in FeatureCheck(directory).validate()]
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print(f"Checked {len(directories)} feature director{'y' if len(directories) == 1 else 'ies'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
