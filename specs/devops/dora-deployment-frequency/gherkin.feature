Feature: Track DORA deployment frequency
  Theseus maintainers can see how often deployments reach production during a reporting period.

  @S-012 @criterion-1
  Scenario: Report production deployments for the period
    Given two distinct deployments reached production during the reporting period
    And one other deployment reached production outside the reporting period
    When a maintainer reviews the deployment frequency report for that period
    Then the report identifies that period
    And the report shows two production deployments

  @S-013 @edge @criterion-2
  Scenario: Report zero when no deployments reach production during the period
    Given one deployment reached staging only during the reporting period
    And one deployment attempted during the reporting period never reached production
    And no deployments reached production during the reporting period
    When a maintainer reviews the deployment frequency report for that period
    Then the report identifies that period
    And the report shows zero production deployments

  @S-021 @criterion-3
  Scenario: Count manually triggered deployments that reach production
    Given a manually triggered deployment reached production during the reporting period
    And another manually triggered deployment attempt during that period never reached production
    And no other deployments reached production during that period
    When a maintainer reviews the deployment frequency report for that period
    Then the report identifies that period
    And the report shows one production deployment
