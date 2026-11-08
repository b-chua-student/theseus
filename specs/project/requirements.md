# Requirements: THES-28 Project Management

## Overview
Let users organize their writing into projects. A project has a name, an optional description, a set of members, and an owner.

## Scope
### In Scope
- Project CRUD (Create, Read, List, Delete)
- Renaming and description management
- Member listing (owner + collaborators) in project detail
- Ownership transfer

### Out of Scope
- Inviting/adding members by email
- Per-member role assignment beyond owner/member
- Project-level permissions/granular sharing
- Pagination (no limit/cursor in v1)

## Functional Requirements & Acceptance Criteria

### THES-29: Create a Project
- **AC-1**: Given a valid session and a `project_name` (1–50 chars), `POST /api/projects` returns `201` and creates project with caller as owner.
- **AC-2**: Given no session, returns `401`.
- **AC-3**: Given a name outside 1–50 chars (or empty after trimming), returns `400` with validation details.
- **AC-4**: Given a duplicate project name for the same owner (lowercased, trimmed), raises `ProjectNameTaken` and returns `409 PROJECT_NAME_TAKEN`.
