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

  @S-025 @criterion-5
  Scenario: Run the report when a change merges into main
    Given a change is ready to merge into main
    When the change is merged into main
    Then a deployment frequency report run starts for that merge

  @S-026 @criterion-6
  Scenario: Include intervals across the complete production deployment history
    Given the first successful production deployment occurred on 2023-01-01 at 09:00 UTC
    And the next two successful production deployments occurred on 2026-01-01 at 09:00 and 12:00 UTC
    And there have been no other successful production deployments
    When a maintainer reviews the deployment frequency report
    Then the report shows two intervals, one of 1096 days and one of 3 hours

  @S-027 @criterion-7
  Scenario: Include successful rollbacks and redeployments
    Given a production deployment succeeded at 09:00 UTC
    And a rollback to a previously deployed revision succeeded at 10:00 UTC
    And a redeployment of that revision succeeded at 13:00 UTC
    And the only other attempts were a failed production rollback and a failed production redeployment
    When a maintainer reviews the deployment frequency report
    Then the report shows intervals of 1 hour and 3 hours
