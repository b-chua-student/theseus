@THES-1
Feature: Consistent error feedback
  Users receive predictable failure information for unsuccessful operations.

  @S-016 @S16 @criterion-7 @edge
  Scenario Outline: Present consistent failure information
    Given an operation that will fail with status <status>
    When the user attempts that operation
    Then status <status> and a string error are returned
    And a domain error includes a string UPPER_SNAKE code
    And a generic framework error omits the code
    Examples:
      | status |
      | 400    |
      | 401    |
      | 404    |
      | 409    |
      | 415    |
      | 422    |
      | 429    |
      | 503    |

  @S-018 @S18 @criterion-8 @edge
  Scenario: Reject a non-JSON state-changing request body
    Given an otherwise authorized state-changing operation with a nonempty non-JSON body
    When the user submits that operation
    Then status 415 and a string error are returned
    And application data remains unchanged
