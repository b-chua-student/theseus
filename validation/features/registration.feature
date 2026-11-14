@THES-1
Feature: Account registration
  New users create an account and are signed in automatically.

  @S-001 @S01 @criterion-1
  Scenario: Register successfully
    Given valid registration details with an unused email
    When the user registers
    Then one account is created with status 201 and its id and display name are returned
    And the user is signed in to that account

  @S-028 @criterion-10
  Scenario: Protect the registered password
    Given valid registration details with an unused email
    When the user registers
    Then the stored password satisfies the approved one-way hashing policy
    And the plaintext password is not persisted

  @S-002 @S02 @criterion-1 @edge
  Scenario: Reject an existing email
    Given valid registration details using the exact email of an existing account
    When the user registers
    Then registration fails with status 409
    And no account is created

  @S-004 @S04 @criterion-1 @edge
  Scenario Outline: Reject registration fields outside their length bounds
    Given otherwise valid registration details with a <field> of <length> characters
    When the user registers
    Then registration fails with status 400
    And no account is created
    Examples:
      | field        | length |
      | display name | 0      |
      | display name | 129    |
      | email        | 0      |
      | email        | 129    |
      | password     | 0      |
      | password     | 129    |
