Feature: Compare manuscript claims with selected library sources
  A writer can use the current manuscript and evidence from selected sources in one answer.

  # Source: https://github.com/b-chua-student/theseus/issues/120 (Markdown body, counted from the title).
  # @from-ticket identifies explicit ticket behavior. @assumed identifies a detail supplied outside the issue body.
  # Each source note names the ticket line and, for adopted clarifications, a link key from brief.md.
  # Open Questions at the end preserve proposed examples separately from the acceptance scenarios.

  Background:
    Given I have a manuscript open in the editor with the Assistant chat panel
    And my project has indexed library sources "Methods", "Replication" and "Pilot"

  # from ticket — #120 L13, L18: choose multiple sources alongside the manuscript.
  @S-063 @criterion-1 @component @from-ticket
  Scenario: Add a second source without losing the first source or the manuscript
    Given "Manuscript" and "Methods" are checked
    When I check "Replication" in the same dropdown
    Then "Manuscript", "Methods" and "Replication" are checked
    And "Pilot" is unchecked

  # from ticket — #120 L13, L23: use the current draft and only the sources still selected.
  @S-064 @criterion-1 @component @from-ticket
  Scenario: Removing one source narrows the next exchange
    Given "Manuscript", "Methods" and "Replication" are checked
    When I uncheck "Methods" and send my next question
    Then the exchange includes the current manuscript text
    And the selected source IDs contain only the ID of "Replication"

  # assumed — #120 L9, L13 (context); PR [fallback] records the clear-selection rule.
  @S-065 @criterion-1 @component @assumed
  Scenario: Clear a combined selection to return to Web
    Given "Manuscript", "Methods" and "Replication" are checked
    When I activate "Clear selection" in the Context dropdown
    Then only "Web" is checked

  # assumed — #120 L9, L13 (context); PR [fallback] records the last-item rule.
  @S-066 @criterion-1 @component @assumed
  Scenario: Clearing the last item returns to Web
    Given only "Methods" is checked
    When I uncheck "Methods"
    Then only "Web" is checked

  # from ticket — #120 L13, L18: use unsaved edits and the selected sources in one answer.
  @S-067 @criterion-2 @component @from-ticket
  Scenario: A combined send uses the draft as it reads when the writer asks
    Given I selected "Manuscript", "Methods" and "Replication"
    And I changed "12 samples" to "18 samples" in the draft without saving
    When I send "Which studies support my sample count?"
    Then one exchange includes the current editor text containing "18 samples"
    And its selected source IDs are exactly those of "Methods" and "Replication"

  # from ticket — #120 L18, L23: identify supporting sources using selected evidence only.
  @S-068 @criterion-2 @criterion-4 @acceptance @from-ticket
  Scenario: Tell the writer which selected study supports the manuscript claim
    Given my manuscript says the trial enrolled 18 participants
    And "Methods" reports 18 participants and "Replication" reports 24 for the same trial
    And the unselected source "Pilot" also reports 18 participants
    And I selected "Manuscript", "Methods" and "Replication" with "Web" unchecked
    When I ask "Which selected studies support my enrollment figure?"
    Then one answer identifies "Methods" as supporting the draft's figure of 18
    And it explains that "Replication" reports 24 for the same trial
    And no passage from "Pilot" is supplied to the model or used in the answer

  # from ticket — #120 L14, L19: address the quoted passage in the comparison.
  @S-069 @criterion-3 @acceptance @from-ticket
  Scenario: Address the quoted passage when the draft contains two related claims
    Given my draft says "Adults recovered in 8 days" and "Children recovered in 5 days"
    And "Methods" reports that children recovered in 7 days
    And I selected "Manuscript" and "Methods"
    And I quoted "Children recovered in 5 days" from the editor
    When I ask "How does this passage compare with Methods?"
    Then the answer compares the quoted 5 days for children with the 7 days reported by "Methods"
    And it attributes the 5-day figure to the quoted passage

  # assumed — #120 L9 (existing scopes), L23; PR [web] and [fallback] clarify standalone Web.
  @S-070 @criterion-4 @service @assumed
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
      | only Web selected     | no text           | is skipped                  |

  # assumed — #120 L23, L36; PR [review] distinguishes unavailable sources from completed searches without a match.
  @S-072 @criterion-5 @acceptance @assumed
  Scenario Outline: Explain a gap in one selected source while using the other
    Given I selected "Manuscript", "Methods" and "Replication" with "Web" unchecked
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

  # assumed — #120 L23, L36; PR [review] specifies the answer when no selected source supplies evidence.
  @S-073 @criterion-5 @acceptance @assumed
  Scenario: None of the selected sources supplies usable evidence
    Given I selected "Manuscript", "Methods" and "Replication" with "Web" unchecked
    And "Methods" is unavailable and "Replication" has no relevant passage
    And unselected "Pilot" contains a matching passage
    When I ask whether the selected studies support the claim
    Then the answer says the claim could not be verified from the selection
    And it identifies the unavailable source and the source searched without a match
    And it neither labels the claim contradicted nor uses evidence from "Pilot"

  # assumed — #120 L23; brief.md criterion 4 links the existing [retrieval] project boundary.
  @S-077 @criterion-4 @service @assumed
  Scenario: A source from another project is never used
    Given "Manuscript" and "Methods" are checked
    And the request also names a source ID that belongs to another project
    When I ask about sample size
    Then the other project's source is not searched
    And no passage from it is supplied to the model

  # from ticket — #120 L18–19: a study limited to one population is an example of partial support.
  @S-078 @criterion-2 @acceptance @from-ticket
  Scenario: Tell the writer when a selected study qualifies the claim
    Given my manuscript says the treatment works for all adults
    And "Methods" reports the effect only in adults under 40
    And I selected "Manuscript" and "Methods"
    When I ask "Do the selected studies support my claim?"
    Then the answer says "Methods" supports the claim only for adults under 40
    And it does not describe "Methods" as contradicting the claim

  # assumed — #120 L9 (existing scopes); PR [web] and [fallback] document the label and existing API value.
  @S-080 @criterion-1 @criterion-4 @component @assumed
  Scenario: Web-only chat uses the existing API scope
    Given only "Web" is selected
    When I send a question
    Then the Context button displays "Web"
    And the request uses scope "none" with empty manuscript text and null source IDs

  # assumed — #120 L35; PR [bulk] resolves the option and [filter] records its label and behavior under a filter.
  @S-081 @criterion-6 @criterion-7 @component @assumed
  Scenario: Select all indexed sources while filtering by title
    Given "Web" and "Manuscript" are checked
    And only "Methods" matches my title filter
    When I check "All indexed sources" in the Context dropdown
    Then "All indexed sources" is the only checkbox for selecting sources in bulk
    And "Methods", "Replication" and "Pilot" are selected
    And "Manuscript" remains checked

  # assumed — #120 L18, L23, L36; PR [review] requires reporting the gap even when Web is available.
  @S-085 @criterion-5 @acceptance @assumed
  Scenario: General knowledge cannot stand in for missing source evidence
    Given "Web", "Manuscript" and "Methods" are selected
    And "Methods" is searched and returns no relevant passage
    When I ask whether "Methods" verifies my claim
    Then the answer names "Methods" and reports that no relevant passage was found
    And it says the claim could not be verified from the selection
    And any general explanation is distinguished from evidence from "Methods"

  # assumed — #120 L9, L13 (context); PR [fallback] specifies Web after clearing project material.
  @S-087 @criterion-1 @component @assumed
  Scenario: Removing the last project item leaves Web checked
    Given "Web" and "Manuscript" are checked
    When I uncheck "Manuscript"
    Then only "Web" is checked

  # assumed — #120 L9, L13 (context); PR [restore] confirms restoration and [restore-detail] identifies the saved exchange.
  @S-090 @criterion-1 @component @assumed
  Scenario: Reopening a chat restores the selection from its last successful exchange
    Given my last successful exchange used "Web", "Manuscript" and "Methods"
    And I then unchecked "Web" and checked "Replication"
    And my next question failed
    When I reopen that chat from the saved conversations
    Then "Web", "Manuscript" and "Methods" are checked
    And "Replication" is unchecked

  # assumed — #120 L13, L36; PR [restore] and [restore-detail] document restoration of the available choices.
  @S-091 @criterion-1 @component @assumed
  Scenario: Reopening a chat names a source that is no longer available
    Given my last successful exchange used "Web", "Manuscript", "Methods" and "Replication"
    And "Replication" has since been removed from the library
    When I reopen that chat from the saved conversations
    Then the Assistant names "Replication" as unavailable
    And "Web", "Manuscript" and "Methods" remain checked

  # assumed — #120 L35; PR [capacity] sets a context-window limit, and [capacity-detail] requires attempting all sources.
  @S-092 @criterion-7 @service @assumed
  Scenario: Choosing all indexed sources checks every source in a large library
    Given the project has 1,001 indexed sources including "Methods", "Replication" and "Pilot"
    When I choose "All indexed sources" and ask about sample size
    Then the exchange selects all 1,001 sources
    And retrieval attempts to check all 1,001 sources
    And no selected source is silently dropped

  # assumed — #120 L36; PR [cosine], [threshold] and [calibrate] establish the relevance test.
  @S-095 @criterion-5 @service @assumed
  Scenario: A completed search with only below-threshold passages yields no match
    Given I selected "Manuscript" and "Methods"
    And the highest cosine similarity score in "Methods" for my question is below the configured relevance threshold
    When the Assistant completes the search of "Methods" for my question
    Then the model receives "Methods" marked as searched without a match
    And the model receives no passage from "Methods"

  # assumed — #120 L35–36; PR [capacity] and [capacity-detail] distinguish omitted evidence from a failed search.
  @S-096 @criterion-5 @criterion-7 @service @assumed
  Scenario: Report a matching source whose evidence exceeds the available context window
    Given I selected "Manuscript", "Methods" and "Replication"
    And each selected source has one relevant passage
    And the remaining evidence budget fits the passage from "Methods" but the passage from "Replication" exceeds it
    When I ask which selected studies support my claim
    Then both sources are searched
    And the model request stays within budget and includes only the passage from "Methods" as library evidence
    And the answer names "Replication" as a match whose evidence could not fit

  # Open Questions — proposed examples from brief.md, retained with their original IDs.
  # These commented examples can become acceptance scenarios when their proposed details have a recorded decision.

  # assumed — Q2; #120 L13: keyboard interaction.
  # @S-071 @criterion-1 @component
  # Scenario: Add a source to a combined selection with the keyboard
  #   Given "Manuscript" and "Methods" are checked in the open Context dropdown
  #   And keyboard focus is on the unchecked "Replication" item
  #   When I press Space and then Escape
  #   Then the dropdown closes with focus on the Context button
  #   And "Manuscript", "Methods" and "Replication" are checked when I reopen it

  # assumed — Q2; #120 L13, L35: scrolling, title filtering and the collapsed label.
  # @S-074 @criterion-6 @component
  # Scenario: Select sources across searches in a long library
  #   Given the open dropdown has more sources than fit onscreen
  #   And "Manuscript" and "Methods" are checked
  #   When I filter for "Replication", check it, and clear the filter
  #   Then "Methods" and "Replication" are both checked
  #   And "Manuscript", "Web" and "Clear selection" remain visible while I scroll the sources
  #   And the closed button reads "Manuscript + 2 sources"

  # assumed — Q3; #120 L14, L19: quote representation.
  # @S-075 @criterion-3 @service
  # Scenario: The quoted passage travels as its own item
  #   Given I selected "Manuscript" and "Methods"
  #   And I quoted "Children recovered in 5 days" from the editor
  #   When I ask "How does this passage compare with Methods?"
  #   Then the exchange carries the quote "Children recovered in 5 days" exactly as written
  #   And the quote is separate from the question text

  # assumed — Q1; #120 L9, L13: thread continuity across selections.
  # @S-076 @criterion-1 @component
  # Scenario: Changing the context keeps the same conversation
  #   Given I asked a question with only "Manuscript" checked
  #   And I cleared the selection and asked a second question
  #   When I check "Methods" and ask a third question
  #   Then all three exchanges belong to the same conversation

  # assumed — Q5; #120 L36: passing per-source statuses to the model.
  # @S-079 @criterion-5 @service
  # Scenario: Source check results are passed to the model
  #   Given I selected "Manuscript", "Methods" and "Replication"
  #   And "Methods" is unavailable and "Replication" returns no relevant passage
  #   When I ask whether the selected studies support the claim
  #   Then the model receives "Methods" marked unavailable
  #   And the model receives "Replication" marked as searched without a match
  #   And the model receives no passage from "Pilot"

  # assumed — Q4; #120 L35: synchronizing the bulk checkbox.
  # @S-082 @criterion-7 @component
  # Scenario Outline: Keep the all-selected indicator in sync with individual selections
  #   Given "Methods" and "Replication" are checked and "Pilot" is <initial>
  #   When I toggle "Pilot"
  #   Then "All indexed sources" is <result>
  #   And "Methods" and "Replication" remain checked
  #
  #   Examples:
  #     | initial   | result    |
  #     | checked   | unchecked |
  #     | unchecked | checked   |

  # assumed — Q4; #120 L35: empty-library controls.
  # @S-083 @criterion-7 @component
  # Scenario: No indexed sources are available
  #   Given I switch to a project with no indexed sources
  #   When I open the Context dropdown
  #   Then "All indexed sources" is disabled
  #   And "Web" and "Manuscript" remain available

  # assumed — Q1; #120 L9, L13, L23: switching Web off independently.
  # @S-084 @criterion-1 @criterion-4 @acceptance
  # Scenario: Turn off Web while keeping the manuscript and source selected
  #   Given "Web", "Manuscript" and "Methods" are selected
  #   When I uncheck "Web" and ask whether my claim is supported
  #   Then the answer draws only on the manuscript and selected source for its factual findings
  #   And the selection still includes "Manuscript" and "Methods"

  # assumed — Q1; #120 L9, L13: independent Web state.
  # @S-086 @criterion-1 @component
  # Scenario Outline: Selecting Manuscript or a source keeps Web as it was
  #   Given "Web" is <web state> in the Context dropdown
  #   When I check "Manuscript" and "Methods"
  #   Then "Web" is still <web state>
  #   And "Manuscript" and "Methods" are checked
  #
  #   Examples:
  #     | web state |
  #     | checked   |
  #     | unchecked |

  # assumed — Q3; #120 L14, L19: quote payload with Manuscript off.
  # @S-088 @criterion-3 @service
  # Scenario: Quoting without Manuscript shares only the quoted passage
  #   Given "Web" and "Methods" are checked and "Manuscript" is unchecked
  #   And my draft says "Adults recovered in 8 days" and "Children recovered in 5 days"
  #   And I quoted "Children recovered in 5 days" from the editor
  #   When I ask "How does this passage compare with Methods?"
  #   Then the exchange carries the quote "Children recovered in 5 days" exactly as written
  #   And the exchange carries no other manuscript text

  # assumed — Q3; #120 L14, L19: context selections after quoting.
  # @S-089 @criterion-1 @criterion-3 @component
  # Scenario: Quoting leaves the context selection unchanged
  #   Given "Web" and "Methods" are checked and "Manuscript" is unchecked
  #   And I quoted "Children recovered in 5 days" from the editor
  #   When I send my question
  #   Then "Manuscript" is still unchecked
  #   And "Web" and "Methods" are still checked

  # assumed — Q4; #120 L23, L35: timing of later additions to the index.
  # @S-093 @criterion-7 @service
  # Scenario: A source indexed after selecting all sources stays excluded until chosen
  #   Given I chose "All indexed sources"
  #   And a new source "Appendix" finishes indexing afterward
  #   When I ask about sample size
  #   Then "Appendix" is unchecked and is not searched
  #   And "Methods", "Replication" and "Pilot" are still searched
  #   And checking "Appendix" makes it searchable in my next exchange

  # assumed — Q5; #120 L18, L36: sharing the evidence budget across sources.
  # @S-094 @criterion-2 @criterion-5 @service
  # Scenario: A source with many matches does not crowd out another selected source
  #   Given I selected "Manuscript", "Methods" and "Replication" with "Web" unchecked
  #   And "Methods" has many relevant passages
  #   And "Replication" has one relevant passage
  #   And the available context window has room for a relevant passage from each source
  #   When I ask which selected studies support the claim
  #   Then both "Methods" and "Replication" are searched
  #   And the model receives the relevant passage from "Replication"
