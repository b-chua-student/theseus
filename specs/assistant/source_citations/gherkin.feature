Feature: Verify sources cited in Assistant answers

  @S-001 @criterion-1
  Scenario: Each cited statement identifies its own supporting source
    Given an Assistant answer uses "Trial Report" as evidence for the sample size
    And it uses "Field Notes" as evidence for the interview dates
    When I read the answer
    Then the citation for the sample size identifies "Trial Report"
    And the citation for the interview dates identifies "Field Notes"

  @S-002 @criterion-1
  Scenario: Open the source supporting a statement from the answer
    Given the sample size in an Assistant answer is supported by "Trial Report"
    When I open the sample size citation from the answer
    Then I see the "Trial Report" item in the Source Library

  @S-003 @criterion-2
  Scenario: Find the supporting page in a paginated source
    Given an Assistant answer cites evidence from page 12 of "Trial Report"
    When I read the citation
    Then it identifies "Trial Report" and shows page 12

  @S-004 @criterion-2
  Scenario: Find a supporting passage in a source without page numbers
    Given an Assistant answer cites the "Exit interviews" section of "Field Notes"
    And "Field Notes" has no page numbers
    When I read the citation
    Then it identifies "Field Notes" and shows the section name "Exit interviews"

  @S-005 @criterion-3
  Scenario: Verify the source even when the evidence has no recorded location
    Given an Assistant answer cites "Workshop Summary" with no page number or passage location
    And the citation identifies "Workshop Summary"
    When I open that citation from the answer
    Then I see the "Workshop Summary" item in the Source Library
