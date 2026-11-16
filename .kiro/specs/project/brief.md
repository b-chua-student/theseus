# Brief: Project Management Context Setup
ID: THES-28
Owner: Arve
Date: 2026-11-14
Base SHA: f61d821

## Goal
Implement the project bounded context within the Hexagonal architecture backend to allow academic writers to organize manuscripts into projects.

## Users / Roles
- Academic Writer
- System Administrator

## In Scope
- Define project domain models, aggregates, and value objects under backend/domain/project/
- Create Flask API routes and request models for project management
- Wire in-memory and MongoDB adapters for project persistence

## Non-Goals
- Implementing manuscript version control or git-like branching
- Setting up AI research assistant queries

## Constraints
- Must comply with strict mypy type checking and ruff lint rules
- Dependencies must point inward following Hexagonal architecture ports-and-adapters design

## Known Touchpoints
- backend/domain/project/
- backend/api/routes.py

## Assumptions
- Project names must be unique per user account

## Open Questions
- Deferred: Should project deletion cascade to nested manuscripts? Deferred to future epic THES-29.

## Success Criteria
- The system successfully creates, reads, and updates project records via the API.
- All unit tests pass cleanly using in-memory adapters without a live database.

## Reference Links
- Jira Epic THES-28

- Author: Project Management Context (THES-28)
