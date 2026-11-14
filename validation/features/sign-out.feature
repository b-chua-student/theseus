@THES-1
Feature: Account sign-out
  Users end their current browser session safely.

  @S-009 @S09 @criterion-4
  Scenario: Sign out of an active session
    Given an authenticated user
    When the user signs out
    Then status 204 is returned and the session cookie is cleared
    And the browser is no longer authenticated

  @S-010 @S10 @criterion-4 @edge
  Scenario: Sign out without an active session
    Given no session
    When the user signs out
    Then sign-out succeeds safely without creating a session
