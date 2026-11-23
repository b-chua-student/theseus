Feature: Shared Project Discovery

  Background:
    Given a signed-in user "Alice" owns project "Theseus"
    And "Bob" is a member of project "Theseus" with role "editor"
    And "Carol" is a registered user who is not a member of project "Theseus"

  @S-001 @criterion-1
  Scenario: Collaborator lists projects shared with them
    Given "Bob" is signed in
    When "Bob" requests their accessible projects
    Then the response status is 200
    And the project list includes "Theseus" with ownership "shared" and role "editor"

  @S-002 @criterion-1
  Scenario: Collaborator filters workspace list to shared projects only
    Given "Bob" owns project "Notes"
    And "Bob" is signed in
    When "Bob" requests their accessible projects with scope "shared"
    Then the response status is 200
    And the project list includes "Theseus"
    And the project list does not include "Notes"

  @S-003 @criterion-1
  Scenario: Collaborator opens a shared project they joined
    Given "Bob" is signed in
    When "Bob" requests project details for "Theseus"
    Then the response status is 200
    And the project details include title "Theseus" and role "editor"

  @S-004 @criterion-2
  Scenario: Non-member cannot open a project they were not invited to
    Given "Carol" is signed in
    When "Carol" requests project details for "Theseus"
    Then the response status is 403
