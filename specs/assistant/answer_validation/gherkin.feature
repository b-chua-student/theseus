Feature: Validate source-backed answers before display

  Background:
    Given the project's Source Library is searchable
    And the user asks the Assistant when a pilot started and ended
    And passage P1 in the Source Library states that the pilot started in May

  @S-001
  Scenario: Display a supported answer
    Given passage P2 in the Source Library states that the pilot ended in July
    When the Assistant drafts an answer that gives May citing P1 and July citing P2
    Then the user sees that answer
    And the answer was validated for relevance, claims, and citations before it was displayed

  @S-002
  Scenario: Withhold an answer to a different question
    Given passage P3 in the Source Library names the pilot sponsor
    And a retry is available
    When the Assistant drafts an answer that only names the sponsor citing P3
    Then the user never sees that draft
    And the Assistant drafts a new answer before displaying anything

  @S-003
  Scenario: Revise an overstated claim
    Given passage P2 in the Source Library gives July as the end month without an exact day
    And a retry is available
    When the Assistant drafts an answer claiming the pilot ended on July 12 citing P2
    Then the user never sees the claim of July 12
    And the revised answer is validated before it is displayed
    And the displayed answer states July as the end month without a day

  @S-004
  Scenario: Correct a mismatched citation
    Given only passage P2 in the Source Library establishes that the pilot ended in July
    And a retry is available
    When the Assistant drafts an answer that cites P1 for the July end date
    Then the corrected answer is validated before it is displayed
    And the displayed answer cites P2 for July
    And the displayed answer does not cite P1 for July

  @S-005
  Scenario: Retrieve missing evidence
    Given the first search returns passage P1 and no passage with the end date
    And passage P2 in the Source Library documents a July end date
    And a retry is available
    When the Assistant finds the evidence is insufficient to answer the question
    Then the Assistant searches the Source Library again
    And the resulting answer is validated against P1 and P2 before it is displayed
    And the displayed answer cites P1 for May and P2 for July

  @S-006
  Scenario: Explain a remaining gap at the retry limit
    Given the request has used all allowed retries
    And no passage in the Source Library establishes the end date
    When the Assistant completes the request
    Then the Assistant makes no further retry
    And the displayed answer cites P1 for the May start
    And the displayed answer says the Source Library does not establish an end date

  @S-007
  Scenario: Redraft an irrelevant answer at the retry limit
    Given the request has used all allowed retries
    And every draft so far addressed a different question
    When the Assistant completes the request
    Then the user never sees an irrelevant draft
    And the user sees a message that the Assistant could not produce an answer from the Source Library

  @S-008
  Scenario: Count every kind of retry against one limit
    Given the request allows one retry
    And the first draft overstates the end date
    And the revised draft still needs a new search
    When the Assistant completes the request
    Then the Assistant makes no second retry
    And the displayed answer reports what the Source Library supports and the remaining gap

  @S-009
  Scenario: Limit the answer when no sources can be used
    Given the Source Library has no passage that relates to the question
    And no retries remain
    When the Assistant completes the request
    Then the displayed answer says the Source Library does not cover the question
    And the answer cites no passage

  @S-010
  Scenario: Report a failure during validation
    Given the Assistant model fails while validating a draft
    When the Assistant completes the request
    Then the user sees an error and no draft answer
    And the user can ask the question again

  @S-011
  Scenario Outline: Skip validation outside the Source Library scope
    Given the user asks with the "<scope>" context scope
    When the Assistant answers
    Then the answer is displayed without source validation

    Examples:
      | scope      |
      | none       |
      | manuscript |
