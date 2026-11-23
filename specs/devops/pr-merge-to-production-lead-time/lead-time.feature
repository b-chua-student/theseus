# Reports the count and median lead time for PRs that first shipped successfully
# to production in the rolling 30-day window. Each PR contributes one sample,
# measured from its merge into the production branch to that first deployment.
# The report runs on demand in GitHub Actions and publishes weekly after
# verification. Credentials stay out of the report and logs.
Feature: Report PR merge-to-production lead time
  Theseus maintainers can see how long merged pull requests take to reach production.

  @S-001 @criterion-1 @criterion-3
  Scenario: Report separate samples when a production deployment ships several pull requests
    Given three pull requests merged into the production branch 2, 6, and 10 hours before they first shipped to production
    And that deployment occurred within the rolling 30-day reporting period
    When a maintainer requests the report on demand in GitHub Actions
    Then the report is labeled "PR merge-to-production lead time"
    And the report shows the rolling 30-day reporting period
    And the report counts 3 included pull requests
    And the median lead time is 6 hours

  @S-002 @criterion-2
  Scenario: Publish the verified report weekly
    Given the report results have been verified
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
  Scenario Outline: Exclude a merged pull request without a successful production deployment
    Given one qualifying pull request has a lead time of 6 hours
    And another pull request merged into the production branch has <deployment history>
    When a maintainer requests the report
    Then the report counts 1 included pull request
    And the median lead time is 6 hours

    Examples:
      | deployment history                   |
      | no deployment                        |
      | only a successful preview deployment |
      | only a successful staging deployment |
      | only a failed production deployment  |

  @edge @S-005 @criterion-5
  Scenario: Preserve the first successful deployment across a redeploy
    Given a pull request first shipped successfully to production 4 hours after merging into the production branch
    And the same changes were successfully redeployed to production 24 hours after the merge
    And both deployments fall within the reporting period
    When a maintainer requests the report
    Then the report counts 1 included pull request
    And the median lead time is 4 hours

  @edge @S-006 @criterion-5 @criterion-6
  Scenario: Exclude a redeploy in the window when the first successful deployment was earlier
    Given no pull request first shipped successfully to production within the reporting period
    And a pull request first shipped successfully to production before the reporting period
    And its changes were successfully redeployed to production during the reporting period
    When a maintainer requests the report
    Then the report counts 0 included pull requests
    And the median lead time is unavailable

  @edge @S-007 @criterion-7
  Scenario: Include a pull request that merged before the reporting period
    Given a pull request merged into the production branch 48 hours before the reporting period began
    And it first shipped successfully to production 24 hours after the reporting period began
    When a maintainer requests the report
    Then the report counts 1 included pull request
    And the median lead time is 72 hours
