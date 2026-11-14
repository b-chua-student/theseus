@THES-1
Feature: Session inspection and protection
  Users identify their current account through a protected session.

  @S-007 @S07 @criterion-3
  Scenario: Inspect the current account
    Given a valid session for an existing account
    When the user inspects their current account
    Then status 200 and that account's id, display name and email are returned
    And application data remains unchanged

  @S-017 @S17 @criterion-8
  Scenario Outline: Set session-cookie safeguards
    Given correct credentials in <environment> with the local HTTP override <override>
    When the user signs in
    Then the session cookie has SameSite Lax and HttpOnly enabled
    And Secure is <secure>
    Examples:
      | environment | override | secure   |
      | production  | disabled | enabled  |
      | local HTTP  | enabled  | disabled |

  @S-020 @S20 @criterion-3
  Scenario: Reading information preserves application data
    Given an authorized user and existing application data
    When the user reads available application information
    Then application data remains unchanged

  @S-008 @S08 @criterion-3 @edge
  Scenario: Reject inspection without a session
    Given no session
    When the user inspects their current account
    Then status 401 and error Unauthorized are returned
