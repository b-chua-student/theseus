Feature: Evidence-use feedback for Source Library answers
  As a user asking a question in the Source Library
  I want to see whether the Assistant used library evidence in its answer
  So that I can tell when my library informed the response.

  @S-001 @criterion-1
  Scenario: The answer draws on a relevant library passage
    Given a Source Library search returns a relevant passage for my question
    When the Assistant uses that passage to answer my question
    Then the answer indicates that the Assistant used library evidence

  @S-002 @criterion-2
  Scenario: The search finds no relevant evidence
    Given a Source Library search returns no relevant passages for my question
    When the Assistant answers my question
    Then the answer clearly states that it was generated without library evidence

  @S-003 @criterion-2
  Scenario: Retrieved passages are unused
    Given a Source Library search returns passages for my question
    When the Assistant answers my question without using any of those passages or other library evidence
    Then the answer clearly states that it was generated without library evidence

  @S-004 @criterion-2
  Scenario: The search fails but the Assistant still answers
    Given a Source Library search fails for my question
    When the Assistant answers my question
    Then the answer clearly states that it was generated without library evidence

  @S-005 @criterion-3
  Scenario: Answers outside the Source Library show no evidence feedback
    Given I ask a question without using the Source Library
    When the Assistant answers my question
    Then the answer does not indicate whether library evidence was used

  @S-006 @criterion-1
  Scenario: Evidence-use feedback remains when I reopen a conversation
    Given the Assistant answered my question using library evidence
    When I reopen the conversation
    Then the answer still indicates that the Assistant used library evidence
