Feature: Project Invitations

  Background:
    Given a signed-in user "Alice" owns project "Theseus"
    And "Bob" is a registered user with email "bob@example.com"

  @S-001 @criterion-1
  Scenario: Project owner invites a collaborator by email
    Given "Alice" is signed in
    When "Alice" invites "bob@example.com" to project "Theseus" with role "editor"
    Then the response status is 201
    And the response includes an invitation ID and token
    And a pending invitation exists for "bob@example.com" with role "editor"

  @S-002 @criterion-2
  Scenario: Invited user accepts a valid pending invitation
    Given "Alice" has sent a pending invitation to "bob@example.com" for "Theseus" with role "editor"
    And "Bob" is signed in
    When "Bob" accepts the invitation using its token
    Then the response status is 200
    And "Bob" is a member of project "Theseus" with role "editor"
    And the invitation status is "accepted"

  @S-003 @criterion-3
  Scenario: Project owner revokes a pending invitation
    Given "Alice" has sent a pending invitation to "bob@example.com" for "Theseus" with role "viewer"
    And "Alice" is signed in
    When "Alice" revokes the invitation
    Then the response status is 204
    And the invitation status is "revoked"

  @S-004 @criterion-3
  Scenario: Accepting a revoked invitation is rejected
    Given "Alice" has revoked the invitation to "bob@example.com" for "Theseus"
    And "Bob" is signed in
    When "Bob" attempts to accept the invitation using its token
    Then the response status is 410
    And "Bob" is not a member of project "Theseus"

  @S-005 @criterion-3
  Scenario: Accepting an expired invitation is rejected
    Given "Alice" sent an invitation to "bob@example.com" for "Theseus" that expired 7 days ago
    And "Bob" is signed in
    When "Bob" attempts to accept the invitation using its token
    Then the response status is 410
    And "Bob" is not a member of project "Theseus"

  @S-006 @criterion-1
  Scenario: Non-owner cannot invite or revoke collaborators
    Given "Bob" is a member of project "Theseus" with role "editor"
    And "Bob" is signed in
    When "Bob" attempts to invite "carol@example.com" to project "Theseus" with role "viewer"
    Then the response status is 403
    And no pending invitation exists for "carol@example.com"

  @S-007 @criterion-4
  Scenario: Reject duplicate pending invitation and normalize email case
    Given "Alice" has sent a pending invitation to "bob@example.com" for "Theseus" with role "editor"
    And "Alice" is signed in
    When "Alice" attempts to invite "  Bob@Example.com " to project "Theseus" with role "viewer"
    Then the response status is 409
    And only one pending invitation exists for "bob@example.com"

  @S-008 @criterion-4
  Scenario: Reject inviting project owner or existing project member
    Given "Bob" is a member of project "Theseus" with role "editor"
    And "Alice" is signed in
    When "Alice" attempts to invite "bob@example.com" to project "Theseus" with role "viewer"
    Then the response status is 409
    And no pending invitation exists for "bob@example.com"

  @S-009 @criterion-4
  Scenario: Reject invalid email or invalid role when creating invitation
    Given "Alice" is signed in
    When "Alice" attempts to invite "not-an-email" to project "Theseus" with role "admin"
    Then the response status is 400

  @S-010 @criterion-2
  Scenario: Reject invitation acceptance when signed-in user email does not match
    Given "Alice" has sent a pending invitation to "bob@example.com" for "Theseus" with role "editor"
    And "Carol" is a signed-in user with email "carol@example.com"
    When "Carol" attempts to accept the invitation using its token
    Then the response status is 403
    And "Carol" is not a member of project "Theseus"

  @S-011 @criterion-3
  Scenario: Reject revoking an already accepted invitation
    Given "Bob" has accepted the invitation for "Theseus"
    And "Alice" is signed in
    When "Alice" attempts to revoke the accepted invitation
    Then the response status is 409

  @S-012 @criterion-4
  Scenario: Allow re-inviting after previous invitation was revoked
    Given "Alice" has revoked the invitation to "bob@example.com" for "Theseus"
    And "Alice" is signed in
    When "Alice" invites "bob@example.com" to project "Theseus" with role "viewer"
    Then the response status is 201
    And a pending invitation exists for "bob@example.com" with role "viewer"
