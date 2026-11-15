Feature: Conversation creation
  A project member can start a conversation within a project to ask the assistant questions.

  Background:
    Given a project

  @S-012 @criterion-8
  Scenario: A member starts a conversation
    Given I am signed in as a member of the project
    When I start a conversation
    Then I receive the id of the new conversation

  @S-013 @edge @criterion-7
  Scenario: A non-member cannot start a conversation
    Given I am signed in but not a member of the project
    When I start a conversation
    Then the request is rejected as not found

  @S-014 @edge @criterion-7
  Scenario: Starting a conversation in an unknown project
    Given I am signed in
    When I start a conversation in a project that does not exist
    Then the request is rejected as not found

  @S-015 @edge @criterion-7
  Scenario: Starting a conversation without a session
    Given I am not signed in
    When I start a conversation
    Then the request is rejected as unauthorized
