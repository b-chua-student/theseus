Feature: Project Member Management

  Background:
    Given a signed-in user "Alice" owns project "Theseus"
    And "Bob" is a member of project "Theseus" with role "viewer"

  @S-001 @criterion-1
  Scenario: Project owner views current project members
    When "Alice" requests the member list for project "Theseus"
    Then the response status is 200
    And the member list includes "Bob" with role "viewer"

  @S-002 @criterion-2
  Scenario: Project owner updates a member role to editor
    When "Alice" updates the role of "Bob" in project "Theseus" to "editor"
    Then the response status is 204
    And "Bob" has role "editor" in project "Theseus"

  @S-003 @criterion-3
  Scenario: Project owner removes a member from the project
    When "Alice" removes "Bob" from project "Theseus"
    Then the response status is 204
    And "Bob" is no longer a member of project "Theseus"

  @S-004 @criterion-2
  Scenario: Non-owner cannot change a member role
    Given "Bob" is signed in
    When "Bob" updates the role of "Bob" in project "Theseus" to "editor"
    Then the response status is 403

  @S-005 @criterion-2
  Scenario: Owner cannot assign an invalid project role
    When "Alice" updates the role of "Bob" in project "Theseus" to "admin"
    Then the response status is 400

  @S-006 @criterion-3
  Scenario: Owner cannot remove a user who is not a project member
    When "Alice" removes an unknown member from project "Theseus"
    Then the response status is 404
