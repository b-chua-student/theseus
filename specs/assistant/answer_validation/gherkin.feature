Feature: Validate source-backed answers before display
  Users see answers checked against Source Library evidence before they are displayed.

  Background:
    Given the user asks when a pilot started and ended
    And passage P1 in the Source Library states that the pilot started in May

  @S-001 @criterion-1
  Scenario: Display a supported answer
    Given passage P2 in the Source Library states that the pilot ended in July
    When the Assistant drafts an answer that gives May citing P1 and July citing P2
    Then the user sees that answer
    And the answer was checked for relevance, claims, and citations before it was displayed

  @S-003 @criterion-3
  Scenario: Revise an overstated claim
    Given passage P2 in the Source Library gives July as the end month without an exact day
    And a retry is available
    When the Assistant drafts an answer claiming the pilot ended on July 12 citing P2
    Then the Assistant removes the unsupported day
    And the revised answer is checked before it is displayed
    And the displayed answer states July as the end month without a day

  @S-004 @criterion-3
  Scenario: Correct a mismatched citation
    Given only passage P2 in the Source Library establishes that the pilot ended in July
    And a retry is available
    When the Assistant drafts an answer that cites P1 for the July end date
    Then the Assistant corrects the citation to P2
    And the corrected answer is checked before it is displayed
    And the displayed answer cites P2 for July

  @S-005 @criterion-4
  Scenario: Retrieve missing evidence
    Given the initial passages omit the end date
    And a retry is available
    And passage P2 in the Source Library documents a July end date
    When the Assistant detects the missing evidence
    Then the Assistant searches again
    And the resulting answer is checked against P1 and P2 before it is displayed
    And the displayed answer cites P1 for May and P2 for July

  @S-002 @criterion-2 @edge
  Scenario: Withhold an answer to a different question
    Given passage P3 in the Source Library names the pilot sponsor
    When the Assistant drafts an answer that only names the sponsor citing P3
    Then the relevance check fails
    And the user never sees that draft as the answer

  @S-006 @criterion-5 @edge
  Scenario: Explain a remaining gap at the retry limit
    Given the initial draft failed validation
    And the first retry revised and rechecked the draft
    And the second retry retrieved more evidence, revised the draft, and rechecked it
    And no passage in the Source Library establishes the end date
    When the Assistant completes the request
    Then the Assistant makes no further retry
    And the displayed answer cites P1 for the May start
    And the displayed answer explains that the available passages do not establish an end date

  @S-007 @criterion-6
  Scenario: Show progress only when validation exceeds five seconds
    Given the first draft is ready to check
    When validation continues past five seconds
    Then the user saw no progress message during the first five seconds
    And the user now sees “Checking the answer against your sources…”
    And the unchecked draft stays hidden throughout validation

  @S-008 @criterion-7 @edge
  Scenario: Return verified partial findings at the deadline
    Given the Assistant has verified the May start against P1
    And the checked passages leave the end date unresolved
    And a retry is underway
    When 30 seconds have elapsed since the first draft was ready to check
    Then validation stops for this request
    And the user sees the verified May start citing P1 and an explanation of the missing end date

  @S-009 @criterion-7 @edge
  Scenario: Reach the deadline before any validation completes
    Given the first draft is waiting for its initial check to finish
    When 30 seconds have elapsed since that draft was ready to check
    Then the user is told the answer could not be checked
    And the unchecked draft stays hidden

  @S-010 @criterion-8 @edge
  Scenario: Exhaust both retries with off-topic drafts
    Given the initial draft and both retried drafts answer only who sponsored the pilot
    And the checked passages establish both the start and end dates
    When the last draft fails the relevance check
    Then the user sees “I couldn’t produce a verified answer to your question.”
    And no sponsor-only draft or claim of missing source evidence is displayed
    And the Assistant makes no further retry

  @S-011 @criterion-9 @edge
  Scenario: Explain an interrupted validation
    Given a draft is awaiting validation
    When a service error prevents the check from completing
    Then the user sees “I couldn’t finish checking this answer. Please try again.”
    And the unchecked draft stays hidden
