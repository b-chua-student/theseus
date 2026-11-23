Feature: Evidence-use feedback for Source Library answers
  As a user asking a question in the Source Library
  I want to see whether the Assistant used library evidence in its answer
  So that I can tell when my library informed the response.

  @S-001
  Scenario: The answer draws on a relevant library passage
    Given a Source Library search returns a relevant passage for my question
    When the Assistant uses that passage to answer my question
    Then the answer indicates that the Assistant used library evidence

  @S-002
  Scenario: The search finds no relevant evidence
    Given a Source Library search finds no relevant evidence for my question
    When the Assistant answers my question without library evidence
    Then the answer clearly states that it was generated without library evidence

  @S-003
  Scenario: Retrieved passages are unused
    Given a Source Library search returns passages for my question
    When the Assistant answers my question without using any of those passages or other library evidence
    Then the answer clearly states that it was generated without library evidence
