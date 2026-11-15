Feature: Ask the assistant a question
  A project member can ask the assistant a question about their manuscript and receive an answer.

  Background:
    Given I am signed in as a member of a project
    And the project has a conversation

  @S-016 @criterion-9
  Scenario: A valid question receives an answer
    Given the manuscript has been saved and indexed
    When I ask a valid question
    Then I receive an answer

  @S-017 @criterion-9
  Scenario: The answer is built from relevant indexed content
    Given the indexed manuscript contains a passage relevant to my question
    When I ask a question about that passage
    Then the answer is produced using the relevant passages retrieved from the indexed manuscript

  @S-025 @criterion-9
  Scenario: The complete answer arrives at once
    Given the manuscript has been saved and indexed
    When I ask a valid question
    Then I receive the complete answer in one piece
    And no part of the answer is delivered before the rest is ready

  @S-018 @edge @criterion-10
  Scenario Outline: An invalid question is rejected
    When I ask <question>
    Then the request is rejected with validation details

    Examples:
      | question                               |
      | an empty question                      |
      | a question made only of spaces         |
      | a question longer than 4000 characters |

  @S-019 @edge @criterion-7
  Scenario: Asking in an unknown conversation
    When I ask a valid question in a conversation that does not exist
    Then the request is rejected as not found

  @S-020 @edge @criterion-11
  Scenario: Asking while a previous answer is pending
    Given my previous question in the conversation is still being answered
    When I ask another valid question
    Then the request is rejected as a conflict

  @S-021 @edge @criterion-12
  Scenario: The AI provider is busy
    Given the AI provider is busy
    When I ask a valid question
    Then I am told the assistant is busy
    And I am told when to retry

  @S-022 @edge @criterion-12
  Scenario: The AI provider fails
    Given the AI provider returns an error
    When I ask a valid question
    Then I am told the assistant could not produce an answer because of a provider error

  @S-023 @edge @criterion-12
  Scenario: The assistant is not configured
    Given the assistant has not been configured
    When I ask a valid question
    Then I am told the assistant is not available because it is not configured

  @S-024 @edge @criterion-7
  Scenario: Asking without a session
    Given I am not signed in
    When I ask a valid question
    Then the request is rejected as unauthorized
