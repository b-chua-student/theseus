Feature: Validate source-backed answers before display
  Writers can check what the selected sources establish about their question.

  Background:
    Given the project's Source Library is searchable

  @S-001 @criterion-1
  Scenario: Display a supported answer
    Given the writer asks when a pilot started and ended using their selected sources
    And retrieved passages P1 and P2 give the May start and July end respectively
    When the Assistant checks a draft giving May with P1 and July with P2
    Then the writer sees May cited to P1 and July cited to P2

  @S-002 @criterion-2
  Scenario: Replace an answer to a different question
    Given the writer asks when the pilot started and the retrieved passage P1 gives May
    And the first draft only names the sponsor and a retry is available
    When the Assistant completes the request
    Then the writer sees the checked replacement giving May and citing P1
    And the sponsor-only draft is never displayed

  @S-003 @criterion-3
  Scenario: Correct an overstated date
    Given the writer asks when the pilot ended
    And retrieved passage P2 gives July without specifying a day
    And a retry is available
    When the Assistant checks a draft claiming July 12 based on P2
    Then the writer sees a checked answer citing P2 for July without claiming a day

  @S-004 @criterion-3
  Scenario: Correct a mismatched citation
    Given the writer asks when the pilot ended
    And retrieved passage P1 gives the start date and only retrieved passage P2 gives the July end
    And a retry is available
    When the Assistant checks a draft citing P1 for the end date
    Then the checked answer cites P2 for July
    And the answer does not cite P1 for the end date

  @S-005 @criterion-4
  Scenario: Retrieve missing evidence and check the resulting answer
    Given the writer asks when the pilot started and ended using the selected pilot report
    And the first search retrieves only P1 giving May as the start
    And a repeat search of the report returns P2 giving July as the end
    And a retry is available
    When the Assistant finds that the first search cannot establish the end date
    Then the Assistant searches again for evidence of the end date
    And the checked answer cites P1 for May and P2 for July

  @S-006 @criterion-5 @edge
  Scenario: Explain a remaining gap at the retry limit
    Given the writer asks when the pilot started and ended
    And retrieved passage P1 gives May as the start but no selected passage establishes the end
    And no retries remain
    When the Assistant completes the request
    Then the answer cites P1 for May and says the selected sources do not establish the end date

  @S-007 @criterion-2 @edge
  Scenario: Withhold an irrelevant draft at the retry limit
    Given the writer asks when the pilot started
    And the retrieved passages identify only the sponsor
    And every draft answers only who sponsored the pilot and no retries remain
    When the Assistant completes the request
    Then no sponsor-only draft is displayed
    And the Assistant makes no further retry
    And the writer is told that the retrieved passages do not establish the start date

  @S-008 @criterion-5 @edge
  Scenario: Stop when the request has exhausted its retry allowance
    Given the writer asks when the pilot started and ended
    And the request has reached its retry limit
    And the retrieved passages establish the May start but contain no end date
    When the Assistant completes the request
    Then it makes no further search or revision
    And the answer reports the supported start and explains that the end date is unverified

  @S-009 @criterion-5 @edge
  Scenario: Explain when no selected evidence answers the question
    Given the writer asks when the pilot started
    And no relevant passage was retrieved from the selected sources and no retries remain
    When the Assistant completes the request
    Then the answer says the start date could not be verified from the selection
    And the answer cites no passage

  @S-010 @criterion-2 @edge
  Scenario: Withhold a draft when validation cannot complete
    Given the writer asks a source-backed question
    When a service error prevents the Assistant from checking its draft
    Then the unchecked draft is never displayed

  @S-012 @criterion-3 @edge
  Scenario: Correct a claim that an unlisted pilot site was excluded
    Given the writer asks whether a third site participated in the pilot
    And the retrieved report names two sites without saying the list is complete
    And a draft says the third site was excluded
    And a retry is available
    When the Assistant checks the draft against the report
    Then the checked answer explains that the report does not establish whether the third site participated
