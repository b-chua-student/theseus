@THES-1
Feature: Account sign-in
  Returning users authenticate without revealing whether an email is registered.

  @S-005 @S05 @criterion-2
  Scenario: Sign in successfully
    Given an existing account and its correct credentials
    When the user signs in
    Then status 200 and that account's id and display name are returned
    And the user is signed in to that account

  @S-006 @S06 @criterion-2 @edge
  Scenario Outline: Reject invalid credentials without revealing account existence
    Given <credentials>
    When the user signs in
    Then status 401 and the same generic invalid-credentials error are returned
    And the user is not authenticated
    Examples:
      | credentials                               |
      | a registered email and incorrect password |
      | an unregistered email and valid-length password |

  @S-027 @criterion-2 @edge
  Scenario Outline: Reject sign-in fields outside their length bounds
    Given otherwise valid credentials with a <field> of <length> characters
    When the user signs in
    Then sign-in fails with status 400
    And the user is not authenticated
    Examples:
      | field    | length |
      | email    | 0      |
      | email    | 129    |
      | password | 0      |
      | password | 129    |

  @S-014 @S14 @criterion-6 @edge
  Scenario Outline: Throttle excess authentication requests
    Given an IP has exhausted the five-request allowance for <operation> within a minute
    When another <operation> attempt is made from that IP before the allowance resets
    Then status 429 and a Retry-After value are returned
    Examples:
      | operation    |
      | registration |
      | sign-in      |
