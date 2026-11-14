@THES-1
Feature: Account deletion
  Account holders without owned projects can remove their account.

  @S-021 @S21 @criterion-9
  Scenario: Delete an eligible account
    Given an authenticated account holder with memberships and no owned projects
    When the user deletes their account
    Then status 204 is returned
    And the account and its memberships are removed
    And the session cookie is cleared

  @S-022 @S22 @criterion-9 @edge
  Scenario: Reject deletion without authentication
    Given no session
    When the user attempts account deletion
    Then status 401 is returned
    And no account or membership is deleted
