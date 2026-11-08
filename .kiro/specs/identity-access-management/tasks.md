# Tasks: Identity & Access Management
Use [requirements.md](requirements.md) for acceptance criteria and [design.md](design.md) for implementation. Checkboxes track this plan, not verified code completion. Jira base: https://theseus-inc.atlassian.net/browse/

## 1. Resolve and inspect
- [ ] Inspect existing identity services, routes, storage, handlers, and tests; reuse implementations.
- [ ] Confirm password rules, email validation/normalization, domain codes and validation details (R1, R2, R8).
- [ ] Resolve session backend/lifetime, logout Content-Type conflict, and deletion ownership assumption (THES-184/185; R4, R6, R9).
- [ ] Check THES-26 before implementing proposed THES-186; avoid duplicate routes.

## 2. Shared foundations
- [ ] THES-182: centralize error envelope; test 400/401/404/409/422/429/503 and Retry-After (R8).
- [ ] THES-184: configure cookie flags/dev override, account-ID-only session, JSON gate/415, and no state-changing GET; test approved lifetime (R9).

## 3. Registration — THES-2 / R1, R7
- [ ] THES-3: implement create_account with uniqueness, strength checks, Argon2, persistence.
- [ ] THES-4: implement register_user orchestration.
- [ ] THES-5: add validated POST /api/auth/register.
- [ ] THES-6: map EmailAlreadyRegistered -> 409 and WeakPassword -> 422.
- [ ] THES-7: establish session for automatic login.
- [ ] THES-8: apply 5/minute/IP limit.
- [ ] THES-9: test success, duplicate email, weak password, input limits, and rate limit.

## 4. Login — THES-10 / R2, R7
- [ ] THES-11: implement login_user with Argon2 verification and session creation.
- [ ] THES-12: add validated POST /api/auth/login.
- [ ] THES-13: map InvalidCredentials -> identical 401 for unknown email/wrong password.
- [ ] THES-14: apply 5/minute/IP limit.
- [ ] THES-15: test success, wrong password, unknown email, invalid input, and rate limit.

## 5. Current session — THES-16 / R3
- [ ] THES-17: implement get_account from session identity.
- [ ] THES-18: protect GET /api/auth/me with login_required.
- [ ] THES-19: test authenticated and unauthenticated fetches.

## 6. Logout — THES-20 / R4
- [ ] THES-21: implement session teardown in auth_service.py.
- [ ] THES-22: expose POST /api/auth/logout.
- [ ] THES-23: test cookie clearing, bodyless 204, and success without session.

## 7. Display name — THES-24 / R5
- [ ] THES-25: implement update_account for current account.
- [ ] THES-26 / THES-186: expose one validated, protected PATCH /api/auth/me after confirming proposed contract.
- [ ] THES-27: test persisted name, invalid length, and missing session.

## 8. Delete account — THES-185 / R6
- [ ] Implement protected DELETE /api/auth/me, account/membership removal, session clearing, and 204.
- [ ] After confirmation, block project owners with 409 ACCOUNT_OWNS_PROJECTS; reference THES-55/51 rather than implement their features here.
- [ ] Test success, missing session, confirmed ownership rule, and no partial deletion.

## Done
- [ ] Verify R1–R9, cookie/error contracts, and GET /api/auth/me after register/login/update/logout/delete.
- [ ] Run relevant existing tests and repository-required checks; record results.
- [ ] Resolve or retain explicitly labeled assumptions; keep changes within THES-1.

