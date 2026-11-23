Feature: Per-Manuscript Access Roles

  Background:
    Given a signed-in user "Alice" owns project "Theseus"
    And project "Theseus" has manuscripts "Manuscript 1" and "Manuscript 2"
    And "Bob" is a member of project "Theseus"

  @S-001 @criterion-1
  Scenario: User edits a manuscript where they have editor access
    Given "Bob" has "editor" access to "Manuscript 1"
    And "Bob" has "viewer" access to "Manuscript 2"
    And "Bob" is signed in
    When "Bob" updates the content of "Manuscript 1"
    Then the response status is 200
    And "Manuscript 1" reflects the updated content

  @S-002 @criterion-1
  Scenario: User views a manuscript where they have viewer access
    Given "Bob" has "editor" access to "Manuscript 1"
    And "Bob" has "viewer" access to "Manuscript 2"
    And "Bob" is signed in
    When "Bob" views "Manuscript 2"
    Then the response status is 200

  @S-003 @criterion-1 @criterion-2
  Scenario: User cannot edit a manuscript where they only have viewer access
    Given "Bob" has "editor" access to "Manuscript 1"
    And "Bob" has "viewer" access to "Manuscript 2"
    And "Bob" is signed in
    When "Bob" attempts to update the content of "Manuscript 2"
    Then the response status is 403
    And "Manuscript 2" remains unchanged

  @S-004 @criterion-2
  Scenario: Project owner assigns different manuscript roles to a collaborator
    Given "Bob" has "editor" access to "Manuscript 1"
    And "Alice" is signed in
    When "Alice" assigns "Bob" role "viewer" on "Manuscript 2"
    Then "Bob" has role "editor" on "Manuscript 1" and "viewer" on "Manuscript 2"

  @S-005 @criterion-2
  Scenario: Non-owner cannot assign manuscript access roles
    Given "Bob" is signed in
    When "Bob" attempts to assign "Bob" role "editor" on "Manuscript 2"
    Then the response status is 403
