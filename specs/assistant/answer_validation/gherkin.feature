Feature: Validate source-backed answers before display
  Users see answers checked against Source Library evidence before they are displayed.

  Background:
    Given the user asks when a pilot started and ended
    And the first search retrieves P1 from the selected pilot report, giving May as the start

  @S-001 @criterion-1
  Scenario: Display a supported answer
    Given the first search also retrieves P2 giving July as the end
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

  @S-004 @criterion-1 @criterion-3
  Scenario: Correct a mismatched citation
    Given only retrieved passage P2 establishes that the pilot ended in July
    And a retry is available
    When the Assistant drafts an answer that cites P1 for the July end date
    Then the Assistant corrects the citation to P2
    And the corrected answer is checked before it is displayed
    And the displayed answer cites P2 for July

  @S-005 @criterion-4
  Scenario: Retrieve missing evidence
    Given the initial passages omit the end date and a retry is available
    When the Assistant detects the missing evidence
    Then the next search retrieves P2 giving July as the end
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
    And a retry is still waiting for evidence when the request deadline cuts it short
    When 30 seconds have elapsed since the first draft was ready to check
    Then validation stops for this request
    And the user sees the verified May start citing P1 and an explanation of the missing end date

  @S-009 @criterion-7 @edge
  Scenario: Reach the deadline before any validation completes
    Given the first draft is waiting for its initial check to finish
    When 30 seconds have elapsed since that draft was ready to check
    Then the user sees “I couldn’t verify an answer within 30 seconds. Please try again.”
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
    When a service error prevents the check from completing before the deadline
    Then the user sees “I couldn’t finish checking this answer. Please try again.”
    And the unchecked draft stays hidden

  @S-012 @criterion-3 @edge
  Scenario: Distinguish the manuscript claim from what the selected report establishes
    Given the manuscript says the pilot ended on July 12
    And the retrieved report gives July without specifying a day
    And the draft says the report contradicts the manuscript
    When the Assistant checks and revises the answer
    Then the displayed answer attributes July 12 to the manuscript
    And it explains that the report leaves the exact day unverified

  @S-013 @criterion-7 @edge
  Scenario Outline: Apply the deadline response when validation fails at exactly 30 seconds
    Given the findings verified so far are <findings>
    When a validation service error occurs exactly 30 seconds after the first draft was ready
    Then the user sees only <deadline response>
    And the unchecked draft stays hidden

    Examples:
      | findings              | deadline response                                                                         |
      | the May start from P1 | the May start citing P1 and an explanation that the end date could not be checked in time |
      | no verified findings  | “I couldn’t verify an answer within 30 seconds. Please try again.”                        |

  @S-014 @criterion-10
  Scenario: Answer a directly supported question without generation
    Given the first search also retrieves P2 stating "The pilot ended in July."
    And the start and end months can both be established locally
    When the Assistant answers the question
    Then the displayed answer gives May citing P1 and July citing P2
    And the request made zero Gemini generation calls

  @S-015 @criterion-11
  Scenario: Verify an assisted answer against the exact excerpts it cites
    Given local selection cannot distinguish a pilot end date from a follow-up end date
    And P2 states "The pilot ended in July." and P3 states "Follow-up ended in August."
    When the single Gemini generation call proposes May citing P1 and July citing P2 with their exact supporting excerpts
    Then the Assistant locally verifies both claims against the question and their respective passages
    And the displayed answer gives May citing P1 and July citing P2
    And the entire request made one Gemini generation call

  @S-016 @criterion-11 @criterion-12 @edge
  Scenario: Withhold an unsupported year even when the quote is genuine
    Given the user also asks for the year the pilot ended
    And the only end-date excerpt is "The pilot ended in July."
    And one generation call proposes an end year citing that exact excerpt
    When local validation and a repeat search find no support for the proposed year
    Then the answer explains that the end year could not be verified
    And the proposed year is never displayed as a finding
    And the entire request made one Gemini generation call

  @S-017 @criterion-9 @criterion-12 @edge
  Scenario: A failed generation attempt consumes the request allowance
    Given local evidence selection is inconclusive
    When the only generation attempt fails before the deadline and prevents validation
    Then the writer sees the validation interruption message
    And no unchecked draft is displayed
    And the entire request made one Gemini generation call
