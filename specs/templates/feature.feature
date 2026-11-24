# Role
# Write Gherkin from the approved intake brief (brief.md). Use that brief as
# the only source of behavior. If it is ambiguous, ask before writing.
#
# Scope and coverage
# Save the scenarios as specs/<context>/<feature_name>/gherkin.feature.
# Stay within In Scope
# and exclude all Non-Goals. Use the brief's domain terms and roles.
# Cover every numbered Success Criterion and every Constraint that affects
# behavior. Do not infer rules, inspect the codebase, or write spec documents.
#
# Scenarios and tags
# Put happy paths first, followed by error and boundary cases tagged @edge.
# Use at most eight non-edge scenarios per feature.
# Give every Scenario and Scenario Outline a unique @S-### tag across all
# features in the context. Use the next available ID. When revising,
# preserve existing IDs and never renumber them or reuse retired IDs.
# Add @criterion-N for each numbered Success Criterion the scenario covers.
#
# Steps
# Use Given for state, a single When for the action, and Then for an
# observable outcome. Use And for additional state or outcomes as needed.
# Keep steps declarative and free of UI and implementation details.
# Use Background only for shared setup. Use Scenario Outline only when
# the behavior is the same for every row and only the data varies.
#
# Before finishing
# Replace all placeholders and remove these instructions. Check Gherkin
# syntax, tag uniqueness and coverage, behavioral constraints, and Non-Goals.

Feature: <User-facing capability>
  <One-line description of the capability>

  @S-001 @criterion-1
  Scenario: <Expected behavior>
    Given <Relevant state>
    When <One action>
    Then <Observable outcome>
