@email-verification
Feature: Email verification
  As a registered user
  I want to verify my email address
  So that the platform can trust that I own it and I can access all features

  Background:
    Given the verification link expiry is 24 hours
    And the resend limit is 3 emails per hour with a 60 second cooldown

  # ---------------------------------------------------------------
  # Sending the verification email
  # ---------------------------------------------------------------

  @S-001 @criterion-1 @smoke @send
  Scenario: Verification email is sent after registration
    Given I am on the registration page
    When I register with email "jane@example.com", a valid display name and a valid password
    Then my account is created with status "unverified"
    And a verification email is sent to "jane@example.com"
    And the email contains a unique verification link
    And I see a message "Check your inbox to verify your email"

  @S-002 @criterion-2 @send
  Scenario: Registration succeeds even if the email provider fails temporarily
    Given the email provider is temporarily unavailable
    When I register with email "jane@example.com", a valid display name and a valid password
    Then my account is created with status "unverified"
    And the verification email is queued for retry
    And I see a message "Check your inbox to verify your email"

  # ---------------------------------------------------------------
  # Verifying with a link
  # ---------------------------------------------------------------

  @S-003 @criterion-3 @smoke @verify
  Scenario: Successfully verify email with a valid link
    Given I registered with email "jane@example.com"
    And I received a verification link less than 24 hours ago
    When I confirm the verification link
    Then my email is marked as verified
    And my account status becomes "verified"
    And I see a message "Your email has been verified"
    And an audit event "email_verified" is recorded

  @S-004 @criterion-4 @verify
  Scenario: Verification link cannot be used twice
    Given I registered with email "jane@example.com"
    And I have already verified using my verification link
    When I confirm the same verification link again
    Then I see a message "This link has already been used"
    And my account remains "verified"

  @S-005 @criterion-5 @verify
  Scenario: Verification link has expired
    Given I registered with email "jane@example.com"
    And my verification link was issued more than 24 hours ago
    When I confirm the verification link
    Then my email is not verified
    And I see a message "This link has expired"
    And I see an option to "Resend verification email"

  @S-006 @criterion-6 @verify @security
  Scenario Outline: Invalid verification links are rejected
    When I confirm a verification link with a <type> token
    Then my email is not verified
    And I see a message "This verification link is not valid"
    And the response does not reveal whether any account exists

    Examples:
      | type       |
      | malformed  |
      | tampered   |
      | unknown    |
      | empty      |

  @S-007 @criterion-7 @verify
  Scenario: Newer verification link invalidates older ones
    Given I registered with email "jane@example.com"
    And I requested a new verification email
    When I confirm the first verification link I received
    Then my email is not verified
    And I see a message "This link is no longer valid"

  @S-008 @criterion-8 @verify
  Scenario: Verification while logged in as a different user
    Given I am logged in as "john@example.com"
    When I confirm the verification link for "jane@example.com"
    Then "jane@example.com" is marked as verified
    And my session for "john@example.com" is unchanged

  # ---------------------------------------------------------------
  # Resending the verification email
  # ---------------------------------------------------------------

  @S-009 @criterion-9 @smoke @resend
  Scenario: Request a new verification email
    Given I am logged in with an unverified account
    When I click "Resend verification email"
    Then a new verification email is sent to my address
    And any previously issued verification links are invalidated
    And I see a message "Verification email sent"

  @S-010 @criterion-10 @resend @ratelimit
  Scenario: Resend is blocked during the cooldown period
    Given I am logged in with an unverified account
    And I requested a verification email 30 seconds ago
    When I click "Resend verification email"
    Then no email is sent
    And I see a message "Please wait before requesting another email"

  @S-011 @criterion-11 @resend @ratelimit
  Scenario: Resend is blocked after reaching the hourly limit
    Given I am logged in with an unverified account
    And I have requested 3 verification emails in the last hour
    When I click "Resend verification email"
    Then no email is sent
    And I see a message "You have reached the limit. Try again later"

  @S-012 @criterion-12 @resend
  Scenario: Verified users cannot request a verification email
    Given I am signed in as a verified user
    When I request a verification email
    Then no email is sent
    And I see a message "Your email is already verified"

  # ---------------------------------------------------------------
  # Access control for unverified accounts
  # ---------------------------------------------------------------

  @S-013 @criterion-13 @smoke @access
  Scenario: Unverified user can log in with restricted access
    Given I have an unverified account
    When I log in with valid credentials
    Then I am logged in
    And I see a banner "Please verify your email to unlock all features"

  @S-014 @criterion-14 @access
  Scenario Outline: Unverified user is blocked from restricted actions
    Given I am logged in with an unverified account
    When I attempt to <action>
    Then the API returns 403 with error code "email_verification_required"
    And the workspace is unchanged
    And I see a message "Verify your email to continue"

    Examples:
      | action                  |
      | create a project             |
      | edit a manuscript section    |
      | upload a source              |
      | restore a revision           |
      | switch drafts                |
      | send an assistant exchange   |

  @S-015 @criterion-15 @access
  Scenario: Features unlock immediately after verification
    Given I am logged in with an unverified account
    When I refresh the page after confirming my email using a valid link
    Then the verification banner is no longer shown
    And I can create a project

  # ---------------------------------------------------------------
  # Input validation
  # ---------------------------------------------------------------

  @S-016 @criterion-16 @validation
  Scenario Outline: Registration rejects invalid email formats
    Given I am on the registration page
    When I register with email "<email>" and otherwise valid registration details
    Then no account is created
    And I see a message "Enter a valid email address"

    Examples:
      | email              |
      | plainaddress       |
      | missing@domain     |
      | @no-local.com      |
      | spaces in@mail.com |

  # ---------------------------------------------------------------
  # Security and auditing
  # ---------------------------------------------------------------

  @S-017 @criterion-17 @security
  Scenario: Verification tokens are stored securely
    Given a verification token is generated for my account
    Then the verification record stores only a hash of the token
    And the token is at least 128 bits of random data
    And the token and email address do not appear in application logs

  @S-018 @criterion-18 @audit
  Scenario Outline: Verification events are logged
    When the event "<event>" occurs for my account
    Then an audit record is created with the event type, user id, and timestamp

    Examples:
      | event                |
      | email_sent           |
      | email_resent         |
      | email_verified       |
      | verification_failed  |
      | resend_rate_limited  |

  @S-019 @criterion-19 @verify
  Scenario: An inbox preview leaves the token usable
    Given I registered and opened my inbox link in a signed-out browser
    When the browser loads the verification landing page
    Then I see a confirmation control
    And the token remains usable
    And my email remains unverified

  @S-020 @criterion-20 @send
  Scenario: Delivery resumes after a provider outage
    Given my registration succeeded during a provider outage
    And the delivery worker restarted
    When the provider recovers and the pending delivery is retried
    Then I receive a usable verification link for my existing account

  @S-021 @criterion-21 @access
  Scenario: A new user unlocks project creation in the original session
    Given I just registered and my browser holds the registration session
    And GET /api/projects succeeds and POST /api/projects returns 403 for a valid project
    When I explicitly confirm my inbox link in a separate signed-out browser and refresh the original page
    Then the separate browser remains signed out
    And GET /api/auth/me in the original session reports verified true and verification_required false
    And submitting the same project in the original session succeeds

  @S-022 @criterion-22 @persistence
  Scenario Outline: Confirmation survives a new database connection and login
    Given I confirmed my address using <adapter> storage
    When I sign in again after the application restarts
    Then GET /api/auth/me reports verified true and verification_required false

    Examples:
      | adapter    |
      | PostgreSQL |
      | MongoDB    |

  @S-023 @criterion-23 @rollout
  Scenario Outline: Existing accounts retain workspace access after migration
    Given my account existed in <adapter> before the verification rollout
    When I sign in after the migration
    Then GET /api/auth/me reports verified false and verification_required false
    And I can create a project

    Examples:
      | adapter    |
      | PostgreSQL |
      | MongoDB    |

  @S-024 @criterion-24 @resend
  Scenario Outline: Public resend gives the same acknowledgement
    Given the supplied email address is <state>
    When I request verification by address while signed out
    Then I see "If an account exists, a verification email has been sent"
    And the number of newly queued deliveries is <count>

    Examples:
      | state        | count |
      | unknown      | 0     |
      | verified     | 0     |
      | rate limited | 0     |
      | eligible     | 1     |
