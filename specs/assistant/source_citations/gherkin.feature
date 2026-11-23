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
    Then the "Trial Report" item opens in the Source Library

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
    Then the "Workshop Summary" item opens in the Source Library

  @S-006 @constraint
  Scenario: Citations only refer to sources used as evidence for the answer
    Given the Source Library contains "Trial Report" and "Unrelated Memo"
    And an Assistant answer uses only "Trial Report" as evidence
    When I read the answer
    Then every citation in the answer identifies "Trial Report"
    And no citation identifies "Unrelated Memo"

  @S-007 @constraint
  Scenario: An answer without source evidence shows no citations
    Given an Assistant answer uses no Source Library item as evidence
    When I read the answer
    Then the answer shows no citations

  @S-008 @criterion-1 @open-question
  Scenario: A saved answer still shows its citations when reopened
    Given I saved an Assistant answer that cites "Trial Report" on page 12
    When I reopen the conversation later
    Then the citation still identifies "Trial Report" and shows page 12

  @S-009 @criterion-1 @open-question
  Scenario: A citation to a removed source is marked unavailable
    Given a saved Assistant answer cites "Trial Report"
    And "Trial Report" has since been removed from the Source Library
    When I read the citation
    Then it still identifies "Trial Report"
    And it shows that the source is no longer available
    And I cannot open the source
