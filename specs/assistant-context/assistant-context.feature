Feature: Choose the Assistant context for a message
  A writer chooses which project material the Assistant may consult for the next question.

  Terms: "Sources" is the UI label and `source_library` is the API scope value.
  An eligible source is a source in the current project whose document is indexed.
  Scenarios tagged @service are checked against the chat service and exchange endpoint with
  fake adapters. The others are checked in the editor UI.

  Background:
    Given I am in the manuscript editor with the Assistant composer open

  @S-001 @criterion-1
  Scenario: A new conversation has one compact context selector
    Given I have started a new conversation
    Then the "Context" button displays "Sources"
    And it is the only context selector visible in the composer when the menu is closed
    And no separate "Manuscript" or "Source Library" context control is visible

  @S-002 @criterion-1
  Scenario: The menu exposes exactly three mutually exclusive contexts
    Given I have started a new conversation
    When I open the "Context" menu
    Then the menu contains exactly these radio items in order:
      | item       | checked |
      | Manuscript | no      |
      | Sources    | yes     |
      | None       | no      |

  @S-003 @criterion-2
  Scenario Outline: Choosing a radio item updates the collapsed button
    Given "<previous>" is selected in the "Context" menu
    When I select "<choice>" from that menu
    Then the menu closes
    And the "Context" button displays "<choice>"
    And "<choice>" is the only checked item when I reopen the menu

    Examples:
      | previous   | choice     |
      | Sources    | Manuscript |
      | Manuscript | None       |
      | None       | Sources    |
      | Sources    | Sources    |

  @S-004 @criterion-2
  Scenario: Choose a context using the keyboard
    Given the "Context" button has keyboard focus and displays "Sources"
    When I press Enter
    Then the menu opens with focus on "Sources"
    When I press Arrow Down and Enter
    Then the menu closes with focus on the "Context" button
    And the button displays "None"

  @S-005 @criterion-2
  Scenario: Dismiss the menu without committing a choice
    Given "Sources" is checked in the open "Context" menu
    When I move focus to "None" with Arrow Down and press Escape
    Then the menu closes with focus on the "Context" button
    And the button still displays "Sources"

  @S-006 @criterion-2
  Scenario: Move up through the menu with the keyboard
    Given the "Context" menu is open with focus on "Sources"
    When I press Arrow Up and Enter
    Then the menu closes with focus on the "Context" button
    And the button displays "Manuscript"

  @S-007 @criterion-3
  Scenario: Manuscript uses unsaved editor text
    Given "Manuscript" is selected
    And I have changed a manuscript sentence from "12 samples" to "18 samples" without saving
    When I send "How many samples did I record?"
    Then the request uses scope "manuscript" with the current editor text containing "18 samples"
    And the request omits source IDs

  @S-008 @criterion-3
  Scenario: Manuscript text is read when the message is sent
    Given "Manuscript" is selected
    And I have typed a question
    When I edit the manuscript again after choosing "Manuscript" and then send the question
    Then the request contains the editor text as it is at the moment of sending

  @S-009 @criterion-3 @service
  Scenario: Manuscript mode runs no library retrieval
    Given the conversation has eligible project sources
    When a message is received with scope "manuscript" and manuscript text
    Then no library retrieval runs for this message
    And the model receives the manuscript text as reference material

  @S-010 @criterion-3
  Scenario: A manuscript over the size limit is not sent
    Given "Manuscript" is selected
    And the editor text is longer than 500000 characters
    When I try to send a question
    Then no request is sent
    And I am told the manuscript is too long for the Assistant
    And my question remains in the composer

  @S-011 @criterion-4
  Scenario: Sources picker lists only eligible entries
    Given the current project has indexed entries "A", "B" and "C"
    And it has an entry "D" that is not yet indexed
    And another project has an indexed entry "E"
    When I open the source picker in Sources mode
    Then the picker lists exactly "A", "B" and "C"
    And all three are checked

  @S-012 @criterion-4
  Scenario: Sources searches only the selected project entries
    Given "Sources" is selected and the eligible project library entries are "A", "B", and "C"
    And I open the source picker and uncheck "B"
    When I send a question
    Then the request uses scope "source_library" with only the IDs of "A" and "C"
    And the request omits manuscript text

  @S-013 @criterion-4 @service
  Scenario: Retrieval is limited to the chosen eligible sources
    Given the project has eligible sources "A", "B" and "C"
    When a message is received with scope "source_library" and source IDs for "A" and "C"
    Then retrieval returns passages only from "A" and "C"

  @S-014 @criterion-4
  Scenario Outline: All sources and a cleared selection have distinct meanings
    Given "Sources" is selected and the project has eligible library entries
    And <picker_state>
    When I send a question
    Then the request uses scope "source_library" with <source_ids>
    And the request omits manuscript text

    Examples:
      | picker_state                                  | source_ids             |
      | I have not changed the picker                 | the source IDs omitted |
      | I have unchecked every entry                  | an empty source list   |
      | I unchecked "B" and then checked it again     | the source IDs omitted |

  @S-015 @criterion-4 @service
  Scenario Outline: The service honors the source ID meanings
    Given the project has eligible sources "A", "B" and "C"
    When a message is received with scope "source_library" and <source_ids>
    Then retrieval uses <eligible_sources>

    Examples:
      | source_ids             | eligible_sources                          |
      | the source IDs omitted | all eligible sources in this project only |
      | an empty source list   | no sources                                |

  @S-016 @criterion-4 @service
  Scenario: Sources outside the project or not indexed are never retrieved
    Given the project has eligible source "A" and an unindexed source "D"
    And another project has an indexed source "E"
    When a message is received with scope "source_library" and source IDs for "A", "D" and "E"
    Then retrieval uses only "A"

  @S-017 @criterion-4
  Scenario: A project with no searchable sources
    Given the current project has no indexed sources
    And "Sources" is selected
    When I open the source picker
    Then the picker says there are no searchable sources
    When I send a question
    Then the request uses scope "source_library" with the source IDs omitted
    And the Assistant answers without library material

  @S-018 @criterion-4
  Scenario: The source selection is kept when switching modes
    Given "Sources" is selected and I have unchecked "B"
    When I switch to "None" and then back to "Sources"
    Then "B" is still unchecked in the picker

  @S-019 @criterion-5 @service
  Scenario Outline: Prior exchanges remain available in every mode
    Given this conversation has a previous exchange with its question and answer
    When a follow-up message is received with scope "<scope>"
    Then the model receives the previous exchange as conversation history

    Examples:
      | scope          |
      | manuscript     |
      | source_library |
      | none           |

  @S-020 @criterion-5
  Scenario: None sends no project material
    Given this conversation has a previous exchange with its question and answer
    And "None" is selected
    When I send a follow-up question
    Then the request uses scope "none" and omits manuscript text and source IDs

  @S-021 @criterion-5 @service
  Scenario: None runs no library retrieval
    Given the project has eligible sources
    When a message is received with scope "none"
    Then no library retrieval runs for this message
    And the model receives no manuscript text and no retrieved passages

  @S-022 @criterion-6
  Scenario Outline: A switch applies to the next send in the same conversation
    Given I have already sent a message using "<previous>"
    And I have switched the context to "<current>"
    When I send another message in the same conversation
    Then the new request uses scope "<scope>"
    And it omits <inactive_input>
    And the earlier question and answer remain unchanged

    Examples:
      | previous   | current    | scope          | inactive_input                 |
      | Sources    | Manuscript | manuscript     | source IDs                     |
      | Manuscript | Sources    | source_library | manuscript text                |
      | Sources    | None       | none           | source IDs and manuscript text |
      | Manuscript | None       | none           | source IDs and manuscript text |
      | None       | Manuscript | manuscript     | source IDs                     |
      | None       | Sources    | source_library | manuscript text                |

  @S-023 @criterion-6
  Scenario: Only the final choice applies after several switches
    Given a conversation is open with "Sources" selected
    When I switch to "Manuscript", then "None", then "Sources" and send a question
    Then the request uses scope "source_library" and omits manuscript text

  @S-024 @criterion-7
  Scenario: A failed send keeps the writer's choices
    Given "Sources" is selected and I have unchecked "B"
    And I have typed a question
    When the send fails
    Then the "Context" button still displays "Sources"
    And "B" is still unchecked
    And my question remains in the composer

  @S-025 @criterion-7
  Scenario: Reopening a conversation restores its context
    Given a conversation whose last answered message used scope "manuscript"
    When I reopen that conversation
    Then the "Context" button displays "Manuscript"

  @S-026 @criterion-7
  Scenario: Reopening a conversation restores its source selection
    Given a conversation whose last answered message used scope "source_library" with source IDs for "A" and "C"
    When I reopen that conversation
    Then the "Context" button displays "Sources"
    And only "A" and "C" are checked in the picker
