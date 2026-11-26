Feature: Track failed deployment recovery time
  Maintainers can see how long it takes to restore normal production service after qualifying deployment failures.

  @S-050 @criterion-1
  Scenario: Report the time from production failure to restoration
    Given a deployment goes live at 09:55 UTC
    And it causes production degradation at 10:00 UTC that requires immediate intervention
    And a corrective deployment goes live at 10:45 UTC on the same day
    And production monitoring confirms that degradation began at 10:00 UTC and normal service was restored at 10:45 UTC
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 45 minutes for the failure

  @S-054 @criterion-1 @criterion-5
  Scenario: Report a recovery confirmed without a corrective deployment
    Given a maintainer records a qualifying deployment-caused production failure
    And the maintainer confirms degradation at 10:00 UTC and intervention at 10:08 UTC
    And the maintainer confirms normal service was restored at 10:30 UTC on the same day
    And service recovered without a corrective deployment
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 30 minutes for the failure

  @S-055 @criterion-1 @criterion-6 @criterion-10
  Scenario: Count one recovery when two hotfixes address the same incident
    Given a maintainer has recorded one qualifying deployment-caused production incident that started at 10:00 UTC
    And a hotfix goes live at 10:20 UTC while production service remains degraded
    And a second hotfix goes live at 10:35 UTC on the same day
    And production monitoring confirms that degradation began at 10:00 UTC and normal service was restored at 10:35 UTC
    When a maintainer links both hotfixes to the existing incident record and views the recovery report
    Then the existing incident record shows both corrective deployments
    And the report shows one entry for the incident with a recovery duration of 35 minutes
    And the report shows a median recovery duration of 35 minutes across 1 completed recovery

  @S-063 @criterion-6 @criterion-10
  Scenario: Link a separately recorded correction to the original incident
    Given a maintainer confirmed a qualifying production incident before any corrective deployment
    And the original incident record has a confirmed timeline from degradation at 10:00 UTC to restoration at 10:35 UTC on the same day
    And a corrective deployment was recorded separately before it was linked to the incident
    When a maintainer links the corrective deployment to the original incident record and refreshes the recovery report
    Then the original record still shows the incident confirmation and timeline
    And the original record shows the linked corrective deployment
    And the separately recorded deployment evidence remains available
    And the original record is the only recovery record for the incident
    And the report shows one entry for the original record with a recovery duration of 35 minutes
    And the report shows a median recovery duration of 35 minutes across 1 completed recovery

  @S-046 @criterion-3 @criterion-4
  Scenario: Summarize completed recoveries with known timestamps
    Given three qualifying production failures with verified recovery durations of 15, 45, and 120 minutes
    And two qualifying failures are unresolved
    And one qualifying failure has been restored with a missing timestamp
    When a maintainer views the failed deployment recovery time report
    Then the report shows a median recovery duration of 45 minutes across 3 completed recoveries
    And the report shows separate counts of 2 unresolved failures and 1 restored failure with a missing timestamp

  @S-057 @criterion-4
  Scenario: Report the median for an even number of completed recoveries
    Given two qualifying production failures with verified recovery durations of 15 and 45 minutes
    When a maintainer views the failed deployment recovery time report
    Then the report shows a median recovery duration of 30 minutes across 2 completed recoveries

  @S-058 @criterion-3 @criterion-5 @criterion-10
  Scenario: Record a qualifying failure before a corrective deployment
    Given a deployment causes production degradation that requires immediate intervention
    And no corrective deployment has gone live
    And normal service has yet to be restored
    When a maintainer records and confirms the qualifying failure
    Then the failed deployment recovery time report shows the failure as "Unresolved" with a blank recovery duration

  @S-051 @criterion-2 @edge
  Scenario Outline: Exclude failures that do not qualify
    Given one qualifying completed recovery with a verified duration of 45 minutes
    And a separate failure in <environment> has known failure and restoration times
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

  @S-059 @criterion-7
  Scenario: Refresh the recovery report on demand
    Given a qualifying completed recovery was recorded more than 30 days ago
    And a qualifying unresolved incident was recorded after the previous report run
    When a maintainer refreshes the dedicated recovery report at 12:00 UTC
    Then the report shows both incident entries
    And the report shows a run time of 12:00 UTC

  @S-060 @criterion-8 @edge
  Scenario Outline: Report a restored incident with unusable timeline evidence
    Given the only qualifying incident has been restored
    And its timeline has <problem>
    When a maintainer views the failed deployment recovery time report
    Then the incident is shown as "Missing timestamp" with a blank duration
    And the report shows 1 restored failure with a missing timestamp
    And the report shows 0 completed recoveries
    And the report identifies the incident and the timeline problem

    Examples:
      | problem                            |
      | conflicting degradation timestamps |
      | conflicting restoration timestamps |
      | restoration earlier than failure   |

  @S-061 @criterion-8
  Scenario: Use the latest confirmation that resolves conflicting evidence
    Given a qualifying incident began at 10:00 UTC
    And its evidence disagrees on the time normal service returned that day
    And an earlier maintainer confirmation recorded restoration at 10:30 UTC
    And a later valid maintainer confirmation explicitly resolves the conflict at 10:45 UTC
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 45 minutes for the incident
    And the report shows a median recovery duration of 45 minutes across 1 completed recovery

  @S-062 @criterion-9 @edge
  Scenario: Report incomplete evidence when incident records cannot be loaded
    Given incident records cannot be loaded
    When a maintainer refreshes the failed deployment recovery time report
    Then the report shows that incident evidence is incomplete
    And the report does not show the zero-incident result
