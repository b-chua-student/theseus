Feature: Project Member Management

  Background:
    Given a signed-in user "Alice" has role "owner" on project "Theseus"
    And "Bob" is a member of project "Theseus" with role "editor"

  @S-001 @criterion-1
  Scenario: Project owner views current project members
    Given "Alice" is signed in
    When "Alice" requests the member list for project "Theseus"
    Then the response status is 200
    And the member list includes "Bob" with role "editor"

  @S-002 @criterion-1
  Scenario: Existing project member views current project members
    Given "Bob" is signed in
    When "Bob" requests the member list for project "Theseus"
    Then the response status is 200
    And the member list includes "Bob" with role "editor"

  @S-003 @criterion-2
  Scenario: Project owner updates a member's role
    Given "Alice" is signed in
    When "Alice" updates "Bob"'s role on project "Theseus" to "viewer"
    Then the response status is 204
    And "Bob"'s role on project "Theseus" is "viewer"

  @S-004 @criterion-2
  Scenario: Project owner removes a member from the project
    Given "Alice" is signed in
    When "Alice" removes "Bob" from project "Theseus"
    Then the response status is 204
    And "Bob" is no longer a member of project "Theseus"

  @S-005 @criterion-3
  Scenario: Non-owner cannot change member roles or remove members
    Given "Carol" is a member of project "Theseus" with role "viewer"
    And "Bob" is signed in
    When "Bob" attempts to change "Carol"'s role on project "Theseus" to "editor"
    Then the response status is 403
    And "Carol"'s role on project "Theseus" remains "viewer"

  @S-006 @criterion-3
  Scenario: Non-owner cannot remove another member or demote themselves
    Given "Carol" is a member of project "Theseus" with role "viewer"
    And "Bob" is signed in
    When "Bob" attempts to remove "Carol" from project "Theseus"
    Then the response status is 403
    And "Carol" remains a member of project "Theseus"

  @S-007 @criterion-4
  Scenario: Project owner cannot remove or demote themselves
    Given "Alice" is signed in
    When "Alice" attempts to remove "Alice" from project "Theseus"
    Then the response status is 400
    And "Alice" remains role "owner" on project "Theseus"

  @S-008 @criterion-4
  Scenario: Reject assigning invalid role or owner role
    Given "Alice" is signed in
    When "Alice" attempts to update "Bob"'s role on project "Theseus" to "owner"
    Then the response status is 400
    And "Bob"'s role on project "Theseus" remains "editor"

  @S-009 @criterion-1
  Scenario: Non-member cannot view project member list
    Given "Dave" is a signed-in user who is not a member of project "Theseus"
    When "Dave" attempts to request the member list for project "Theseus"
    Then the response status is 403

  @S-010 @criterion-2
  Scenario: Removing or updating a non-existent member returns 404
    Given "Alice" is signed in
    When "Alice" attempts to remove non-member "Dave" from project "Theseus"
    Then the response status is 404
