Feature: Validate source-backed answers before display

  Background:
    Given the user asks when a pilot started and ended
    And passage P1 states that the pilot started in May

  @S-001
  Scenario: Display a supported answer
    Given passage P2 states that the pilot ended in July
    When a draft answers May citing P1 and July citing P2
    Then the Assistant displays the answer after validating its relevance, claims, and citations

  @S-002
  Scenario: Withhold an answer to a different question
    Given passage P3 names the pilot sponsor
    When a draft only names the sponsor and cites P3
    Then the relevance check fails
    And the user never sees that draft as the answer

  @S-003
  Scenario: Revise an overstated claim
    Given passage P2 gives July as the end month without an exact day
    And a retry is available
    When a draft claims the pilot ended on July 12 citing P2
    Then the Assistant removes the unsupported day
    And it checks the revised answer before displaying it

  @S-004
  Scenario: Correct a mismatched citation
    Given only passage P2 establishes that the pilot ended in July
    And a retry is available
    When a draft cites P1 for the July end date
    Then the Assistant corrects the citation to P2
    And it checks the corrected draft before displaying it

  @S-005
  Scenario: Retrieve missing evidence
    Given the initial passages omit the end date
    And a retry is available
    And a further search would return passage P2 documenting a July end date
    When the Assistant detects the missing evidence
    Then it searches again and checks the resulting draft against P1 and P2
    And the displayed answer cites P1 for May and P2 for July

  @S-006
  Scenario: Explain a remaining gap at the retry limit
    Given the request has used all allowed retries
    And no retrieved passage establishes the end date
    When the Assistant completes the request
    Then it makes no further retry
    And the displayed answer cites P1 for the May start
    And it explains that the available passages do not establish an end date
