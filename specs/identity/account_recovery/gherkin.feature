@account-recovery @ACCT-REC-001
Feature: Account recovery by resetting a forgotten password
  As a registered user who has forgotten my password
  I want to reset it using a secure link sent to my email
  So that I can regain access to my account without contacting support

  Background:
    Given the following user accounts exist:
      | email             | password        |
      | alice@example.com | OldPassw0rd!xyz |
    And I am on the login page

  # ---------------------------------------------------------------------------
  # Requesting a reset link
  # ---------------------------------------------------------------------------

  @S-001 @criterion-1 @smoke @request
  Scenario: Forgot password link is available on the login page
    Given I can see the "Forgot password?" link
    When I click the "Forgot password?" link
    Then I should be on the password reset request page

  @S-002 @criterion-1 @smoke @request
  Scenario: Request a reset link with a registered email
    Given I am on the password reset request page
    When I submit the email "alice@example.com"
    Then I should see the message "If an account exists for that email, we've sent a password reset link."
    And a password reset email should be sent to "alice@example.com"
    And the email should contain a single-use reset link over HTTPS
    And the reset link should not contain the email address
    And an audit log entry "PASSWORD_RESET_REQUESTED" should be recorded

  @S-003 @criterion-1 @edge @security @request
  Scenario: Request a reset link with an unregistered email
    Given I am on the password reset request page
    When I submit the email "nobody@example.com"
    Then I should see the message "If an account exists for that email, we've sent a password reset link."
    And no email should be sent
    And the response should be indistinguishable from the registered email case

  @S-004 @criterion-1 @edge @request
  Scenario Outline: Reject invalid email formats
    Given I am on the password reset request page
    When I submit the email "<email>"
    Then I should see the validation error "Enter a valid email address."
    And no email should be sent

    Examples:
      | email             |
      |                   |
      | alice             |
      | alice@            |
      | @example.com      |
      | alice@@example.com|

  @S-005 @criterion-1 @request
  Scenario: Recovery uses the same email normalization as login
    Given I am on the password reset request page
    When I submit the email "alice@EXAMPLE.COM"
    Then a password reset email should be sent to "alice@example.com"

  @S-006 @criterion-1 @edge @request @security
  Scenario: Case-distinct local parts identify separate accounts
    Given another account exists with the stored address "Alice@example.com"
    When I request a reset for "Alice@example.com"
    Then a reset link should be issued only for the account stored as "Alice@example.com"

  @S-007 @criterion-3 @smoke @reset
  Scenario: Recover an account created through normal registration
    Given I register "bob@example.com" with the password "OldPassw0rd!xyz"
    And I log out
    And I have requested a reset for "bob@example.com"
    When I use the emailed link to set the password "N3wSecurePassw0rd"
    Then I should be redirected to the login page
    And "bob@example.com" should be able to log in with "N3wSecurePassw0rd"

  @S-008 @criterion-3 @edge @reset
  Scenario: Recover a legacy account
    Given Alice's stored account predates verification, password history and session versions
    When Alice completes recovery using the link delivered to her stored address
    Then her previous password hash should be the only entry in her password history
    And her session version should be 1

  @S-009 @criterion-2 @edge @security @token
  Scenario: Changing the account email invalidates an outstanding link
    Given Alice has received a reset link at her stored address
    When her account email changes before redemption
    Then the old link should be rejected
  @S-010 @criterion-2 @edge @request
  Scenario: Requesting a new link invalidates the previous link
    Given "alice@example.com" has requested a password reset and received link "A"
    And "alice@example.com" has requested another reset and received link "B"
    When I open reset link "A"
    Then I should see the error "This reset link is invalid or has expired."
    And reset link "B" should open the new password form

  # ---------------------------------------------------------------------------
  # Rate limiting
  # ---------------------------------------------------------------------------

  @S-011 @criterion-4 @edge @security @rate-limit
  Scenario: Reset requests are limited per email address
    Given "alice@example.com" has requested 5 password resets in the last hour
    When I submit the email "alice@example.com" on the password reset request page
    Then I should see the message "If an account exists for that email, we've sent a password reset link."
    And no additional password reset email should be sent to "alice@example.com"
    And an audit log entry "PASSWORD_RESET_RATE_LIMITED" should be recorded

  @S-012 @criterion-4 @edge @security @rate-limit
  Scenario: Reset requests are limited per IP address
    Given my IP address has submitted 20 password reset requests in the last hour
    When I submit the email "alice@example.com" on the password reset request page
    Then the request should be rejected with the message "Too many requests. Please try again later."
    And no email should be sent

  # ---------------------------------------------------------------------------
  # Opening the reset link
  # ---------------------------------------------------------------------------

  @S-013 @criterion-2 @smoke @token
  Scenario: Valid reset link shows the new password form
    Given "alice@example.com" has requested a password reset
    When I open the reset link from the email
    Then I should see the new password form
    And the form should have "New password" and "Confirm new password" fields
    And the page should not be cached
    And the page should send the header "Referrer-Policy: no-referrer"

  @S-014 @criterion-2 @edge @token
  Scenario: Expired reset link is rejected
    Given "alice@example.com" has requested a password reset
    And 31 minutes have passed
    When I open the reset link from the email
    Then I should see the error "This reset link is invalid or has expired."
    And I should see an option to request a new reset link
    And an audit log entry "PASSWORD_RESET_TOKEN_REJECTED" should be recorded

  @S-015 @criterion-2 @edge @token
  Scenario: Reset link still works just before it expires
    Given "alice@example.com" has requested a password reset
    And 29 minutes have passed
    When I open the reset link from the email
    Then I should see the new password form

  @S-016 @criterion-2 @edge @token @security
  Scenario: Tampered reset link is rejected
    Given "alice@example.com" has requested a password reset
    When I open the reset link with a modified token
    Then I should see the error "This reset link is invalid or has expired."

  @S-017 @criterion-2 @edge @token
  Scenario: Reset link cannot be reused after a successful reset
    Given "alice@example.com" has successfully reset their password using the reset link
    When I open the same reset link again
    Then I should see the error "This reset link is invalid or has expired."

  # ---------------------------------------------------------------------------
  # Setting a new password
  # ---------------------------------------------------------------------------

  @S-018 @criterion-3 @smoke @reset
  Scenario: Successfully reset the password
    Given "alice@example.com" has requested a password reset
    And I have opened the reset link from the email
    When I submit "N3wSecurePassw0rd" in both password fields
    Then I should see the message "Your password has been reset. You can now log in."
    And I should be redirected to the login page
    And the password for "alice@example.com" should be stored as a salted hash
    And an audit log entry "PASSWORD_RESET_COMPLETED" should be recorded
    And "alice@example.com" should be able to log in with "N3wSecurePassw0rd"

  @S-019 @criterion-3 @edge @reset
  Scenario: Old password no longer works after reset
    Given "alice@example.com" has successfully reset their password to "N3wSecurePassw0rd"
    When I log in with "alice@example.com" and "OldPassw0rd!xyz"
    Then I should see the login error "Invalid credentials"

  @S-020 @criterion-3 @edge @reset
  Scenario: Password confirmation does not match
    Given "alice@example.com" has requested a password reset
    And I have opened the reset link from the email
    When I submit "N3wSecurePassw0rd" with the confirmation "Different123Passw0rd"
    Then I should see the validation error "Passwords do not match."
    And the password for "alice@example.com" should not be changed
    And the reset link should remain valid

  @S-021 @criterion-3 @edge @reset @policy
  Scenario Outline: New password must meet the password policy
    Given "alice@example.com" has requested a password reset
    And I have opened the reset link from the email
    When I submit "<password>" in both password fields
    Then I should see the validation error "<error>"
    And the password for "alice@example.com" should not be changed

    Examples:
      | password          | error                                              |
      | Short1Aa          | Password must be at least 12 characters.           |
      | alllowercase12345 | Password must include an uppercase letter.         |
      | ALLUPPERCASE12345 | Password must include a lowercase letter.          |
      | NoNumbersHereAbcd | Password must include a number.                    |
      | OldPassw0rd!xyz   | You cannot reuse a recent password.                |
      | Password12345Abc  | This password is too common or has been breached.  |

  @S-022 @criterion-3 @edge @reset @policy
  Scenario: Cannot reuse any of the last 5 passwords
    Given the five previous passwords for "alice@example.com" include "Prev3Passw0rdCCC"
    And "alice@example.com" has requested a password reset
    And I have opened the reset link from the email
    When I submit "Prev3Passw0rdCCC" in both password fields
    Then I should see the validation error "You cannot reuse a recent password."

  # ---------------------------------------------------------------------------
  # Side effects after reset
  # ---------------------------------------------------------------------------

  @S-023 @criterion-5 @security @session
  Scenario: All active sessions are terminated after a reset
    Given "alice@example.com" is logged in on a laptop and a phone
    And "alice@example.com" has requested a password reset
    When "alice@example.com" completes the reset with the new password "N3wSecurePassw0rd"
    Then a request to the protected current-user endpoint from the laptop should return 401
    And the same request from the phone should return 401

  @S-024 @criterion-5 @notification
  Scenario: User is notified when their password is changed
    Given "alice@example.com" has requested a password reset
    When "alice@example.com" completes the reset with the new password "N3wSecurePassw0rd"
    Then a "password changed" notification email should be sent to "alice@example.com"
    And the email should include the time of the change
    And the email should advise contacting support if the change was not made by the user
    And the email should not contain the password or any reset token

  @S-025 @criterion-5 @edge @security @reset
  Scenario: Concurrent submissions can complete a reset only once
    Given Alice has received one valid reset link
    When two clients submit different policy-compliant passwords concurrently using that link
    Then exactly one reset should succeed
    And only the successful submission's password should authenticate Alice
    And exactly one password-change notification should be queued

  @S-026 @criterion-5 @edge @security @session
  Scenario: Reset revokes a session issued before session versions existed
    Given Alice has a valid legacy session cookie without a session version
    When Alice completes a password reset
    Then the protected current-user endpoint should return 401 for that cookie
  # ---------------------------------------------------------------------------
  # Resilience and accessibility
  # ---------------------------------------------------------------------------

  @S-027 @criterion-6 @edge @resilience
  Scenario: Email service outage does not reveal account existence
    Given the email service is unavailable
    When I submit the email "alice@example.com" on the password reset request page
    Then I should see the message "If an account exists for that email, we've sent a password reset link."
    And the email should be queued for retry
    And an alert should be raised for email delivery failure
    And delivery should resume if the service recovers while the link is current

  @S-028 @criterion-7 @edge @accessibility
  Scenario: Recovery screens are accessible
    Given I am on the password reset request page
    Then the page should meet WCAG 2.1 AA accessibility checks
    And all form fields should have visible labels
    And validation errors should be announced to screen readers
