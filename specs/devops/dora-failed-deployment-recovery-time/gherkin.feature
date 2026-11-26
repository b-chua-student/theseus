Feature: Track failed deployment recovery time
  Maintainers can see how long it takes to restore normal production service after qualifying deployment failures.

  @S-028 @criterion-1
  Scenario: Report the time from production failure to restoration
    Given a deployment causes a production failure at 10:00 UTC that requires immediate intervention
    And normal service is restored at 10:45 UTC on the same day
    When a maintainer views the failed deployment recovery time report
    Then the report shows a recovery duration of 45 minutes for the failure

  @S-029 @criterion-2 @edge
  Scenario Outline: Exclude failures that do not qualify
    Given a failure with a known failure time and a known restoration time
    And the failure occurred in <environment>
    And deployment attribution is <attribution>
    And immediate intervention is <intervention>
    When a maintainer views the failed deployment recovery time report
    Then the failure is excluded from the metric

    Examples:
      | environment | attribution | intervention |
      | staging     | confirmed   | required     |
      | production  | absent      | required     |
      | production  | confirmed   | not required |

  @S-030 @criterion-3 @edge
  Scenario: Omit the completed recovery duration for an unresolved failure
    Given a deployment causes a production failure that requires immediate intervention
    And the failure time is known
    And normal service has yet to be restored
    When a maintainer views the failed deployment recovery time report
    Then the report shows no completed recovery duration for the failure

  @S-031 @criterion-3 @edge
  Scenario Outline: Omit the completed recovery duration when one time is unknown
    Given a deployment causes a production failure that requires immediate intervention
    And normal service has been restored
    And the failure time is <failure time>
    And the restoration time is <restoration time>
    When a maintainer views the failed deployment recovery time report
    Then the report shows no completed recovery duration for the failure

    Examples:
      | failure time | restoration time |
      | unknown      | known            |
      | known        | unknown          |
