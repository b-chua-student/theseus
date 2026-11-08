# Tasks: THES-28 Project Management

- [ ] THES-29: 2.1 Create a project
  - [ ] THES-30: Implement `create_project` service (initialize creator as owner member, enforce unique trimmed lowercased name per owner)
  - [ ] THES-31: Add `POST /api/projects` route with Pydantic model (`project_name` 1–50 chars)
  - [ ] THES-32: Add tests (creation success, unauthenticated, invalid name length, duplicate name 409)

- [ ] THES-33: 2.2 List my projects
  - [ ] THES-34: Implement `list_projects` service scoped to caller membership (full set, no pagination)
  - [ ] THES-35: Add `GET /api/projects` route returning members with (`id`, `display_name`, `email`, `role`)
  - [ ] THES-36: Add tests (lists only member projects, unauthenticated)

- [ ] THES-37: 2.3 View project details
  - [ ] THES-38: Implement `get_project` service returning `ProjectDetail` (owner + member emails and roles)
  - [ ] THES-39: Add `GET /api/projects/{p}` route with membership check
  - [ ] THES-40: Map `ProjectNotFound` and non-member access to identical `404` via THES-183 guard
  - [ ] THES-41: Add tests (member access, non-member 404, compare non-member vs unknown ID response equality, unauthenticated)

- [ ] THES-42: 2.4 Rename a project
  - [ ] THES-43: Implement `rename_project` service with ownership guard and per-owner name uniqueness check
  - [ ] THES-44: Add `PATCH /api/projects/{p}/name` route with Pydantic model
  - [ ] THES-45: Add tests (rename success, invalid length, duplicate name 409, not owner, not found, unauthenticated)

- [ ] THES-46: 2.5 Manage the project description
  - [ ] THES-47: Implement `edit_project_description` service (non-empty validation, max 2,000 chars)
  - [ ] THES-48: Implement `remove_project_description` service
  - [ ] THES-49: Add `PUT` and `DELETE /api/projects/{p}/description` routes
  - [ ] THES-50: Add tests (set, clear, blank rejected, >2,000 chars rejected, not owner, not found, unauthenticated)

- [ ] THES-51: 2.6 Delete a project
  - [ ] THES-52: Implement `delete_project` service with ownership guard, cascading cleanup, and `delete_by_project` adapter call
  - [ ] THES-53: Add `DELETE /api/projects/{p}` route
  - [ ] THES-54: Add tests (delete success, not owner, not found, unauthenticated, cascade behavior)

- [ ] THES-55: 2.7 Transfer project ownership
  - [ ] THES-56: Implement `transfer_project_ownership` service (target must be member, check name conflict 409, update target to owner & prev to member in single transaction)
  - [ ] THES-57: Add `PATCH /api/projects/{p}/owner` route with Pydantic model (`new_owner_id`)
  - [ ] THES-58: Add tests (transfer success, target not member, name conflict 409, not owner, not found, unauthenticated)
