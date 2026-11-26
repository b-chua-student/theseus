Feature: Track failed deployment recovery time
  Maintainers can see how long it takes to restore normal production service after qualifying deployment failures.

  @S-050 @criterion-1
  Scenario: Report the time from production failure to restoration
    Given a deployment goes live at 09:55 UTC and causes production service to degrade at 10:00 UTC, requiring immediate intervention
    And a corrective deployment goes live at 10:45 UTC on the same day
    And production monitoring confirms that degradation began at 10:00 UTC and normal service was restored at 10:45 UTC
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 45 minutes for the failure

  @S-054 @criterion-1 @criterion-5
  Scenario: Report a recovery confirmed without a corrective deployment
    Given a maintainer records a qualifying deployment-caused production failure
    And the maintainer confirms that degradation began at 10:00 UTC, intervention began at 10:08 UTC, and normal service was restored at 10:30 UTC on the same day
    And service recovered without a corrective deployment
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 30 minutes for the failure

  @S-055 @criterion-1 @criterion-6
  Scenario: Count one recovery when two hotfixes address the same incident
    Given one qualifying deployment-caused production incident starts at 10:00 UTC
    And a hotfix goes live at 10:20 UTC while production service remains degraded
    And a second hotfix for the same incident goes live at 10:35 UTC on the same day
    And production monitoring confirms that degradation began at 10:00 UTC and normal service was restored at 10:35 UTC
    When a maintainer views the failed deployment recovery time report
    Then the report shows one entry for the incident with a recovery duration of 35 minutes
    And the report shows a median recovery duration of 35 minutes across 1 completed recovery

  @S-046 @criterion-3 @criterion-4
  Scenario: Summarize completed recoveries with known timestamps
    Given three qualifying production failures with verified recovery durations of 15, 45, and 120 minutes
    And two qualifying failures are unresolved
    And one qualifying failure has been restored with a missing timestamp
    When a maintainer views the failed deployment recovery time report
    Then the report shows a median recovery duration of 45 minutes across 3 completed recoveries
    And the report shows separate counts of 2 unresolved failures and 1 restored failure with a missing timestamp

  @S-051 @criterion-2 @edge
  Scenario Outline: Exclude failures that do not qualify
    Given one qualifying completed recovery with a verified duration of 45 minutes
    And a separate failure with a known failure time and a known restoration time
    And the failure occurred in <environment>
    And deployment attribution is <attribution>
    And immediate intervention is <intervention>
    When a maintainer views the failed deployment recovery time report
    Then the nonqualifying failure has no report entry
    And the report shows a median recovery duration of 45 minutes across 1 completed recovery
    And the report shows separate counts of 0 unresolved failures and 0 restored failures with a missing timestamp

    Examples:
      | environment | attribution | intervention |
      | staging     | confirmed   | required     |
      | production  | absent      | required     |
      | production  | confirmed   | not required |

  @S-048 @criterion-2 @edge
  Scenario: Exclude a failed deployment attempt that leaves production healthy
    Given one qualifying completed recovery with a verified duration of 45 minutes
    And a separate production deployment attempt fails during startup
    And the previous release continues to serve users normally
    When a maintainer views the failed deployment recovery time report
    Then the failed deployment attempt has no report entry
    And the report shows a median recovery duration of 45 minutes across 1 completed recovery
    And the report shows separate counts of 0 unresolved failures and 0 restored failures with a missing timestamp

  @S-049 @criterion-1 @edge
  Scenario: Use verified restoration after the corrective deployment goes live
    Given a deployment causes production degradation at 10:00 UTC that requires immediate intervention
    And a corrective deployment goes live at 10:20 UTC on the same day
    And a maintainer-confirmed incident timeline records degradation at 10:00 UTC and restoration at 10:30 UTC
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 30 minutes for the failure

  @S-052 @criterion-3 @criterion-5 @edge
  Scenario: Omit the completed recovery duration for an unresolved failure
    Given a maintainer records a deployment-caused production failure that requires immediate intervention
    And the failure time is known
    And no corrective deployment has shipped
    And normal service has yet to be restored
    When a maintainer views the failed deployment recovery time report
    Then the report shows the failure as "Unresolved" with a blank recovery duration

  @S-053 @criterion-3 @criterion-4 @edge
  Scenario Outline: Omit the completed recovery duration when one or both timestamps are unknown
    Given the only qualifying failure is a deployment-caused production failure that requires immediate intervention
    And normal service has been restored
    And the failure time is <failure time>
    And the restoration time is <restoration time>
    When a maintainer views the failed deployment recovery time report
    Then the report shows the failure as "Missing timestamp" with a blank recovery duration
    And the report shows 1 restored failure with a missing timestamp, 0 completed recoveries, and 0 unresolved failures

    Examples:
      | failure time | restoration time |
      | unknown      | known            |
      | known        | unknown          |
      | unknown      | unknown          |

  @S-047 @criterion-4 @edge
  Scenario: Show when there are no completed recoveries with known timestamps
    Given there is at least one qualifying failure
    And all qualifying failures are unresolved or missing a timestamp
    When a maintainer views the failed deployment recovery time report
    Then the report shows a completed recovery count of 0
    And the report shows "No completed recoveries with known timestamps."

  @S-056 @criterion-3 @criterion-4 @edge
  Scenario: Show an empty report when there are no qualifying failures
    Given there are zero qualifying failures
    When a maintainer views the failed deployment recovery time report
    Then the report shows no incident entries
    And the report shows 0 completed recoveries, 0 unresolved failures, and 0 restored failures with a missing timestamp
    And the report shows "No completed recoveries with known timestamps."
