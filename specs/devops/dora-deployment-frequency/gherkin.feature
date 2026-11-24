Feature: Track DORA deployment frequency
  Theseus maintainers can see how much time passes between deployments that reach production.

  @S-023 @criterion-1
  Scenario: Report elapsed time between consecutive production deployments
    Given deployments reached production at 09:00, 11:00, and 14:00 UTC on the same day
    When a maintainer reviews the deployment frequency report
    Then the report shows intervals of 2 hours and 3 hours

  @S-024 @edge @criterion-2
  Scenario: Exclude deployments that never reach production from intervals
    Given two deployments reached production 4 hours apart with no other production deployments between them
    And a staging-only deployment and an attempt that never reached production occurred between them
    When a maintainer reviews the deployment frequency report
    Then the report shows a single interval of 4 hours

  @S-021 @criterion-3
  Scenario: Include manually triggered deployments that reach production
    Given an automatically triggered deployment reached production
    And a manually triggered deployment reached production 6 hours later
    And the only intervening deployment attempt was manually triggered and never reached production
    When a maintainer reviews the deployment frequency report
    Then the report shows a single interval of 6 hours

  @S-022 @edge @criterion-4
  Scenario Outline: Report that an interval is unavailable with fewer than two production deployments
    Given exactly <deployments> deployments reached production
    When a maintainer reviews the deployment frequency report
    Then the report indicates that an interval is unavailable

    Examples:
      | deployments |
      | 0           |
      | 1           |
