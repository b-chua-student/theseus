@authentication @oauth
Feature: User can log in through email via OAuth
  As a user
  I want to sign in with my email identity from an OAuth provider
  So that I can access the application without managing a separate password

  Background:
    Given the OAuth providers "Google" and "Microsoft" are enabled
    And I am not logged in
    And I am on the login page

  # ---------------------------------------------------------------
  # Login page
  # ---------------------------------------------------------------

  @smoke
  @S-001 @criterion-1
  Scenario: Login page shows OAuth provider options
    Then I should see a "Continue with Google" button
    And I should see a "Continue with Microsoft" button

  @S-002 @criterion-1
  Scenario: Provider redirect uses secure OAuth parameters
    When I click "Continue with Google"
    Then I should be redirected to the Google authorization endpoint
    And the request should use the authorization code flow with PKCE
    And the request should include a "state" and a "nonce" value
    And the requested scopes should be "openid email profile"

  # ---------------------------------------------------------------
  # Successful login
  # ---------------------------------------------------------------

  @smoke @happy-path
  @S-003 @criterion-2
  Scenario: New user signs in with a verified email and an account is created
    Given no account exists for "new.user@example.com"
    And Google returns verified email "new.user@example.com" and the display name "New User"
    When I complete Google sign-in and grant consent
    Then a new account should be created for "new.user@example.com"
    And the account should have the display name "New User" and no password credential
    And the Google identity should be linked to that account
    And I should be logged in
    And I should be redirected to the home page

  @smoke @happy-path
  @S-004 @criterion-2
  Scenario: Returning user signs in with a linked OAuth identity
    Given an account exists for "returning.user@example.com" linked to Google
    And Google will authenticate me as "returning.user@example.com" with a verified email
    When I click "Continue with Google"
    Then I should be logged in
    And I should be redirected to the home page
    And no duplicate account should be created

  @S-005 @criterion-3
  Scenario: An unlinked identity matches an existing email after a repository reload
    Given password account "A" with email "Mixed.Case@example.com" has been saved and reloaded
    And Google authenticates an unlinked subject with verified email "mixed.case@example.com"
    When I continue with Google
    Then I should remain signed out and be directed to use my existing sign-in method
    And account "A" and its credentials should be unchanged
    And no identity link or duplicate account should be created

  @S-006 @criterion-2
  Scenario Outline: Provisioning handles an unusable provider display name
    Given an unlinked Google subject has a new verified email and <name> as its profile name
    When I complete Google sign-in
    Then my new account should have the display name "Theseus user"
    And I should be signed in to that account

    Examples:
      | name                 |
      | no value             |
      | only whitespace      |
      | a 51-character value |

  @S-007 @criterion-3
  Scenario: An OAuth-only account has no usable password credential
    Given a previously provisioned OAuth-only account has been saved and reloaded
    When I attempt password login for that account
    Then I should receive the ordinary invalid-credentials response
    And I should remain signed out

  @S-008 @criterion-2
  Scenario: User returns to the originally requested page after login
    Given I tried to open "/settings/profile" while logged out
    And an account exists for "returning.user@example.com" linked to Google
    When I log in with Google as "returning.user@example.com"
    Then I should be redirected to "/settings/profile"

  @S-009 @criterion-2
  Scenario Outline: External return destinations fall back to home
    Given my requested return destination is "<destination>"
    When I log in successfully with Google
    Then I should be redirected to the home page

    Examples:
      | destination                 |
      | https://example.org/profile |
      | //example.org/profile       |

  @S-010 @criterion-2
  Scenario: Linked identity is matched by provider subject if the provider email changes
    Given an account exists linked to Google subject "google-sub-123"
    And Google will authenticate subject "google-sub-123" with the new verified email "changed@example.com"
    When I click "Continue with Google"
    Then I should be logged in to the existing account

  # ---------------------------------------------------------------
  # Email validation rules
  # ---------------------------------------------------------------

  @S-011 @criterion-2
  Scenario: A linked subject returns an email already held by another account
    Given account "A" with email "original@example.com" is linked to Google subject "sub-A"
    And account "B" has email "changed@example.com"
    When I sign in through the same Google issuer as "sub-A" with verified email "changed@example.com"
    Then my session should identify account "A"
    And account "A" should retain email "original@example.com"
    And account "B" should retain email "changed@example.com"
    And the identity links for both accounts should be unchanged

  @security
  @S-012 @criterion-3
  Scenario: Login is rejected when the provider email is not verified
    Given Google will authenticate me as "unverified@example.com" with an unverified email
    When I click "Continue with Google"
    Then I should not be logged in
    And I should be returned to the login page
    And I should see the message "Your email address must be verified with the provider to sign in."
    And no account should be created for "unverified@example.com"

  @S-013 @criterion-3
  Scenario: Login is rejected when the provider returns no email
    Given Google will authenticate me but return no email address
    When I click "Continue with Google"
    Then I should not be logged in
    And I should see the message "We could not get an email address from your provider."

  # ---------------------------------------------------------------
  # Failure and cancellation
  # ---------------------------------------------------------------

  @S-014 @criterion-3
  Scenario: User denies consent at the provider
    When I deny consent during Google sign-in
    Then I should not be logged in
    And I should be returned to the login page
    And I should see the message "Sign-in was cancelled. Please try again."

  @S-015 @criterion-3
  Scenario: Provider returns an error
    Given Google will respond with the error "server_error"
    When I click "Continue with Google"
    Then I should not be logged in
    And I should see the message "We couldn't sign you in with Google. Please try again."
    And the failure should be recorded in the audit log

  @S-016 @criterion-3
  Scenario: Theseus receives a callback but the token exchange times out
    Given I started Google sign-in and the provider returned a valid authorization code
    When the token endpoint times out during the exchange
    Then I should remain signed out and return to the login page
    And I should see a retry message and the enabled Microsoft option

  @S-017 @criterion-3
  Scenario: User reopens Theseus after an interrupted provider redirect
    Given I left Theseus for Google and the provider page failed to load
    When I reopen the Theseus login page without completing a callback
    Then I should remain signed out
    And I should see the enabled Microsoft option

  @S-018 @criterion-3
  Scenario: Suspended account cannot sign in
    Given an account exists for "suspended.user@example.com" linked to Google
    And that account has status "suspended"
    And Google will authenticate me as "suspended.user@example.com" with a verified email
    When I click "Continue with Google"
    Then I should not be logged in
    And I should see the message "This account is unavailable. Please contact support."

  # ---------------------------------------------------------------
  # Security validation
  # ---------------------------------------------------------------

  @security
  @S-019 @criterion-3
  Scenario Outline: Callback with invalid security parameters is rejected
    Given I started a Google sign-in and have a pending authorization request
    When its callback is processed with <problem> as the only invalid condition
    Then I should not be logged in
    And I should see the message "We couldn't complete sign-in. Please try again."
    And the failure should be recorded in the audit log

    Examples:
      | problem                          |
      | a missing state value            |
      | a state value that does not match |
      | an expired authorization code    |
      | an already used authorization code |
      | an ID token with a wrong audience |
      | an ID token with an invalid signature |
      | an ID token with a wrong issuer   |
      | an expired ID token               |
      | an ID token with a wrong nonce   |

  @security
  @S-020 @criterion-1
  Scenario: Tokens are never exposed in logs or the browser
    Given I log in successfully with Google
    Then the provider tokens should not appear in application logs
    And the provider tokens should not be accessible from client-side JavaScript

  @security
  @S-021 @criterion-2
  Scenario: Session cookie is set with secure attributes
    When I log in successfully with Google
    Then the session cookie should be "HttpOnly"
    And the session cookie should be "Secure"
    And the session cookie should have "SameSite" set to "Lax"

  # ---------------------------------------------------------------
  # Logout and auditing
  # ---------------------------------------------------------------

  @S-022 @criterion-2
  Scenario: User logs out
    Given I am logged in via Google
    When I click "Log out"
    Then my session should be ended
    And I should be redirected to the login page
    And protected pages should require me to log in again

  @S-023 @criterion-2
  Scenario: Successful login is audited
    When I log in successfully with Google as "audit.user@example.com"
    Then the audit log should contain a "login_success" entry for "audit.user@example.com" with provider "Google"
    And the audit log entry should not contain any tokens
