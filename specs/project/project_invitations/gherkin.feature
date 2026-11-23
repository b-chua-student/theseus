Feature: Project Invitations

  Background:
    Given a signed-in user "Alice" owns project "Theseus"
    And "Bob" is a registered user who is not a member of project "Theseus"

  @S-001 @criterion-1
  Scenario: Project owner invites a collaborator by email
    When "Alice" invites "bob@example.com" to project "Theseus" as "editor"
    Then the response status is 201
    And a pending invitation exists for "bob@example.com" on project "Theseus"

  @S-002 @criterion-1
  Scenario: Invited user accepts a pending project invitation
    Given "Alice" has invited "bob@example.com" to project "Theseus" as "editor"
    And "Bob" is signed in
    When "Bob" accepts the invitation for project "Theseus"
    Then the response status is 200
    And "Bob" is a member of project "Theseus" with role "editor"

  @S-003 @criterion-2
  Scenario: Project owner revokes a pending project invitation
    Given "Alice" has invited "bob@example.com" to project "Theseus" as "viewer"
    When "Alice" revokes the invitation for "bob@example.com" on project "Theseus"
    Then the response status is 204
    And the invitation for "bob@example.com" on project "Theseus" has status "revoked"

  @S-004 @criterion-3
  Scenario: Invited user cannot accept a revoked invitation
    Given "Alice" has invited "bob@example.com" to project "Theseus" as "viewer"
    And "Alice" revokes the invitation for "bob@example.com" on project "Theseus"
    And "Bob" is signed in
    When "Bob" accepts the invitation for project "Theseus"
    Then the response status is 400

  @S-005 @criterion-3
  Scenario: Invited user cannot accept an expired invitation
    Given "Alice" sent an invitation to "bob@example.com" that expired 1 day ago
    And "Bob" is signed in
    When "Bob" accepts the invitation for project "Theseus"
    Then the response status is 400

  @S-006 @criterion-1
  Scenario: Non-owner cannot invite collaborators to a project
    Given "Bob" is signed in
    When "Bob" invites "carol@example.com" to project "Theseus" as "viewer"
    Then the response status is 403
