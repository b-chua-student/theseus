Feature: Validate source-backed answers before display
  Users see answers checked against Source Library evidence before they are displayed.

  Background:
    Given the user can access the selected Source Library report

  @S-098 @criterion-1
  Scenario: Display a supported answer
    Given the writer asks when the pilot started and ended
    And passages P1 and P2 give May as the start and July as the end
    When the Assistant drafts an answer that gives May citing P1 and July citing P2
    Then the user sees that answer
    And the answer was checked for relevance, claims, and citations before it was displayed

  @S-100 @criterion-3
  Scenario: Revise an overstated claim
    Given passage P2 in the Source Library gives July as the end month without an exact day
    And a retry is available
    When the Assistant drafts an answer claiming the pilot ended on July 12 citing P2
    Then the Assistant removes the unsupported day
    And the review confirms the narrower claim before display
    And the displayed answer states July as the end month without a day

  @S-101 @criterion-1 @criterion-3
  Scenario: Correct a mismatched citation
    Given only retrieved passage P2 establishes that the pilot ended in July
    And a retry is available
    When the Assistant drafts an answer that cites P1 for the July end date
    Then the Assistant corrects the citation to P2
    And the review confirms that P2 supports the corrected finding
    And the displayed answer cites P2 for July

  @S-102 @criterion-4
  Scenario: Retrieve missing evidence
    Given P1 gives the May start and the draft needs additional evidence for the end date before review
    When the Assistant detects the missing evidence
    Then the next search retrieves P2 giving July as the end
    And the resulting answer is checked against P1 and P2 before it is displayed
    And the displayed answer cites P1 for May and P2 for July

  @S-099 @criterion-2 @edge
  Scenario: Withhold an answer to a different question
    Given the writer asks for the pilot dates and P3 names the sponsor
    When the Assistant drafts an answer that only names the sponsor citing P3
    Then the relevance check fails
    And the user never sees that draft as the answer

  @S-103 @criterion-5 @edge
  Scenario: Explain a remaining gap after evidence recovery
    Given P1 gives the May start and two further searches find no end date
    When the review confirms the start and the gap in the retrieved evidence
    Then the answer cites P1 for May and explains that the passages do not establish the end date
    And the request ends after one draft attempt and one review attempt

  @S-104 @criterion-6
  Scenario: Show progress only when validation exceeds five seconds
    Given the first draft is ready to check
    When validation continues past five seconds
    Then the user saw no progress message during the first five seconds
    And the user now sees “Checking the answer against your sources…”
    And the unchecked draft stays hidden throughout validation

  @S-105 @criterion-7 @edge
  Scenario: Return verified partial findings at the deadline
    Given the Assistant has verified the May start against P1
    And the checked passages leave the end date unresolved
    And an unchecked generated draft is available
    And a retry is still waiting for evidence when the request deadline cuts it short
    When 30 seconds have elapsed since the first draft was ready to check
    Then validation stops for this request
    And the user sees the verified May start citing P1 and an explanation of the missing end date
    And no unverified draft is offered

  @S-106 @criterion-7 @edge
  Scenario: Reach the deadline before any validation completes
    Given the first draft is waiting for its initial check to finish
    And no eligible draft text remains to offer
    When 30 seconds have elapsed since that draft was ready to check
    Then the user sees “I couldn’t verify an answer within 30 seconds. Please try again.”
    And the unchecked draft stays hidden

  @S-107 @criterion-8 @edge
  Scenario: Withhold an entirely off-topic draft after review
    Given the writer asks for dates and the draft only identifies the sponsor
    When the review finds the draft off-topic
    Then the writer sees “I couldn’t produce a verified answer to your question.”
    And no sponsor claim or evidence gap is displayed
    And no further generation is attempted

  @S-108 @criterion-9 @edge
  Scenario: Explain an interrupted validation
    Given a draft is awaiting validation
    When a service error prevents the check from completing before the deadline
    Then the user sees “I couldn’t finish checking this answer. Please try again.”
    And the unchecked draft stays hidden

  @S-109 @criterion-3 @edge
  Scenario: Distinguish the manuscript claim from what the selected report establishes
    Given the manuscript says the pilot ended on July 12
    And the retrieved report gives July without specifying a day
    And the draft says the report contradicts the manuscript
    When the Assistant checks and revises the answer
    Then the displayed answer attributes July 12 to the manuscript
    And it explains that the report leaves the exact day unverified

  @S-110 @criterion-7 @edge
  Scenario Outline: Apply the deadline response when validation fails at exactly 30 seconds
    Given no eligible unchecked draft text is available
    And the findings verified so far are <findings>
    When a validation service error occurs exactly 30 seconds after the first draft was ready
    Then the user sees only <deadline response>
    And the unchecked draft stays hidden

    Examples:
      | findings              | deadline response                                                                         |
      | the May start from P1 | the May start citing P1 and an explanation that the end date could not be checked in time |
      | no verified findings  | “I couldn’t verify an answer within 30 seconds. Please try again.”                        |

  @S-111 @criterion-10
  Scenario: Reuse an exact fully reviewed answer
    Given a fully reviewed answer with citations is available in this authorized conversation
    And the selected sources, evidence, citation details, context used and review configuration are unchanged
    When the writer repeats the exact question
    Then the writer receives the reviewed answer with the same citations
    And the request uses zero Gemini generation attempts

  @S-112 @criterion-11
  Scenario: Review which group a number describes
    Given the writer asks how many schools enrolled in total
    And P1 reports 75 schools overall and 25 schools per group
    And a new draft incorrectly answers 25 citing P1
    When the review checks the question and P1
    Then the displayed finding gives the reviewed total of 75 citing P1
    And the request uses one draft attempt and one review attempt

  @S-113 @criterion-11 @criterion-12 @edge
  Scenario: Withhold an unsupported year even when the quote is genuine
    Given the user also asks for the year the pilot ended
    And the only end-date excerpt is "The pilot ended in July."
    And the draft proposes an end year citing that exact excerpt
    When a repeat search and the review find no support for the proposed year
    Then the answer explains that the end year could not be verified
    And the proposed year is never displayed as a finding
    And the request uses one draft attempt and one review attempt

  @S-114 @criterion-9 @criterion-12 @edge
  Scenario Outline: Count failed attempts without automatic retries
    Given a new question with retrieved passages
    When the <stage> fails before the deadline
    Then the writer sees the validation interruption message
    And the request ends after <count> generation attempts with no draft displayed

    Examples:
      | stage  | count |
      | draft  | 1     |
      | review | 2     |

  @S-115 @criterion-7 @edge
  Scenario: Offer pending claims on request when validation runs out of time
    Given Gemini returned a draft before the validation deadline
    And no finding is verified and one draft claim still awaits a check
    And another claim about July 12 was already found unsupported
    When the 30-second validation window ends
    Then the writer sees “View unverified draft” with the draft text hidden
    And selecting “View unverified draft” reveals only the pending claim with an unverified label
    And the July 12 claim is absent
    And the entire exchange made one Gemini generation call

  @S-116 @criterion-7 @edge
  Scenario: Withhold a draft with no eligible claims
    Given Gemini returned a draft whose claims were all found unsupported or off-topic
    And no finding is verified
    When the validation deadline cuts a retry short
    Then the writer sees “I couldn’t verify an answer within 30 seconds. Please try again.”
    And no unverified draft is offered

  @S-117 @criterion-10 @edge
  Scenario Outline: Require fresh review when reuse conditions change
    Given a fully reviewed answer is available for an earlier question
    And the current authorized search finds evidence
    When the writer asks again with a different <input>
    Then the Assistant drafts and reviews a fresh answer

    Examples:
      | input                  |
      | question wording       |
      | selected source        |
      | retrieved passage text |
      | citation location      |
      | conversation context   |
      | authorized conversation |
      | review configuration   |

  @S-118 @criterion-10 @edge
  Scenario Outline: Retry an exchange that had no fully reviewed success
    Given the previous exchange ended with <outcome>
    When the writer retries the question and the search finds evidence
    Then the previous result is withheld from reuse
    And a fresh draft and review are attempted

    Examples:
      | outcome          |
      | a partial answer |
      | an interruption  |
      | a timeout        |
      | an unverified draft |

  @S-119 @criterion-13
  Scenario: Explain an empty search without generation
    Given the selected report previously supported an answer
    When the current search succeeds and returns no passages
    Then the writer learns that the search found insufficient evidence
    And the request uses zero Gemini generation attempts

  @S-120 @criterion-9 @criterion-13 @edge
  Scenario: Distinguish a failed search from an empty search
    Given the writer asks about a selected report
    When the initial search fails
    Then the writer sees the interruption message
    And no source gap is claimed
    And the request uses zero Gemini generation attempts
