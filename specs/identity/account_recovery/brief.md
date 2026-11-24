# Brief: Account Recovery (ACCT-REC-001)
Draft | High priority | 2026-11-24
## Goal
Allow registered users who have forgotten their password to securely regain access to their account by requesting a time-limited reset link sent to their registered email address and setting a new password.

## In Scope

| ID | Requirement |
|---|---|
| FR-01 | The login page shall provide a "Forgot password?" link leading to the reset request page. |
| FR-02 | The reset request page shall accept an email address and validate its format. |
| FR-03 | The system shall display the same confirmation message whether or not the email matches an account. |
| FR-04 | For a matching registered account, the system shall send an email containing a unique, single-use reset link. |
| FR-05 | The reset token shall expire after 30 minutes. |
| FR-06 | Requesting a new reset link shall invalidate any previously issued unused links for that account. |
| FR-07 | The reset page shall validate the token before showing the new password form. |
| FR-08 | The new password shall be entered twice and both entries must match. |
| FR-09 | The new password shall satisfy the password policy (see Constraints). |
| FR-10 | On success, the system shall store the new password hashed, invalidate the token, and revoke all existing Flask sessions for the account. |
| FR-11 | On success, the system shall send a password-changed notification email to the account's email address. |
| FR-12 | The system shall rate limit reset requests per email address and per IP address. |
| FR-13 | All reset requests, token validations, and completions shall be written to the audit log. |

## Non-Goals
- Recovery via SMS, authenticator app, or security questions.
- Recovery of a forgotten username or email address.
- Recovery of accounts with a lost or compromised email inbox (handled by support).
- Changing a password while already logged in.
- Social login / SSO password management.

## Constraints

- **Password policy:** shared by registration and recovery from rollout onward. Existing passwords remain valid for login. Require at least 12 characters; at least one uppercase letter, one lowercase letter, one number; must not match the current password or any of the last 5 passwords; must not appear in a versioned local known-breached password list. Existing users start with empty history. Each successful password replacement moves the current Argon2 hash into history and retains the five most recent previous hashes.
- **Token:** cryptographically random, at least 128 bits of entropy, stored hashed, single use, expires in 30 minutes.
- **Rate limits:** maximum 5 reset requests per email per hour; maximum 20 reset requests per IP per hour.
- All registered accounts can request recovery, including existing accounts without a verification flag. Redeeming the link proves control of the stored inbox. Bind it to the account and its email at issuance and invalidate it if the address changes.
- Registration, login and recovery use the existing Email value object's normalization and lookup rules. Preserve local-part case and normalize domain case. Send to the stored address. Existing case-distinct accounts retain distinct recovery destinations.
- Suspension, lockout and MFA are future identity features. Define their recovery behavior when they are introduced.
- **Link in email:** must use HTTPS and must not contain the user's email or other personal data.
- Prevent account enumeration: identical response content and similar response timing for known and unknown emails.
- Tokens must never be logged in plaintext.
- Reset pages must set `Referrer-Policy: no-referrer` and be excluded from caching.
- Protect request form with CAPTCHA or equivalent after repeated attempts.
- Password change notification must not include the password or token.
- Email content must warn users to contact support if they did not request the reset.
- Comply with applicable data protection requirements for storage of email addresses and audit logs.
| Category | Requirement |
|---|---|
| Performance | Reset request responds in under 2 seconds at p95; email dispatched within 1 minute. |
| Availability | Meets the same availability target as the login service. |
| Accessibility | WCAG 2.1 AA for all recovery screens. |
| Localization | Screens and emails support all currently supported locales. |
| Observability | Metrics and alerts for request volume, failure rate, email delivery failures, and rate-limit hits. |
| Compatibility | Supported desktop and mobile browsers; email renders in major clients. |

## Implementation dependencies
- Extend the identity repository across its in-memory, PostgreSQL and MongoDB adapters. Persist reset state, password history and a per-user session version. Existing accounts start at version zero.
- Issue and supersede links atomically per account. A suppressed request leaves the last issued link valid. On redemption, conditionally verify the current token, expiry and email, replace the hash, update history, consume the token, advance the session version and record the pending password-change notification in one commit. Failure leaves all of these unchanged.
- Registration and login record the current version in the Flask session. Every authenticated entry point checks it against the stored version. Treat existing cookies without a version as version zero. The application uses Flask sessions and has no refresh-token flow.
- Add transactional email delivery for reset links and change notifications. Persist pending work before acknowledging issuance or completion. Encrypt queued link material, restrict worker access and discard it after dispatch or expiry. Retry transient failures with backoff, suppress expired or superseded links on retry and alert on delivery failures. A notification delivery failure leaves a committed password change in effect.
- Extend Flask-Limiter with shared counters for the email and IP limits. Add structured audit events and delivery metrics. Exclude passwords, tokens and complete reset URLs from logs.
Deploy storage changes and session-version checks across all instances before enabling recovery. Provision the mail worker, sender, templates and breached-password list before exposing the login-page link. Successful recovery redirects to login.

## Open release decisions
Select the mail provider, support contact, breached-password dataset owner, delivery retry budget and audit retention period.

## Success Criteria

1. Valid email requests respect stored addresses and conceal account existence.
2. Only the current, unexpired link works once for its original account and address.
3. A matching policy-compliant password restores access and replaces the old password, including for legacy users.
4. Requests exceeding email or IP limits are throttled.
5. Completion revokes existing sessions and queues one change notification.
6. Pending email can be delivered after an outage without revealing account existence.
7. Recovery screens meet WCAG 2.1 AA.
- 70%+ of reset flows started are completed within 30 minutes.
- At least 40% reduction in password-related support tickets within 90 days of release.
- Zero confirmed account takeovers attributed to the recovery flow.
- Reset email delivery success rate above 99%.
