Feature: Ask the assistant a question
  A project member can ask the assistant a question about their manuscript and receive an answer.

  @S-016 @criterion-9
  Scenario: A valid question receives an answer
    Given I am signed in as a member of a project with a valid conversation
    And the manuscript has been saved and indexed
    And the assistant is available
    When I ask a valid question
    Then the response has status 201 and contains an answer

  @S-017 @criterion-9
  Scenario: The answer is built from relevant indexed content
    Given I am signed in as a member of a project with a valid conversation
    And the indexed manuscript contains a passage relevant to my question
    And the assistant is available
    When I ask a question about that passage
    Then the answer is produced using relevant indexed passages as context for Gemini

  @S-025 @criterion-9
  Scenario: The complete answer arrives at once
    Given I am signed in as a member of a project with a valid conversation
    And the manuscript has been saved and indexed
    And the assistant is available
    When I ask a valid question
    Then I receive the complete answer in one response
    And no partial answer is sent before completion

  @S-018 @edge @criterion-10
  Scenario Outline: An invalid question is rejected
    Given I am signed in as a member of a project with a valid conversation
    When I ask <question>
    Then the request is rejected with status 400 and validation details

    Examples:
      | question                               |
      | an empty question                      |
      | a question made only of spaces         |
      | a question longer than 4000 characters |

  @S-019 @edge @criterion-7
  Scenario: Asking in an unknown conversation
    Given I am signed in as a member of a project
    When I ask a valid question in a conversation that does not exist
    Then the request is rejected with status 404

  @S-020 @edge @criterion-11
  Scenario: Asking while a previous answer is pending
    Given I am signed in as a member of a project with a valid conversation
    And my previous question in the conversation is still being answered
    When I ask another valid question
    Then the request is rejected with status 409

  @S-021 @edge @criterion-12
  Scenario: The AI provider is busy
    Given I am signed in as a member of a project with a valid conversation
    And the AI provider is busy
    When I ask a valid question
    Then the request is rejected with status 429
    And the response includes a Retry-After indication

  @S-022 @edge @criterion-12
  Scenario: The AI provider fails
    Given I am signed in as a member of a project with a valid conversation
    And the AI provider returns an error
    When I ask a valid question
    Then the request is rejected with status 502

  @S-023 @edge @criterion-12
  Scenario: The Gemini API key is missing
    Given I am signed in as a member of a project with a valid conversation
    And the Gemini API key is not configured
    When I ask a valid question
    Then the request is rejected with status 503

  @S-024 @edge @criterion-7
  Scenario: Asking without a session
    Given I am not signed in
    And a project has a conversation
    When I ask a valid question in that conversation
    Then the request is rejected with status 401

  @S-026 @edge @criterion-7
  Scenario: Asking in an unknown project
    Given I am signed in
    When I ask a valid question in a project that does not exist
    Then the request is rejected as not found

  @S-027 @edge @criterion-10
  Scenario Outline: A question at the length limits is accepted
    Given I am signed in as a member of a project with a valid conversation
    And the manuscript has been saved and indexed
    And the assistant is available
    When I ask a non-blank question of <length> characters
    Then the response has status 201 and contains an answer

    Examples:
      | length |
      | 1      |
      | 4000   |
