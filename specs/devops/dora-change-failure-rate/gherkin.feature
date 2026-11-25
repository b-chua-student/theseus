Feature: Track DORA change failure rate
  Theseus maintainers can see how often production deployments require immediate intervention.

  Background:
    Given each confirmed intervention has an incident record that a maintainer confirmed
    And the record identifies the original production deploy ID and confirms that the deploy caused the issue
    And the record lists the intervention type and start time and links the rollback deploy or hotfix PR

  @S-028 @criterion-1
  Scenario: Report the share of production deployments requiring intervention
    Given complete evidence and Render history showing 4 production deployments and 1 staging deployment within the reporting period
    And one production deployment required a confirmed rollback within 24 hours of going live
    And another production deployment required a confirmed hotfix within 24 hours of going live
    And the staging deployment required immediate intervention
    And the other two production deployments required no intervention
    When a maintainer reviews the change failure rate report
    Then the report shows 2 production deployments requiring immediate intervention
    And the report shows 4 total production deployments
    And the change failure rate is 50%

  @S-031 @criterion-3
  Scenario: Run the report on demand
    Given a maintainer wants the latest change failure rate
    When the maintainer requests a report on demand
    Then a change failure rate report run starts

  @S-032 @criterion-4
  Scenario: Run the report automatically after a merge into main
    Given a change is ready to merge into main
    When the change is merged into main
    Then a change failure rate report run starts automatically for that merge

  @S-037 @criterion-9 @criterion-11
  Scenario Outline: Create an incident issue for a corrective production deployment
    Given a <corrective deployment> has no linked GitHub incident issue
    When the corrective deployment goes live in production
    Then a GitHub incident issue is created with a link to the corrective action
    And the original deployment attribution is pending maintainer confirmation

    Examples:
      | corrective deployment                                                         |
      | rollback                                                                      |
      | hotfix merged directly into main from a pull request labeled production-hotfix |

  @S-038 @criterion-9 @criterion-11
  Scenario: Record a corrective deployment on its linked incident issue
    Given a hotfix pull request labeled production-hotfix merged into staging and explicitly links a GitHub incident issue
    And an unlabeled promotion pull request carries the hotfix from staging into main
    When the promoted hotfix goes live in production
    Then the linked issue records the original hotfix pull request and pending attribution
    And no new incident issue is created

  @S-029 @criterion-1 @criterion-2 @edge
  Scenario: Count a deployment once when it requires several interventions
    Given complete evidence for 4 production deployments in the report
    And one production deployment required both a confirmed rollback and a confirmed hotfix within 24 hours of going live
    And the other three production deployments required no intervention
    When a maintainer reviews the change failure rate report
    Then the report shows 1 production deployment requiring immediate intervention
    And the report shows 4 total production deployments
    And the change failure rate is 25%

  @S-030 @criterion-1 @edge
  Scenario: Report zero percent when no production deployment requires intervention
    Given complete evidence for 4 production deployments in the report
    And none required immediate intervention
    When a maintainer reviews the change failure rate report
    Then the report shows 0 production deployments requiring immediate intervention
    And the report shows 4 total production deployments
    And the change failure rate is 0%

  @S-033 @criterion-5 @edge
  Scenario: Attribute an intervention at the 24-hour boundary to the original period
    Given a production deployment went live near the end of a reporting period
    And complete evidence shows its confirmed rollback started exactly 24 hours after it went live, in the next reporting period
    And another production deployment in the original period had a confirmed hotfix start 25 hours after it went live
    When a maintainer reviews the report for the original period
    Then the report counts the deployment that required the rollback as requiring immediate intervention
    And the report excludes the deployment that required the hotfix from the intervention count

  @S-034 @criterion-6 @edge
  Scenario: Report an unavailable rate for an empty period
    Given complete production deployment history confirms there were no deployments in the report period
    When a maintainer reviews the change failure rate report
    Then the report shows 0 production deployments requiring immediate intervention
    And the report shows 0 total production deployments
    And the rate is unavailable

  @S-035 @criterion-7 @criterion-12 @edge
  Scenario Outline: Identify incomplete evidence
    Given the report has confirmed counts for some deployments
    And <evidence gap>
    When a maintainer reviews the change failure rate report
    Then the report marks the rate unavailable due to incomplete evidence
    And the report identifies the missing evidence
    And any displayed counts are labeled as confirmed so far

    Examples:
      | evidence gap                                                                                          |
      | part of the production deployment history is unavailable                                              |
      | a pending hotfix incident could add an eligible deployment to the intervention count under the 24-hour rule  |

  @S-036 @criterion-8 @edge
  Scenario Outline: Apply the same cutoff to each trigger
    Given the report starts at 12:00 UTC on November 25
    And complete Render production history shows deployments went live at 11:00, 12:00, and 13:00 UTC on November 24
    And only the deployment at <deployment time> UTC on November 24 required a confirmed rollback 1 hour after going live
    When a maintainer reviews the report started <trigger>
    Then the report displays a start of 12:00 UTC on October 25 and a cutoff of 12:00 UTC on November 24
    And the report shows <intervention count> production deployments requiring immediate intervention
    And the report shows 2 total production deployments
    And the change failure rate is <rate>

    Examples:
      | trigger                                | deployment time | intervention count | rate |
      | on demand                              | 12:00           | 1                  | 50%  |
      | on demand                              | 13:00           | 0                  | 0%   |
      | automatically after a merge into main  | 12:00           | 1                  | 50%  |
      | automatically after a merge into main  | 13:00           | 0                  | 0%   |

  @S-039 @criterion-10 @edge
  Scenario: Record a corrective deployment only once
    Given a production rollback is already recorded on one GitHub incident issue
    When the same rollback deployment is processed again
    Then one GitHub incident issue contains the rollback
    And that issue contains one entry for the rollback deployment

  @S-040 @criterion-8 @edge
  Scenario: Exclude deployments at the start of the reporting period
    Given the report starts at 12:00 UTC on November 25
    And complete Render production history shows deployments went live at 11:59, 12:00, and 12:01 UTC on October 25
    And the deployment at 12:01 UTC required no intervention
    When a maintainer reviews the report
    Then the report displays a start of 12:00 UTC on October 25
    And the report shows 1 total production deployment
    And the change failure rate is 0%

  @S-041 @criterion-12 @edge
  Scenario: Publish the rate when a pending incident cannot affect it
    Given a report has complete evidence for 2 eligible production deployments with no qualifying interventions
    And a pending hotfix incident started more than 24 hours after both deployments went live
    When a maintainer reviews the report
    Then the report shows 0 production deployments requiring immediate intervention
    And the report shows 2 total production deployments
    And the change failure rate is 0%
