# Design Specification: THES-28 Project Management

## Architecture & Service Structure
All project service logic will live under `backend/domain/project/services/`:
- `create_project.py`
- `list_projects.py`
- `get_project.py`
- `rename_project.py`
- `edit_project_description.py`
- `remove_project_description.py`
- `delete_project.py`
- `transfer_project_ownership.py`

## Spec Review Resolutions (2026-11-08)

### Validation & Security Rules
- **X-2 (Membership Guard)**: Non-members and unknown IDs both return an identical `404` via `THES-183` guard (never `403`).
- **X-3 (ID Formatting)**: Malformed project ID returns `400`; well-formed ID with no matching record returns `404`.
- **P-1 (Role Model)**: Roles are constants: `owner`, `member`. Reject any other value on write.
- **P-3 (Name Uniqueness)**: Unique constraint on `(owner_id, lowercased, trimmed name)`. Duplicates raise `ProjectNameTaken` and return `409 PROJECT_NAME_TAKEN`.
- **P-5 (Trimming & Constraints)**: Trim name and reject empty string after trim (`400`). Description max length is 2,000 characters (`400` if exceeded).
- **X-4 (Pagination Scope)**: Returns full result set; no `limit` or `cursor` parameters in v1.

### Data Integrity & Cascade Rules
- **P-7 (Role Update Transaction)**: In a single database transaction, set target user to `owner` and previous owner to `member`. The target must already be a project member.
- **P-6 & S-6 (Cascading Deletion)**: Delete cascades in one DB transaction: manuscripts (with sections, revisions, and drafts), sources, conversations/exchanges, and memberships. After DB commit, invoke vector index adapter `delete_by_project` (idempotent) to clear all source index entries.
