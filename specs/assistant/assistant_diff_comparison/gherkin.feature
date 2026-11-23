Feature: Ask the Assistant about changes between saved revisions

  @S-001 @criterion-1
  Scenario: Explain an edit using only the selected revision pair
    Given a draft has saved revisions A, B, and C in that order
    And the submission deadline changed from Friday in A to Monday in B
    And a reviewer was added only in C
    And I have selected A as the starting revision and B as the ending revision
    When I ask the Assistant "What changed?"
    Then the answer explains that the deadline moved from Friday to Monday
    And the answer does not report the reviewer addition as a change between A and B

  @S-002 @criterion-1
  Scenario: Ask about a specific detail in the comparison
    Given I have selected two saved revisions of a draft
    And their comparison shows that the appendix title changed from "Notes" to "Sources"
    When I ask the Assistant "What was the appendix renamed to?"
    Then the answer identifies "Sources" as the new appendix title

  @S-003 @criterion-1
  Scenario: Compare saved revisions with identical content
    Given I have selected two saved revisions of a draft
    And their comparison shows no differences
    When I ask the Assistant "What changed?"
    Then the answer tells me that the selected revisions have identical content
