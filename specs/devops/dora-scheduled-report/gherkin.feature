Feature: Scheduled DORA metrics report
  Theseus maintainers can review the five DORA metrics together on a weekly schedule or on demand.

  @S-079 @criterion-1 @criterion-2 @criterion-4
  Scenario: Publish a consolidated report at the scheduled time
    Given evidence is available for all five metrics
    When it is Sunday at 00:00 Manila time (Saturday at 16:00 UTC)
    Then the run starts without maintainer action
    And the displayed report matches the single downloadable Markdown file under "reports/dora/"
    And the report shows its generation time in UTC and contains no credentials
    And the report includes these metric sections
      | Metric                                   |
      | Deployment frequency                     |
      | Feature PR merge-to-production lead time |
      | Change failure rate                      |
      | Failed deployment recovery time         |
      | Deployment rework rate                   |
    And each result follows its existing metric definition, evidence rules, and reporting period
    And individual report entry points stay available and deployments, incident records, and repository files stay unchanged

  @S-081 @criterion-2 @criterion-4 @criterion-5
  Scenario: Publish a consolidated report on demand
    Given it is outside the scheduled reporting time
    And evidence is available for all five metrics
    When a Theseus maintainer manually starts a consolidated report run
    Then the displayed report matches the single downloadable Markdown file under "reports/dora/"
    And the report shows the same five metric sections as a scheduled report
    And the report shows its generation time in UTC and contains no credentials
    And each result follows its existing metric definition, evidence rules, and reporting period
    And the individual report entry points remain available

  @S-080 @criterion-3 @edge
  Scenario: Publish available results when a metric lacks evidence
    Given the scheduled report cannot verify one metric
    And evidence is available for the other four metrics
    When the scheduled report is generated
    Then the unavailable metric's section identifies the evidence gap
    And the other four results are visible in the report

  @S-082 @criterion-5
  Scenario: Recover a dropped scheduled run manually
    Given a scheduled report run was dropped
    When a Theseus maintainer manually starts a consolidated report run
    Then the run displays the report and makes it available for download
    And no automatic recovery run was started for the dropped run

  @S-083 @criterion-2
  Scenario: Display a report that exceeds the size of one display section
    Given the consolidated Markdown exceeds the run page's limit for a single display section
    When the report is published
    Then the run page displays the full report across multiple sections in order
    And the combined displayed content matches the single downloadable Markdown file
