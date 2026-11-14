@THES-1
Feature: Display-name updates
  Account holders keep their displayed identity current.

  @S-029 @criterion-5
  Scenario: Save a preferred display name
    Given an authenticated account holder and a valid new display name
    When the user updates their display name
    Then the name is persisted for their account
    And subsequent account inspection shows the new name

  @S-019 @S19 @criterion-8
  Scenario: Update without a CSRF token
    Given an authenticated account holder and a valid JSON display-name update without a CSRF token
    When the user updates their display name
    Then the new display name is saved successfully

  @S-011 @S11 @criterion-5 @edge
  Scenario Outline: Accept display-name length boundaries
    Given an authenticated account holder and a new display name of <length> characters
    When the user updates their display name
    Then the name is persisted and shown on subsequent account inspection
    Examples:
      | length |
      | 1      |
      | 128    |

  @S-012 @S12 @criterion-5 @edge
  Scenario: Reject an update without authentication
    Given no session and a valid new display name
    When the user attempts to update their display name
    Then status 401 is returned and no account is changed
