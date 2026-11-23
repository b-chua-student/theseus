Feature: Choose the Assistant's reference material from one dropdown
  A writer can ask about the manuscript, one library source, both together, or neither.

  Background:
    Given I am in the manuscript editor with the Assistant chat composer open

  @S-033 @criterion-1 @component
  Scenario: Manuscript and individual sources are available in the same menu
    Given the current project's indexed sources are "Source 1" and "Source 2" in library order
    And the project has an unindexed source "Pending" and another project has an indexed source "Other"
    When I open the composer's only context control, the "Context" dropdown
    Then I see exactly these selectable items in order:
      | item       |
      | Manuscript |
      | Source 1   |
      | Source 2   |
      | None       |
    And the composer has no separate context buttons or source picker

  @S-034 @criterion-1 @component
  Scenario: The writer can still choose a context when the library has no searchable sources
    Given the current project has no indexed sources and the editor is ready
    When I open the "Context" dropdown
    Then the only items are "Manuscript" and "None"

  @S-035 @criterion-2 @component
  Scenario Outline: Each toggle updates the selection immediately and keeps the menu open
    Given the open dropdown has indexed sources "Source 1" and "Source 2"
    And the button displays "<before>"
    When I activate "<item>"
    Then the dropdown stays open with exactly <checked> checked
    And the button displays "<after>"

    Examples:
      | before                | item       | checked                     | after                 |
      | None                  | Manuscript | "Manuscript"                | Manuscript            |
      | None                  | Source 1   | "Source 1"                  | Source 1              |
      | Manuscript            | Source 1   | "Manuscript" and "Source 1" | Manuscript + Source 1 |
      | Source 1              | Manuscript | "Manuscript" and "Source 1" | Manuscript + Source 1 |
      | Source 1              | Source 2   | "Source 2"                  | Source 2              |
      | Manuscript + Source 1 | Source 2   | "Manuscript" and "Source 2" | Manuscript + Source 2 |
      | Manuscript + Source 1 | Manuscript | "Source 1"                  | Source 1              |
      | Manuscript + Source 1 | Source 1   | "Manuscript"                | Manuscript            |
      | Manuscript + Source 1 | None       | "None"                      | None                  |
      | Manuscript            | Manuscript | "None"                      | None                  |
      | Source 1              | Source 1   | "None"                      | None                  |

  @S-036 @criterion-2 @component
  Scenario: Add a source to the manuscript using the keyboard
    Given "Manuscript" is selected and the "Context" button has keyboard focus
    And "Source 1" is the first source in the menu
    When I press Enter, Arrow Down, Enter, and Escape
    Then the dropdown closes with focus on the "Context" button
    And the button displays "Manuscript + Source 1"

  @S-057 @criterion-2 @component
  Scenario: Add a source to the manuscript using the Space key
    Given "Manuscript" is selected and the open "Context" dropdown has focus on "Source 1"
    When I press Space
    Then the dropdown stays open with "Manuscript" and "Source 1" checked
    And the button displays "Manuscript + Source 1"

  @S-058 @criterion-2 @component
  Scenario: Activating None while it is checked changes nothing
    Given the open "Context" dropdown has only "None" checked
    When I activate "None"
    Then only "None" is checked
    And the button displays "None"

  @S-037 @criterion-2 @component
  Scenario: Moving focus to None and dismissing the menu keeps the selection
    Given "Source 1" is selected in the open "Context" dropdown
    And I have moved keyboard focus to "None"
    When I press Escape
    Then the dropdown closes with focus on the "Context" button
    And the button still displays "Source 1"

  @S-038 @criterion-3 @component
  Scenario: Deselecting the source keeps Manuscript with the latest unsaved text
    Given I deselected "Source 1" with "Manuscript" still checked
    And I changed "12 samples" to "18 samples" in the editor without saving
    When I send "How many samples did I record?"
    Then the request uses scope "manuscript" with the current editor text containing "18 samples"
    And the request has null source IDs

  @S-039 @criterion-4 @component
  Scenario: Choosing the only source still identifies that source explicitly
    Given "Methods" with ID "3f2b8c1e-5a47-4d6e-9b10-7c2a4e8d1f01" is the project's only indexed source
    And only "Methods" is checked
    When I send a question
    Then the request uses scope "source_library" with exactly the source ID "3f2b8c1e-5a47-4d6e-9b10-7c2a4e8d1f01"
    And the request has empty manuscript text

  @S-040 @criterion-4 @component
  Scenario: Changing sources replaces the source used for the next question
    Given I sent a question with "Source 1" selected
    And I have since selected "Source 2" with ID "9a1d7e34-2c58-4b0f-8e6a-1d5f3b7c9a22"
    When I send my next question
    Then the request uses scope "source_library" with exactly the source ID "9a1d7e34-2c58-4b0f-8e6a-1d5f3b7c9a22"
    And the request has empty manuscript text

  @S-041 @criterion-4 @service
  Scenario: Search stays within the chosen source when two sources match
    Given "Source 1" and "Source 2" are indexed in the current project
    And both contain a passage that matches the question
    When the Assistant receives the question with scope "source_library" and only the ID of "Source 2"
    Then every retrieved passage is from "Source 2"
    And the model receives a matching passage from "Source 2"

  @S-042 @criterion-5 @component
  Scenario Outline: A writer can clear project context for the next message
    Given I sent a question with "<previous>" selected
    And I have since chosen "None"
    When I send a follow-up question
    Then the request uses scope "none" with empty manuscript text and null source IDs

    Examples:
      | previous              |
      | Manuscript            |
      | Source 1              |
      | Manuscript + Source 1 |

  @S-043 @criterion-3 @criterion-5 @service
  Scenario Outline: Sending without a source skips library retrieval
    Given the project has an indexed source with a passage that matches the question
    When the Assistant receives the question with scope "<scope>" and manuscript text "<text>"
    Then the Assistant performs no library retrieval for that message

    Examples:
      | scope      | text                      |
      | manuscript | The trial had 18 samples. |
      | none       |                           |

  @S-044 @criterion-6 @component
  Scenario Outline: A new conversation starts on the right choice
    Given I open a new conversation and the editor <editor state>
    Then the "Context" button displays "<initial>"

    Examples:
      | editor state     | initial    |
      | is ready         | Manuscript |
      | is not yet ready | None       |

  @S-045 @criterion-6 @component
  Scenario Outline: Reopening a saved conversation restores the available selections
    Given a saved conversation with stored scope "<scope>" and <stored source>
    And the editor and project source list have finished loading
    When I open that conversation
    Then the "Context" button displays "<label>"

    Examples:
      | scope                 | stored source                          | label                 |
      | source_library        | the ID of indexed source "Source 1"    | Source 1              |
      | source_library        | the ID of a source that is not indexed | None                  |
      | source_library        | null source IDs for all sources        | None                  |
      | source_library        | an empty list of source IDs            | None                  |
      | source_library        | IDs for two indexed sources            | None                  |
      | manuscript            | no source IDs                          | Manuscript            |
      | none                  | no source IDs                          | None                  |
      | manuscript_and_source | the ID of indexed source "Source 1"    | Manuscript + Source 1 |
      | manuscript_and_source | the ID of a source that is not indexed | Manuscript            |
      | manuscript_and_source | null source IDs                        | Manuscript            |
      | manuscript_and_source | an empty list of source IDs            | Manuscript            |
      | manuscript_and_source | IDs for two indexed sources            | Manuscript            |

  @S-046 @criterion-7 @component
  Scenario Outline: A failed send keeps the reference selection available for retry
    Given the "Context" button displays "<selection>"
    When sending my question fails
    Then the question stays in the thread with a "Try again" action
    And the button still displays "<selection>"

    Examples:
      | selection             |
      | Source 2              |
      | Manuscript + Source 2 |

  @S-047 @criterion-3 @component
  Scenario Outline: A manuscript over the limit is not sent
    Given the "Context" button displays "<selection>" and the editor holds more than 500000 characters
    When I type "Summarise this" and send it
    Then no request is made
    And the composer tells me the manuscript is too long
    And "Summarise this" is still in the composer

    Examples:
      | selection             |
      | Manuscript            |
      | Manuscript + Source 1 |

  @S-048 @criterion-2 @component
  Scenario Outline: Opening the menu focuses the first checked item
    Given the "Context" button displays "<selection>"
    When I open the "Context" dropdown
    Then keyboard focus is on "<item>"

    Examples:
      | selection             | item       |
      | None                  | None       |
      | Source 1              | Source 1   |
      | Manuscript + Source 1 | Manuscript |

  @S-049 @criterion-6 @component
  Scenario: The control is disabled while a message is in flight
    Given I have sent a question and the answer has not arrived
    Then the "Context" button is disabled

  @S-050 @criterion-6 @component
  Scenario: Changing the choice keeps the same conversation
    Given I have an earlier exchange in the conversation
    When I change the "Context" selection to "None"
    Then no new conversation is started
    And the earlier exchange is still visible

  @S-051 @criterion-1 @service
  Scenario: The source list marks which sources are indexed
    Given the project has an indexed source "Source 1" and an unindexed source "Pending"
    When the client requests the project's sources
    Then "Source 1" has "indexed" true and "Pending" has "indexed" false

  @S-052 @criterion-8 @component
  Scenario: A comparison sends the latest manuscript and the selected source in one exchange
    Given "Manuscript" and "Source 1" are checked
    And I replace "12 samples" with "18 samples" in the manuscript without saving
    When I ask "Does my sample count match the study?"
    Then one exchange request uses scope "manuscript_and_source"
    And its manuscript text equals the current editor text containing "18 samples"
    And its source IDs contain exactly the UUID of "Source 1"

  @S-053 @criterion-8 @service
  Scenario: The model can compare a manuscript claim with evidence from the chosen study
    Given the manuscript text says "We analysed 18 samples"
    And indexed study "Methods" reports "We analysed 24 samples"
    And another indexed study "Pilot" reports "We analysed 12 samples"
    When the Assistant receives "Does my count match Methods?" with both the manuscript and the ID of "Methods"
    Then retrieval searches only "Methods"
    And the same model call receives the manuscript claim and the "24 samples" passage from "Methods"
    And the model receives no passages from "Pilot"

  @S-054 @criterion-2 @component
  Scenario: Closing the menu with its button preserves the selected items
    Given the open dropdown has "Manuscript" and "Methods" checked
    When I activate the "Context" button
    Then the dropdown closes and its button displays "Manuscript + Methods"
    And only "Manuscript" and "Methods" are checked when I reopen the dropdown

  @S-055 @criterion-6 @component
  Scenario: The manuscript is unavailable while the editor is loading
    Given a new conversation is open and the manuscript editor is still loading
    When I open the "Context" dropdown
    Then "None" is checked and "Manuscript" is disabled

  @S-056 @criterion-8 @service
  Scenario Outline: A combined request must identify exactly one source
    Given the exchange request includes scope "manuscript_and_source" and current manuscript text
    When the Assistant receives that request with <source IDs>
    Then the exchange is rejected as invalid
    And neither library retrieval nor a model call runs

    Examples:
      | source IDs                   |
      | null source IDs              |
      | an empty list of source IDs  |
      | two distinct source UUIDs    |

  @S-059 @criterion-6 @service
  Scenario: A saved conversation keeps the combined scope and its source
    Given a conversation is saved with scope "manuscript_and_source" and the ID of indexed source "Source 1"
    When the conversation is loaded
    Then its stored scope is "manuscript_and_source"
    And its stored source IDs contain exactly the UUID of "Source 1"

  @S-060 @criterion-6 @service
  Scenario Outline: The existing scopes are still accepted
    Given the exchange request includes scope "<scope>" with a valid manuscript text and source IDs for that scope
    When the Assistant receives the request
    Then the exchange is accepted as valid

    Examples:
      | scope          |
      | none           |
      | manuscript     |
      | source_library |

  @S-061 @criterion-3 @component
  Scenario Outline: A long manuscript does not block a send that excludes it
    Given the "Context" button displays "<selection>" and the editor holds more than 500000 characters
    When I type "Summarise this" and send it
    Then the request uses scope "<scope>" with empty manuscript text
    And the composer shows no manuscript length warning

    Examples:
      | selection | scope          |
      | Source 1  | source_library |
      | None      | none           |

  @S-062 @criterion-3 @component
  Scenario: A manuscript of exactly 500000 characters is sent
    Given the "Context" button displays "Manuscript" and the editor holds exactly 500000 characters
    When I type "Summarise this" and send it
    Then the request uses scope "manuscript" with the current editor text
    And the composer shows no manuscript length warning
