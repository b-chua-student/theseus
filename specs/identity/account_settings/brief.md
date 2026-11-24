# Brief: Account settings

- ID: account-settings
- Owner: Unassigned in the source ticket
- Date: 2026-11-24
- Base SHA: 2bb7768

## Goal

Give signed-in Theseus users a place to view their account details and update their display name.

## Users / Roles

- Signed-in Theseus user managing their own account.

## In Scope

- View the current display name and email address.
- Save a valid display name and see it when reopening settings.

## Non-Goals

- Changes to email addresses and passwords are deferred pending a scope decision.

## Constraints

- Users can manage only their own account settings.

## Known Touchpoints

- The ticket identifies the Identity model as holding the display name and email address.

## Assumptions

- No additional assumptions.

## Open Questions

- Deferred: Email and password changes require a product decision on whether to include them.
- Deferred: Reauthentication for sensitive changes depends on which changes are supported.

## Success Criteria

1. Opening account settings shows the signed-in user's current display name and email address.
2. After the user saves a valid display name, reopening their settings shows the saved name.
3. A user cannot view or change another user's account settings.

## Reference Links

- [Source ticket (GitHub issue #124)](https://github.com/b-chua-student/theseus/issues/124)
- [Acceptance scenarios](gherkin.feature)
