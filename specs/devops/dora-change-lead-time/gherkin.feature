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
    And no production deployment starts as a result of the report run

  @S-008 @criterion-9
  Scenario: Keep credentials out of the report and logs
    Given credentials are used to retrieve the reporting data
    When a maintainer requests the report
    Then the credentials are absent from the report output and logs

  @S-011 @criterion-3
  Scenario: Include a feature pull request merged directly into main
    Given a feature pull request merges directly into main
    And a maintainer manually deploys the change to production
    And it first goes live 3 hours after the merge
    And the deployment falls within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 3 hours

  @edge @S-078 @criterion-2
  Scenario: Generate the report only when requested manually
    Given a maintainer has not requested a report
    When a change merges into main
    Then no lead-time report run starts

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
      | only a live deployment on another service |
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
    Given verified production history shows that a feature pull request first shipped before the reporting period
    And the same change was successfully redeployed to production during the reporting period
    And there are no other feature pull requests in the verified production history
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
    And maintainer-reviewed evidence identifies the original pull request carried by the promotion
    And the deployment falls within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 8 hours

  @edge @S-010 @criterion-3 @criterion-9
  Scenario: Fail the report when a squash promotion lacks maintainer-reviewed evidence
    Given a successful production deployment within the reporting period includes a squash promotion
    And the promotion obscures which original feature pull requests it carried
    And there is no maintainer-reviewed evidence identifying those pull requests
    When a maintainer requests the report on demand
    Then the report run fails with a sanitized diagnostic
    And the report withholds the median and included pull request count
    And credentials are absent from the report output and logs

  @edge @S-075 @criterion-7
  Scenario: Include the UTC start boundary and exclude the UTC end boundary
    Given an enhancement pull request first went live on the designated Render production service at 00:00 UTC on November 1, 2026, 4 hours after merging
    And another enhancement pull request first went live on that service at 00:00 UTC on December 1, 2026, 8 hours after merging
    When a maintainer starts the on-demand report at 00:00 UTC on December 1, 2026
    Then the report shows a UTC start of November 1, 2026 at 00:00 and a UTC end of December 1, 2026 at 00:00
    And the report counts 1 included feature pull request
    And the median lead time is 4 hours

  @edge @S-076 @criterion-1 @criterion-8
  Scenario: Identify historical feature pull requests by the enhancement label
    Given a historical pull request labeled enhancement merged 4 hours before its first successful deployment
    And a historical pull request without the enhancement label merged 8 hours before that same deployment
    And the deployment went live on the designated Render production service within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 4 hours

  @edge @S-077 @criterion-5 @criterion-8
  Scenario: Preserve the first live timestamp after a deployment is deactivated
    Given a feature pull request first went live on the designated Render production service 4 hours after it merged
    And that deployment was later deactivated
    And the same change went live on that service again 24 hours after the merge
    And both live timestamps fall within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included feature pull request
    And the median lead time is 4 hours
