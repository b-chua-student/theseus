Feature: Per-Manuscript Access

  Background:
    Given a signed-in user "Alice" has role "owner" on project "Theseus"
    And "Bob" is a member of project "Theseus" with baseline role "viewer"
    And project "Theseus" contains manuscripts "Manuscript 1" and "Manuscript 2"

  @S-001 @criterion-1
  Scenario: Member with editor override can edit assigned manuscript
    Given "Alice" has assigned "Bob" role "editor" on "Manuscript 1"
    And "Bob" is signed in
    When "Bob" edits "Manuscript 1" with content "Updated draft"
    Then the response status is 200
    And "Manuscript 1" has content "Updated draft"

  @S-002 @criterion-1
  Scenario: Member with viewer access can view manuscript
    Given "Alice" has assigned "Bob" role "viewer" on "Manuscript 2"
    And "Bob" is signed in
    When "Bob" views "Manuscript 2"
    Then the response status is 200

  @S-003 @criterion-1
  Scenario: Member with viewer access cannot edit manuscript
    Given "Alice" has assigned "Bob" role "viewer" on "Manuscript 2"
    And "Manuscript 2" has content "Original text"
    And "Bob" is signed in
    When "Bob" attempts to edit "Manuscript 2" with content "Unauthorized change"
    Then the response status is 403
    And "Manuscript 2" still has content "Original text"

  @S-004 @criterion-2
  Scenario: Project owner assigns per-manuscript role to a project member
    Given "Alice" is signed in
    When "Alice" assigns "Bob" role "editor" on "Manuscript 1"
    Then the response status is 200
    And "Bob"'s effective role on "Manuscript 1" is "editor"

  @S-005 @criterion-2
  Scenario: Non-owner cannot assign or change per-manuscript roles
    Given "Carol" is a member of project "Theseus" with baseline role "editor"
    And "Carol" is signed in
    When "Carol" attempts to assign "Bob" role "editor" on "Manuscript 2"
    Then the response status is 403

  @S-006 @criterion-3
  Scenario: Member without manuscript override inherits baseline project role
    Given "Carol" is a member of project "Theseus" with baseline role "editor"
    And "Carol" is signed in
    When "Carol" edits "Manuscript 2" with content "Baseline editor change"
    Then the response status is 200
    And "Manuscript 2" has content "Baseline editor change"

  @S-007 @criterion-3
  Scenario: Non-member is denied access to project manuscripts
    Given "Dave" is a signed-in user who is not a member of project "Theseus"
    When "Dave" attempts to view "Manuscript 1"
    Then the response status is 403

  @S-008 @criterion-2
  Scenario: Project owner cannot have manuscript access restricted
    Given "Alice" is signed in
    When "Alice" attempts to assign "Alice" role "viewer" on "Manuscript 1"
    Then the response status is 400
