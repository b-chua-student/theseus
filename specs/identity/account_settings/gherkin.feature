Feature: Manage my account settings
  A signed-in Theseus user can view their account details and update their display name.

  @S-001 @criterion-1
  Scenario: View my current account details
    Given I am signed in with display name "Maria Cruz" and email address "maria@example.com"
    When I open my account settings
    Then I see the display name "Maria Cruz" and email address "maria@example.com"

  @S-002 @criterion-2
  Scenario: A saved display name is visible on a later visit
    Given I am signed in with the display name "Maria Cruz"
    When I save "Maria L. Cruz" as my display name in account settings
    Then I see "Maria L. Cruz" as my display name when I reopen account settings

  @S-003 @criterion-3 @edge
  Scenario: Another user's settings are private
    Given I am signed in to my own account
    And another user has an account
    When I try to view the other user's account settings
    Then their account details are withheld from me

  @S-004 @criterion-3 @edge
  Scenario: Another user's display name is protected
    Given I am signed in to my own account
    And another user has the display name "Alex Reyes"
    When I try to change that user's display name to "Another Name"
    Then the other user's display name remains "Alex Reyes"

  @S-005 @criterion-1 @edge
  Scenario: Account details are private when signed out
    Given I am signed out
    When I try to open account settings
    Then I see no account details
