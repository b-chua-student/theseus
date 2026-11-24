Feature: Shared Project Discovery

  Background:
    Given a signed-in user "Alice" owns project "Theseus"
    And "Bob" is a member of project "Theseus" with role "editor"
    And "Carol" is a signed-in user who is not a member of project "Theseus"

  @S-001 @criterion-1
  Scenario: Collaborator sees shared projects alongside owned projects
    Given "Bob" owns project "Notes"
    And "Bob" is signed in
    When "Bob" requests their project list
    Then the response status is 200
    And the project list includes "Notes" with ownership "owned" and role "owner"
    And the project list includes "Theseus" with ownership "shared" and role "editor"

  @S-002 @criterion-2
  Scenario: Collaborator filters project list to shared projects only
    Given "Bob" owns project "Notes"
    And "Bob" is signed in
    When "Bob" requests their project list with scope "shared"
    Then the response status is 200
    And the project list includes "Theseus" with ownership "shared" and role "editor"
    And the project list does not include "Notes"

  @S-003 @criterion-2
  Scenario: User with only owned projects gets empty list for shared scope
    Given "Alice" is signed in
    When "Alice" requests their project list with scope "shared"
    Then the response status is 200
    And the project list is empty

  @S-004 @criterion-2
  Scenario: Invalid scope parameter returns 400
    Given "Bob" is signed in
    When "Bob" requests their project list with scope "archived"
    Then the response status is 400

  @S-005 @criterion-3
  Scenario: Collaborator opens a shared project and sees effective role
    Given "Bob" is signed in
    When "Bob" requests details for project "Theseus"
    Then the response status is 200
    And the response includes project title "Theseus" and role "editor"

  @S-006 @criterion-3
  Scenario: Non-member is denied project details without leaking metadata
    Given "Carol" is signed in
    When "Carol" attempts to request details for project "Theseus"
    Then the response status is 403
    And the response body does not contain "Theseus" or "Alice"

  @S-007 @criterion-3
  Scenario: Removed member no longer sees project in list or details
    Given "Alice" has removed "Bob" from project "Theseus"
    And "Bob" is signed in
    When "Bob" requests their project list
    Then the project list does not include "Theseus"
    When "Bob" attempts to request details for project "Theseus"
    Then the response status is 403

  @S-008 @criterion-1
  Scenario: Pending invitations do not appear in shared project list
    Given "Alice" has sent a pending invitation to "carol@example.com" for "Theseus"
    And "Carol" is signed in
    When "Carol" requests their project list
    Then the project list does not include "Theseus"
