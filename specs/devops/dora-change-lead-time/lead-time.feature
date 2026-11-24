Feature: Report feature PR merge-to-production lead time
  Theseus maintainers can see how long merged feature pull requests take to go live in production.

  @S-001 @criterion-1 @criterion-3
  Scenario: Trace several feature pull requests through one staging promotion
    Given three feature pull requests merge into staging 2, 6, and 10 hours before their first successful production deployment
    And one of those pull requests contains multiple commits
    And one staging promotion carries all three changes into main
    And that deployment falls within the rolling 30-day reporting period
    When a maintainer requests the report on demand in GitHub Actions
    Then the report is labeled "Feature PR merge-to-production lead time"
    And the report shows the UTC bounds of the rolling 30-day reporting period
    And the report counts 3 included feature pull requests
    And the median lead time is 6 hours

  @S-002 @criterion-2
  Scenario: Publish the verified report weekly
    Given a maintainer has verified the on-demand report
    When the weekly reporting time arrives
    Then the report is published

  @S-008 @criterion-9
  Scenario: Keep credentials out of the report and logs
    Given credentials are used to retrieve the reporting data
    When a maintainer requests the report
    Then the credentials are absent from the report output and logs

  @edge @S-003 @criterion-2
  Scenario: Withhold weekly publication before verification
    Given the report results are awaiting verification
    When the weekly reporting time arrives
    Then the report is not published

  @edge @S-004 @criterion-4 @criterion-8
  Scenario Outline: Exclude a merged feature pull request without a successful production deployment
    Given one qualifying feature pull request has a lead time of 6 hours
    And another merged feature pull request has <deployment history>
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 6 hours

    Examples:
      | deployment history                   |
      | no deployment                        |
      | only a successful preview deployment |
      | only a successful staging deployment |
      | only a failed production deployment  |

  @edge @S-005 @criterion-5
  Scenario: Preserve the first successful deployment across a redeploy
    Given a feature pull request first shipped successfully to production 4 hours after it merged
    And the same change was successfully redeployed to production 24 hours after the merge
    And both deployments fall within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 4 hours

  @edge @S-006 @criterion-5 @criterion-6
  Scenario: Exclude a redeploy in the window when the first successful deployment was earlier
    Given no feature pull request first shipped successfully to production within the reporting period
    And a feature pull request first shipped successfully to production before the reporting period
    And the same change was successfully redeployed to production during the reporting period
    When a maintainer requests the report
    Then the report counts 0 included feature pull requests
    And the median lead time is unavailable

  @edge @S-007 @criterion-7
  Scenario: Include a feature pull request merged before the reporting period
    Given a feature pull request merged 48 hours before the reporting period began
    And it first shipped successfully to production 24 hours after the reporting period began
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 72 hours

  @edge @S-009 @criterion-3
  Scenario: Preserve the feature pull request merge time across a squash promotion
    Given a feature pull request merges into staging 8 hours before it first ships successfully to production
    And a squash promotion carries its change into main 2 hours before that deployment
    And the deployment falls within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 8 hours

  @edge @S-010 @criterion-3
  Scenario: Fail the report when a deployed feature pull request cannot be traced
    Given a successful production deployment contains a squash promotion with insufficient evidence to identify its feature pull requests
    When a maintainer requests the report
    Then the report run fails with a sanitized diagnostic
    And no median or included pull request count is published

  @S-011 @criterion-3
  Scenario: Include a feature pull request merged directly into main
    Given a feature pull request merges directly into main
    And it first ships successfully to production 3 hours after the merge
    And the deployment falls within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 3 hours
