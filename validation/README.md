# Revised THES-1 validation package
Supersedes the earlier THES-1-intake.md / THES-1.feature package. Use this folder alone to avoid duplicated context.

1. Review brief.md and approve the accepted scope. All unanswered questions are explicitly deferred, not decided by this package.
2. Put brief.md and features/ in your Theseus checkout (for example in a dedicated validation folder).
3. Paste KIRO-VALIDATE.txt into Kiro chat and reference this folder. Supply the actual checkout; no repository has been inspected here.

The supplied intake and Gherkin contexts guided this revision: 68-line brief, exact heading order, one feature per capability, business-level steps, one When per scenario, unique canonical IDs, criterion tags, edge tags, and happy paths first.

Identity preservation: @S-001 is the template-compliant alias of previous @S01, and so on. Retained scenarios carry both tags so original IDs are not lost. New scenarios start at @S-027. Previous @S03 (strength-policy example), @S13 (proposed update contract), @S15 (separate rate buckets), @S23 (project-owner deletion), @S24 (proposed password rules), @S25 (email normalization), @S26 (assumed lifetime) are reserved and withheld pending decisions; never reuse them. Existing IDs keep their original capability meaning; wording is revised to the new behavioral format. @S04 now covers registration length cases; its former sign-in rows use new @S-027. Password-storage coverage extracted from @S01 uses new @S-028. @S-029 adds the ordinary display-name happy path.

Deferred behavior is intentionally not turned into acceptance scenarios. Password hashing remains a checkable constraint in the brief; its Gherkin refers to that policy without naming a library. JSON/header, status and cookie concepts remain where they are observable contracts. No endpoint, source-file, class, table or library names occur in steps.

Q6: sign-out scenarios assert accepted user behavior only; a validator must report transport ambiguity instead of choosing a body/header exemption. Q1: valid registration fixtures require an approved password policy or an explicit fixture blocker. Q7: owned-project deletion is excluded, not silently implemented. Success/error envelopes do not resolve Q8 structured-detail placement.

Verification: authoring checks cover headings/line limit, tags and unique IDs, single When, Examples widths/placeholders, criterion coverage, edge ordering and scenario limits. A full Gherkin parser was unavailable; parser validation and repository evidence remain pending. These are acceptance descriptions, not executable tests until suitable step bindings exist. No claim is made that Jira policies are approved or application tests pass.

For lower context use, send only brief.md and features/*.feature plus the short validation prompt. README.md is usage guidance, not required model context. Exact credit savings depend on Kiro's model and usage.
