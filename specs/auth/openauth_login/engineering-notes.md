# OpenAuth login engineering notes

## S-001–002

The Gherkin configures Google as the provider fixture. The Flask auth blueprint in `backend/domain/identity/api/auth/routes.py` defines login, registration, current-user and logout routes. The proposed provider flow also needs authorization and callback handling.

## S-003–007

The `User` aggregate requires a `PasswordHash`. The PostgreSQL identity adapter declares `password_hash TEXT NOT NULL`, and both the PostgreSQL and MongoDB adapters expect a hash when saving and loading users. Credential-free provisioning requires the model and adapters to preserve an absent credential across a reload while continuing to support password registration.

`LoginUser` reads `user.password_hash.value` during password verification. For a reloaded OAuth-only account, this path needs to return its ordinary invalid-credentials response. Also exercise the email collision check against a reloaded password account.
