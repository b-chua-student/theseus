Feature: Compare manuscript claims with selected library sources
  A writer can use the current manuscript and evidence from selected sources in one answer.

  Background:
    Given I have a manuscript open in the editor with the Assistant chat panel
    And my project has indexed library sources "Methods", "Replication" and "Pilot"

  @S-063 @criterion-1 @component
  Scenario: Add a second source without losing the first source or the manuscript
    Given "Manuscript" and "Methods" are checked in the Context dropdown
    When I check "Replication" in the same dropdown
    Then "Manuscript", "Methods" and "Replication" are checked
    And "Pilot" and "None" are unchecked

  @S-064 @criterion-1 @component
  Scenario: Removing one source narrows the next exchange
    Given "Manuscript", "Methods" and "Replication" are checked
    When I uncheck "Methods" and send my next question
    Then the exchange includes the current manuscript text
    And the selected source IDs contain only the ID of "Replication"
    And the exchange belongs to the same conversation

  @S-065 @criterion-1 @component
  Scenario: Clear a combined selection with None
    Given "Manuscript", "Methods" and "Replication" are checked
    When I choose "None" in the Context dropdown
    Then only "None" is checked

  @S-066 @criterion-1 @component
  Scenario: Clearing the last item selects None
    Given only "Methods" is checked
    When I uncheck "Methods"
    Then only "None" is checked

  @S-067 @criterion-2 @component
  Scenario: A combined send uses the draft as it reads when the writer asks
    Given I selected "Manuscript", "Methods" and "Replication"
    And I changed "12 samples" to "18 samples" in the draft without saving
    When I send "Which studies support my sample count?"
    Then one exchange includes the current editor text containing "18 samples"
    And its selected source IDs are exactly those of "Methods" and "Replication"

  @S-068 @criterion-2 @criterion-4 @acceptance
  Scenario: Tell the writer which selected study supports the manuscript claim
    Given my manuscript says the trial enrolled 18 participants
    And "Methods" reports 18 participants and "Replication" reports 24 for the same trial
    And the unselected source "Pilot" also reports 18 participants
    And I selected "Manuscript", "Methods" and "Replication"
    When I ask "Which selected studies support my enrollment figure?"
    Then one answer identifies "Methods" as supporting the draft's figure of 18
    And it explains that "Replication" reports 24 for the same trial
    And no passage from "Pilot" is supplied to the model or used in the answer

  @S-069 @criterion-3 @acceptance
  Scenario: Address the quoted passage when the draft contains two related claims
    Given my draft says "Adults recovered in 8 days" and "Children recovered in 5 days"
    And "Methods" reports that children recovered in 7 days
    And I selected "Manuscript" and "Methods"
    And I quoted "Children recovered in 5 days" from the editor
    When I ask "How does this passage compare with Methods?"
    Then the answer compares the quoted 5 days for children with the 7 days reported by "Methods"
    And it attributes the 5-day figure to the quoted passage

  @S-070 @criterion-4 @service
  Scenario Outline: Standalone selections retain their reference boundaries
    Given the manuscript contains a claim about sample size
    And "Methods" and "Pilot" each contain a matching passage
    When I ask about sample size with <selection>
    Then the model receives <draft input> as new manuscript material
    And library retrieval <retrieval behavior>

    Examples:
      | selection             | draft input       | retrieval behavior          |
      | Manuscript alone      | the current draft | is skipped                  |
      | only Methods selected | no text           | searches only Methods       |
      | only None selected    | no text           | is skipped                  |

  @S-071 @criterion-1 @component
  Scenario: Add a source to a combined selection with the keyboard
    Given "Manuscript" and "Methods" are checked in the open Context dropdown
    And keyboard focus is on the unchecked "Replication" item
    When I press Space and then Escape
    Then the dropdown closes with focus on the Context button
    And "Manuscript", "Methods" and "Replication" are checked when I reopen it

  @S-072 @criterion-5 @acceptance
  Scenario Outline: Explain a gap in one selected source while using the other
    Given I selected "Manuscript", "Methods" and "Replication"
    And "Methods" has a passage supporting the claim
    And "Replication" <condition>
    When I ask which selected studies support the claim
    Then the answer cites the supporting passage from "Methods"
    And it tells me <explanation>
    And the Assistant uses no evidence from "Pilot"

    Examples:
      | condition                               | explanation                                  |
      | became unavailable before the search    | Replication could not be checked             |
      | was searched and had no relevant result | no relevant passage was found in Replication |

  @S-073 @criterion-5 @acceptance
  Scenario: None of the selected sources supplies usable evidence
    Given I selected "Manuscript", "Methods" and "Replication"
    And "Methods" is unavailable and "Replication" has no relevant passage
    And unselected "Pilot" contains a matching passage
    When I ask whether the selected studies support the claim
    Then the answer says the claim could not be verified from the selection
    And it identifies the unavailable source and the source searched without a match
    And it neither labels the claim contradicted nor uses evidence from "Pilot"

  @S-074 @criterion-6 @component
  Scenario: Select sources across searches in a long library
    Given the open dropdown has more sources than fit onscreen
    And "Manuscript" and "Methods" are checked
    When I filter for "Replication", check it, and clear the filter
    Then "Methods" and "Replication" are both checked
    And "Manuscript" and "None" remain visible while I scroll the sources
    And the closed button reads "Manuscript + 2 sources"

  @S-075 @criterion-3 @service
  Scenario: The quoted passage travels as its own item
    Given I selected "Manuscript" and "Methods"
    And I quoted "Children recovered in 5 days" from the editor
    When I ask "How does this passage compare with Methods?"
    Then the exchange carries the quote "Children recovered in 5 days" exactly as written
    And the quote is separate from the question text

  @S-076 @criterion-1 @component
  Scenario: Changing the context keeps the same conversation
    Given I asked a question with only "Manuscript" checked
    When I choose "None" and ask a second question
    And I check "Methods" and ask a third question
    Then all three exchanges belong to the same conversation

  @S-077 @criterion-4 @service
  Scenario: A source from another project is never used
    Given "Manuscript" and "Methods" are checked
    And the request also names a source ID that belongs to another project
    When I ask about sample size
    Then the other project's source is not searched
    And no passage from it is supplied to the model

  @S-078 @criterion-2 @acceptance
  Scenario: Tell the writer when a selected study qualifies the claim
    Given my manuscript says the treatment works for all adults
    And "Methods" reports the effect only in adults under 40
    And I selected "Manuscript" and "Methods"
    When I ask "Do the selected studies support my claim?"
    Then the answer says "Methods" supports the claim only for adults under 40
    And it does not describe "Methods" as contradicting the claim

  @S-079 @criterion-5 @service
  Scenario: Source check results are passed to the model
    Given I selected "Manuscript", "Methods" and "Replication"
    And "Methods" is unavailable and "Replication" returns no relevant passage
    When I ask whether the selected studies support the claim
    Then the model receives "Methods" marked unavailable
    And the model receives "Replication" marked as searched without a match
    And the model receives no passage from "Pilot"
