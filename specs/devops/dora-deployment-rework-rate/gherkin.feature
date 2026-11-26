Feature: Track deployment rework rate
  Maintainers can see what share of production deployments were unplanned responses to production incidents.

  @S-046 @criterion-1
  Scenario: Report the share of deployments that addressed production incidents
    Given complete evidence for four deployments that went live in production during the reporting period
    And a maintainer confirmed that two were unplanned responses to the same production incident
    And the incident was caused by an infrastructure outage
    And a maintainer recorded the other two deployments as reviewed with no qualifying rework
    And a separate confirmed incident response never went live in production
    When a maintainer runs the report on demand
    Then the report shows 2 rework deployments and 4 production deployments
    And the rework rate is 50%

  @S-054 @criterion-7
  Scenario: Guide maintainers in confirming deployment rework
    Given a maintainer is documenting a production incident
    When the maintainer uses the production incident template
    Then the template includes a "Deployment rework" section
    And the section explains how to record that a specific deployment went live in production as an unplanned response to the incident

  @S-047 @edge @criterion-1 @criterion-2
  Scenario: Count a deployment linked to multiple incidents once
    Given complete evidence for two deployments that went live in production during the reporting period
    And a maintainer confirmed the same deployment as an unplanned response on two incident records
    And a maintainer recorded the other deployment as reviewed with no qualifying rework
    When a maintainer runs the report on demand
    Then the report shows 1 rework deployment and 2 production deployments
    And the rework rate is 50%

  @S-048 @edge @criterion-3
  Scenario: Use production live time to include the window start and exclude the report start
    Given complete evidence for the following production deployments
      | Production live time UTC | Rework status                       |
      | 2026-10-27T11:59:59Z      | Confirmed unplanned response        |
      | 2026-10-27T12:00:00Z      | Confirmed unplanned response        |
      | 2026-11-26T11:59:59Z      | Reviewed with no qualifying rework   |
      | 2026-11-26T12:00:00Z      | Confirmed unplanned response        |
      | 2026-11-26T12:00:01Z      | Confirmed unplanned response        |
    And the incident addressed by the deployment at the window start began before the window
    When a maintainer runs the report on demand at 2026-11-26T12:00:00Z
    Then the report shows 1 rework deployment and 2 production deployments

  @S-049 @edge @criterion-4
  Scenario: Report a verified period with no production deployments
    Given verified production history shows no deployments went live during the reporting period
    When a maintainer runs the report on demand
    Then the report shows 0 rework deployments and 0 production deployments
    And the rate is displayed as "N/A — no production deployments"

  @S-050 @edge @criterion-4 @criterion-6
  Scenario: Report zero rework when deployments were planned
    Given verified production history shows two deployments went live during the reporting period
    And a maintainer recorded a reviewed disposition of no qualifying rework for each deployment
    And the remaining evidence is complete
    When a maintainer runs the report on demand
    Then the report shows 0 rework deployments and 2 production deployments
    And the rework rate is 0%

  @S-051 @edge @criterion-5
  Scenario: Withhold the rate while a potential rework deployment awaits confirmation
    Given verified production history shows three deployments went live during the reporting period
    And one deployment was a maintainer-confirmed unplanned response to a production incident
    And a maintainer recorded one deployment as reviewed with no qualifying rework
    And one deployment was flagged as a hotfix and awaits maintainer confirmation
    When a maintainer runs the report on demand
    Then the report shows "Incomplete evidence" and omits the percentage
    And it shows 3 verified production deployments, 1 confirmed rework deployment, and 1 awaiting review

  @S-052 @edge @criterion-5
  Scenario: Withhold the rate when production history is incomplete
    Given a gap in production history could change the deployment total for the reporting period
    When a maintainer runs the report on demand
    Then the report shows "Incomplete evidence" and omits the percentage
    And it marks the production deployment total as unverified

  @S-053 @edge @criterion-5 @criterion-6
  Scenario: Treat a deployment without an incident or disposition as awaiting review
    Given verified production history shows two deployments went live during the reporting period
    And one deployment was a maintainer-confirmed unplanned response to a production incident
    And the other deployment has no linked incident and no maintainer disposition
    When a maintainer runs the report on demand
    Then the report shows "Incomplete evidence" and omits the percentage
    And it shows 2 verified production deployments, 1 confirmed rework, and 1 awaiting review

  @S-055 @edge @criterion-5 @criterion-8
  Scenario: Treat a recorded no-rework decision as awaiting review when incident evidence is unavailable
    Given verified production history shows three deployments went live during the reporting period
    And a maintainer confirmed one deployment as an unplanned response to a production incident
    And a maintainer recorded no qualifying rework for the other two deployments
    And unavailable incident evidence could establish rework for only one of those two deployments
    When a maintainer runs the report on demand
    Then the report shows "Incomplete evidence" and omits the percentage
    And it shows 3 verified production deployments, 1 confirmed rework deployment, and 1 awaiting review

  @S-056 @edge @criterion-5 @criterion-8
  Scenario: Count all potentially affected deployments when unavailable evidence cannot be tied to deployment IDs
    Given verified production history shows four deployments went live during the reporting period
    And a maintainer confirmed one deployment as an unplanned response to a production incident
    And a maintainer recorded no qualifying rework for two deployments
    And the remaining deployment already awaits review because it has no maintainer disposition
    And unavailable incident evidence could establish rework but cannot be tied to specific deployment IDs
    When a maintainer runs the report on demand
    Then the report shows "Incomplete evidence" and omits the percentage
    And it shows 4 verified production deployments, 1 confirmed rework deployment, and 3 awaiting review
