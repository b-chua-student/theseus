@authentication @oauth
Feature: User can log in through email via OAuth
  As a user
  I want to sign in with my email identity from an OAuth provider
  So that I can access the application without managing a separate password

  Background:
    Given Google is the only enabled OAuth provider
    And I am not logged in
    And I am on the login page

  # ---------------------------------------------------------------
  # Login page
  # ---------------------------------------------------------------

  @smoke
  @S-001 @criterion-1
  Scenario: Login page shows OAuth provider options
    Then I should see a "Continue with Google" button
    And Google should be the only OAuth choice

  @S-002 @criterion-1
  Scenario Outline: User continues to the selected provider to authorize sign-in
    When I click "Continue with <provider>"
    Then I should see the <provider> authorization page for Theseus

    Examples:
      | provider  |
      | Google    |

  @edge @S-029 @criterion-4
  Scenario Outline: The Google button remains visible when sign-in becomes unavailable
    Given sign-in with <provider> has become unavailable
    When I reopen the regular sign-in page and select "Continue with <provider>"
    Then I should see that sign-in with <provider> is unavailable
    And I should remain signed out on the sign-in page with the Google button visible

    Examples:
      | provider  |
      | Google    |

  # ---------------------------------------------------------------
  # Successful login
  # ---------------------------------------------------------------

  @smoke @happy-path
  @S-003 @criterion-2
  Scenario: First sign-in automatically creates a passwordless account with the provider's display name
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
  Scenario: An unlinked identity matches an existing email on a later sign-in
    Given password account "A" with email "Mixed.Case@example.com" already exists
    And Google authenticates an unlinked subject with verified email "mixed.case@example.com"
    When I continue with Google
    Then I should remain signed out and be directed to use my existing sign-in method
    And the sign-in page should explain how to continue with my password and offer "Try again"
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
    Given I have an existing OAuth-only account
    When I attempt password login for that account
    Then I should receive the ordinary invalid-credentials response
    And I should remain signed out

  @S-008 @criterion-2
  Scenario: User returns to the originally requested page after login
    Given I tried to open a protected Theseus page other than the home page while logged out
    And an account exists for "returning.user@example.com" linked to Google
    When I log in with Google as "returning.user@example.com"
    Then I should be returned to the page I originally requested

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
    Given an account with email "original@example.com" is linked to Google subject "google-sub-123"
    And Google will authenticate subject "google-sub-123" with the new verified email "changed@example.com"
    When I click "Continue with Google"
    Then I should be logged in to the existing account
    And my Theseus email should still be "original@example.com"

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
  @S-012 @criterion-2
  Scenario Outline: User signs in with an unverified provider email
    Given no account exists for "unverified@example.com"
    When I successfully authenticate with <provider> using the unverified email "unverified@example.com"
    Then I should be logged in to Theseus

    Examples:
      | provider  |
      | Google    |

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
    And I should be back on the sign-in page with a "Try again" action
    And the failure should follow the existing Theseus sign-in audit behavior

  @S-016 @criterion-3
  Scenario: The provider takes too long to complete sign-in
    Given I started Google sign-in
    When Google takes too long to complete sign-in
    Then I should remain signed out and return to the login page
    And I should see a retry message and the password sign-in option

  @S-017 @criterion-3
  Scenario: User reopens Theseus after an interrupted provider redirect
    Given I left Theseus for Google and the provider page failed to load
    When I return to Theseus without completing sign-in
    Then I should remain signed out
    And I should see the message "Sign-in wasn’t completed"
    And I should be able to restart Google sign-in or use my password

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
  Scenario: Theseus cannot confirm the provider sign-in
    Given I started Google sign-in
    When Theseus cannot confirm that Google authenticated me for this attempt
    Then I should remain signed out
    And I should see the message "We couldn't complete sign-in. Please try again."
    And the failure should follow the existing Theseus sign-in audit behavior
  @security
  @S-020 @criterion-1
  Scenario: Tokens are never exposed in logs or the browser
    Given I log in successfully with Google
    Then the provider tokens should not appear in application logs
    And the provider tokens should not be accessible from client-side JavaScript

  @security
  @S-021 @criterion-2
  Scenario: The Theseus session identifies the signed-in user
    When I log in successfully with Google
    Then I should be able to reopen a protected Theseus page as the same user
  # ---------------------------------------------------------------
  # Logout and auditing
  # ---------------------------------------------------------------

  @S-022 @criterion-2
  Scenario: OpenAuth user ends the Theseus session through the existing sign-out flow
    Given I am logged in via Google
    When I click "Log out"
    Then my session should be ended
    And I should be redirected to the login page
    And protected pages should require me to log in again

  @S-023 @criterion-2
  Scenario: Successful OpenAuth sign-in reuses an existing Theseus audit event
    Given Theseus records an audit event for successful sign-ins with its other methods
    When I log in successfully with Google as "audit.user@example.com"
    Then the audit log should record the same type of sign-in event
    And the audit log entry should not contain any tokens

  @S-024 @criterion-2
  Scenario: User explicitly links a matching provider after signing in
    Given I was directed to my existing sign-in method because my unlinked Google identity matched my Theseus email
    And I signed in to that account using my existing method
    And I explicitly linked that Google identity and signed out
    When I sign in again with the same Google identity
    Then I should be logged in to my existing Theseus account

  @S-025 @criterion-2
  Scenario: User edits the display name supplied by the provider
    Given I am signed in to my new passwordless account with the initial provider name "New User"
    When I change my Theseus display name to "Alex" and save it
    Then I should see "Alex" as my display name when I reopen my profile

  @S-026 @criterion-2
  Scenario: The originally requested Theseus page is no longer available
    Given I was sent to sign in when I tried to open a Theseus page
    And that page is no longer available
    When I successfully sign in
    Then I should be redirected to the Theseus home page

  @S-027 @criterion-2
  Scenario: Only the provider data needed by Theseus is retained
    Given my provider supplies the account fields and additional profile data
    When I complete sign-in with that provider
    Then Theseus should keep only the stable provider ID, email, email verification status, and display name
    And Theseus should retain neither the raw provider profile nor any provider tokens

  @S-028 @criterion-3
  Scenario: Provider tokens are discarded after unsuccessful authentication
    Given Theseus has received provider tokens during my sign-in attempt
    When authentication ends in failure
    Then Theseus should retain no provider tokens from that attempt

  @S-030 @criterion-5
  Scenario: A new user sees how to create an account
    Then the first-time Google registration note should be absent
    And password sign-up should be available

  @S-031 @criterion-5
  Scenario: Restart an expired Google sign-in
    Given my Google sign-in request expired
    And I see "This sign-in request expired"
    When I select "Restart Google sign-in"
    Then I should reach Google authorization for a fresh attempt

  @S-032 @criterion-5
  Scenario: Retry when Theseus cannot reach Google
    Given Theseus cannot reach Google during sign-in
    When I return to the sign-in page
    Then I should see a message explaining that Theseus could not reach Google
    And I should remain signed out with a "Try again" action

  @S-033 @criterion-5
  Scenario: Reopen Account after linking Google
    Given I signed in with my password and my account has no Google identity
    And I selected "Link Google" in Account and completed linking
    When I reopen Account
    Then I should see "Google connected"
    And the "Link Google" action should be absent

  @S-034 @criterion-6
  Scenario: Returning Google user signs in with existing approval
    Given I previously clicked Allow and successfully signed in to Theseus with Google
    And I signed out of Theseus
    And Google can authenticate the same account using its existing approval
    When I continue with Google using that account
    Then I should be signed in to my original Theseus account without clicking Allow again

  @S-035 @criterion-6
  Scenario: Google requires interaction for a returning user
    Given I previously signed in to Theseus with Google and then signed out
    And Google requires interaction before it can authenticate me again
    When I continue with Google
    Then I should be able to complete Google's normal sign-in flow
    And I should receive a Theseus session only after Google authenticates me

  @S-036 @criterion-7
  Scenario: Continue with the last successful Google account
    Given I last signed in successfully with Google as "reader@example.com" in this browser
    And I signed out of Theseus
    And Google sign-in is available
    When I open the sign-in page
    Then I should see "Continue with reader@example.com" and "Use another Google account"
    And selecting "Continue with reader@example.com" should start Google sign-in for "reader@example.com"

  @S-037 @criterion-7
  Scenario: A browser without a remembered account offers generic Google sign-in
    Given this browser has no remembered Google account
    When I open the sign-in page
    Then I should see "Continue with Google"
