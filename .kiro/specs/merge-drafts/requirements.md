# Requirements Document

## Introduction

Drafts are named branches of a manuscript's revision history (`backend/domain/revision_history`). Users can create, list, rename, delete and switch drafts, but cannot bring the work from one draft into another. The editor header (`frontend/src/components/editor/EditorHeader.svelte`) already renders a **Merge** button, which is permanently disabled and marked `TODO(API): MERGE`.

This feature adds a draft merge: the content of a source draft is combined into the current draft as one new revision. It spans the backend (domain, service, API endpoint, docs) and the frontend (enabling the button, a merge panel, conflict resolution).

Current model facts that shape these requirements:

- A manuscript snapshot is a tree of sections. Each section has a stable `id`, `parent_id`, `heading`, `ordinal` and `body`.
- A draft is a linear list of revisions. Creating a draft copies the revisions of `main` (same revision IDs), so two drafts share a common prefix of revisions.
- A revision has no parent pointers and no record of merges.

Merge semantics, decided in this document:

- **Direction**: the source draft is merged into the current draft (the target). The source draft is not changed.
- **Algorithm**: three-way merge at section and field granularity (`heading`, `body`, `parent_id`, `ordinal`). The base is the most recent revision common to both drafts, or the source head recorded by the last merge from the same source into the target, whichever is later in the target.
- **Conflicts**: the merge is never applied partially. If any conflict exists and the request does not resolve it, nothing is written and the conflicts are returned.
- **Result**: one new revision appended to the target draft, whose snapshot is the merged section tree, and the working copy is set to that snapshot.

## Glossary

- **Merge_Service**: The backend application service that merges one draft into another.
- **Merge_Engine**: The domain logic inside the RevisionHistory aggregate that computes a merged snapshot and its conflicts from a base, a target and a source snapshot.
- **Revision_History**: The existing aggregate that holds a manuscript's drafts and revisions.
- **Merge_API**: The HTTP endpoint `POST /api/projects/{p}/manuscripts/{m}/drafts/{name}/merge`, where `{name}` is the source draft.
- **Merge_Panel**: The frontend UI opened by the Merge button for choosing a source draft, reviewing conflicts and confirming.
- **Merge_Button**: The existing button labeled "Merge" in the editor header.
- **Editor**: The manuscript editing page that contains the editor header.
- **Source_Draft**: The draft whose changes are brought in. It is never modified by a merge.
- **Target_Draft**: The current draft. It receives the merge revision.
- **Base_Revision**: The revision used as the common ancestor for a three-way merge.
- **Section**: A node of the manuscript section tree with `id`, `parent_id`, `heading`, `ordinal` and `body`.
- **Field**: One of the four mergeable attributes of a Section: `heading`, `body`, `parent_id`, `ordinal`.
- **Conflict**: A Section Field (or Section existence) that both drafts changed relative to the Base_Revision in different ways.
- **Resolution**: A caller-supplied choice of `target` or `source` for one Conflict.
- **Merge_Revision**: The single revision appended to the Target_Draft by a successful merge.
- **Working_Copy**: The manuscript's editable content, which may hold uncommitted edits.
- **Unsaved_Changes**: A state in which the Working_Copy snapshot differs from the head snapshot of the current draft.

## Requirements

### Requirement 1: Merge a draft into the current draft

**User Story:** As a manuscript author, I want to merge another draft into the draft I am working on, so that I can combine alternative versions of my manuscript.

#### Acceptance Criteria

1. WHEN a merge is requested for a Source_Draft and the Revision_History exists, THE Merge_Service SHALL merge the Source_Draft head snapshot into the Target_Draft head snapshot.
2. WHEN a merge completes without unresolved Conflicts, THE Merge_Service SHALL append exactly one Merge_Revision to the Target_Draft.
3. WHEN a merge completes without unresolved Conflicts, THE Merge_Service SHALL leave the Source_Draft revisions unchanged in count, content, and order.
4. WHEN a merge completes without unresolved Conflicts, THE Merge_Service SHALL apply the Merge_Revision snapshot to the Working_Copy so that the Working_Copy content equals the Merge_Revision snapshot.
5. WHEN a merge completes without unresolved Conflicts, THE Merge_Service SHALL keep the Target_Draft as the current draft.
6. WHEN a merge request includes a message of 1 to 256 characters, THE Merge_Service SHALL use it as the Merge_Revision message.
7. WHEN a merge request includes no message, THE Merge_Service SHALL set the Merge_Revision message to "Merge draft '<source name>' into '<target name>'".
8. IF a merge request includes a message that is empty or longer than 256 characters, THEN THE Merge_Service SHALL return a revision error indicating the message length is invalid and write nothing.
9. IF the merge produces unresolved Conflicts, THEN THE Merge_Service SHALL return the unresolved Conflicts to the caller, append no Merge_Revision, and leave the Target_Draft revisions, Source_Draft revisions, and Working_Copy unchanged.
10. IF the Source_Draft does not exist, THEN THE Merge_Service SHALL return a revision error identifying the missing draft and write nothing.
11. IF the manuscript has no Revision_History, THEN THE Merge_Service SHALL return a history-not-found error and write nothing.
12. IF the Source_Draft is the Target_Draft, THEN THE Merge_Service SHALL return a revision error stating that a draft cannot be merged into itself and write nothing.

### Requirement 2: Determine the merge base

**User Story:** As a manuscript author, I want repeated merges from the same draft to include only new changes, so that I do not resolve the same conflicts twice.

#### Acceptance Criteria

1. WHEN a merge from a Source_Draft into a Target_Draft is requested, THE Merge_Engine SHALL select as the Base_Revision the most recent revision in the Target_Draft revision list, ordered by position in the Target_Draft history, whose revision ID also occurs in the Source_Draft revision list.
2. WHEN a merge from a Source_Draft into a Target_Draft is requested AND the Target_Draft contains one or more Merge_Revisions that recorded a source head revision ID occurring in the Source_Draft revision list, THE Merge_Engine SHALL select as the Base_Revision the recorded source head revision ID from the most recent such Merge_Revision, if that Merge_Revision is positioned later in the Target_Draft history than the common revision selected by criterion 1.
3. WHEN a Merge_Revision is created, THE Merge_Service SHALL record the Source_Draft name and the Source_Draft head revision ID on the Merge_Revision.
4. WHEN a Source_Draft is renamed after a merge, THE Merge_Engine SHALL match the recorded source head revision ID to the renamed draft and SHALL use the recorded Merge_Revision as a base candidate under criterion 2 when the renamed draft is the Source_Draft.
5. IF no revision common to both drafts exists AND no applicable Merge_Revision exists in the Target_Draft, THEN THE Merge_Service SHALL return a revision error indicating that the drafts share no history, create no Merge_Revision, and leave the Target_Draft and Source_Draft unchanged.
6. WHEN the same merge is computed twice against an unchanged Revision_History, THE Merge_Engine SHALL select the same Base_Revision both times.

### Requirement 3: Combine non-conflicting changes

**User Story:** As a manuscript author, I want changes made in different places to be combined automatically, so that I only handle real conflicts.

#### Acceptance Criteria

1. WHEN a Section Field changed only in the Source_Draft since the Base_Revision, THE Merge_Engine SHALL take the Source_Draft value for that Field in the merged snapshot.
2. WHEN a Section Field changed only in the Target_Draft since the Base_Revision, THE Merge_Engine SHALL keep the Target_Draft value for that Field in the merged snapshot.
3. WHEN a Section Field changed in both drafts to the same value since the Base_Revision, THE Merge_Engine SHALL keep that value in the merged snapshot and SHALL report zero Conflicts for that Field.
4. WHEN a Section exists in the Source_Draft and in neither the Base_Revision nor the Target_Draft, THE Merge_Engine SHALL add the Section with all of its Fields from the Source_Draft to the merged snapshot.
5. WHEN a Section exists in the Target_Draft and in neither the Base_Revision nor the Source_Draft, THE Merge_Engine SHALL keep the Section with all of its Fields in the merged snapshot.
6. WHEN a Section exists in the Base_Revision, is deleted in the Source_Draft and has no Field changes in the Target_Draft since the Base_Revision, THE Merge_Engine SHALL omit the Section from the merged snapshot.
7. WHEN a Section exists in the Base_Revision, is deleted in the Target_Draft and has no Field changes in the Source_Draft since the Base_Revision, THE Merge_Engine SHALL omit the Section from the merged snapshot.
8. WHEN a Section is added in both drafts with the same ID and identical Fields, THE Merge_Engine SHALL include exactly one copy of the Section in the merged snapshot and SHALL report zero Conflicts for that Section.
9. WHEN the merged snapshot is built, THE Merge_Engine SHALL renumber the `ordinal` values of the children of each parent to consecutive integers starting at 0, preserving the merged relative order and breaking ties by ascending Section ID.
10. WHEN the Source_Draft head snapshot equals the Base_Revision snapshot, THE Merge_Service SHALL return an error with code `revision.no_changes`, write no Revision, and leave the Target_Draft unchanged.
11. WHEN the merged snapshot equals the Target_Draft head snapshot, THE Merge_Service SHALL return an error with code `revision.no_changes`, write no Revision, and leave the Target_Draft unchanged.
12. FOR ALL snapshots S, merging a Source_Draft whose head equals the Base_Revision into a Target_Draft with head S SHALL yield S (identity property).
13. FOR ALL snapshots B and S, merging a Source_Draft with head S into a Target_Draft whose head equals the Base_Revision B SHALL yield S (fast-forward property).

### Requirement 4: Detect conflicts

**User Story:** As a manuscript author, I want the system to detect incompatible changes instead of silently overwriting my work, so that I never lose content in a merge.

#### Acceptance Criteria

1. IF a Section Field has a value in the Target_Draft that differs from its Base_Revision value, and has a value in the Source_Draft that differs from its Base_Revision value, and the Target_Draft value differs from the Source_Draft value, THEN THE Merge_Engine SHALL report one Conflict for that Section and Field identifying the Section ID, the Field, the Base_Revision value, the Target_Draft value and the Source_Draft value.
2. IF a Section was deleted in exactly one of the Target_Draft or the Source_Draft and any Field of that Section has a value that differs from its Base_Revision value in the other draft, THEN THE Merge_Engine SHALL report one Conflict for that Section identifying the Section ID and which draft (Target_Draft or Source_Draft) deleted it.
3. IF the merged Section tree would contain a cycle through `parent_id`, THEN THE Merge_Engine SHALL report one Conflict on the `parent_id` Field of each Section in that cycle whose `parent_id` differs between the Source_Draft and the Base_Revision, and SHALL NOT report a Conflict on any Section in the cycle whose `parent_id` is unchanged in the Source_Draft.
4. IF a merged Section would have a `parent_id` that references a Section ID absent from the merged snapshot, THEN THE Merge_Engine SHALL report one Conflict on the `parent_id` Field of that Section identifying the Section ID, the Field and the missing parent Section ID.
5. WHEN the merge contains one or more unresolved Conflicts, THE Merge_Service SHALL persist no changes (no new revision and no modification to either draft) and SHALL return every detected Conflict in a single response.
6. IF the merge contains one or more unresolved Conflicts, THEN THE Merge_API SHALL respond with HTTP status 409 and error code `revision.merge_conflict`, and the response SHALL contain the full list of Conflicts.
7. WHEN the same inputs are merged repeatedly, THE Merge_Engine SHALL return the same Conflicts in the same order, sorted ascending by Section ID and then ascending by Field name.
8. FOR ALL merges, THE Merge_Engine SHALL report no Conflict for a Section Field whose Target_Draft value equals its Source_Draft value, including when both values differ from the Base_Revision value.

### Requirement 5: Resolve conflicts

**User Story:** As a manuscript author, I want to choose which side wins for each conflict, so that I can complete the merge without editing both drafts by hand.

#### Acceptance Criteria

1. WHEN a merge request includes a Resolution of `target` for a Conflict, THE Merge_Engine SHALL use the Target_Draft value of the Conflict's Field for the Section identified by the Conflict's Section ID in the merged snapshot.
2. WHEN a merge request includes a Resolution of `source` for a Conflict, THE Merge_Engine SHALL use the Source_Draft value of the Conflict's Field for the Section identified by the Conflict's Section ID in the merged snapshot.
3. WHEN a Section deletion Conflict is resolved to the side that deleted the Section, THE Merge_Engine SHALL remove the Section and all of its descendant Sections from the merged snapshot.
4. WHEN a Section deletion Conflict is resolved to the side that kept the Section, THE Merge_Engine SHALL keep the Section and all of its descendant Sections in the merged snapshot, with every Field value taken from the side that kept the Section.
5. WHEN a merge request includes exactly one Resolution for every Conflict in the current Conflict set and the resolved snapshot has no new Conflict, THE Merge_Service SHALL complete the merge as in Requirement 1.
6. IF a Resolution refers to a Section ID and Field combination that is not in the current Conflict set, THEN THE Merge_API SHALL respond with HTTP status 422, return an error identifying the unmatched Section ID and Field, and leave the Target_Draft unchanged.
7. IF a Resolution has a value other than `target` or `source` (including empty or missing), THEN THE Merge_API SHALL respond with HTTP status 422, return an error identifying the invalid Resolution, and leave the Target_Draft unchanged.
8. IF a merge request contains Resolutions for fewer than all Conflicts in the current Conflict set, THEN THE Merge_Service SHALL return the remaining unresolved Conflicts in the format defined in Requirement 4 and leave the Target_Draft unchanged.
9. IF the resolved snapshot produces a new structural Conflict from Requirement 4 criterion 3 or 4, THEN THE Merge_Service SHALL return that Conflict in the format defined in Requirement 4 and leave the Target_Draft unchanged.
10. IF a merge request contains more than one Resolution for the same Section ID and Field combination, THEN THE Merge_API SHALL respond with HTTP status 422, return an error identifying the duplicated Section ID and Field, and leave the Target_Draft unchanged.

### Requirement 6: Protect uncommitted work

**User Story:** As a manuscript author, I want the merge to refuse to overwrite edits I have not saved, so that I never lose work.

#### Acceptance Criteria

1. IF Unsaved_Changes exist in the Working_Copy when a merge is requested, THEN THE Merge_Service SHALL reject the request with an error that has code `revision.unsaved_changes`, leave the Working_Copy content unchanged, and add zero revisions to the Target_Draft revision list.
2. IF the manuscript identified in a merge request does not exist, THEN THE Merge_Service SHALL reject the request with a not-found error that identifies the missing manuscript, and create zero Merge_Revisions and zero Working_Copy changes.
3. IF the Working_Copy cannot be updated after the Merge_Revision is computed, THEN THE Merge_Service SHALL return an error indicating the update failed, leave the Target_Draft revision list identical to its state before the request, and leave the Working_Copy content unchanged.
4. WHEN two merge requests for the same manuscript are in progress at the same time, THE Merge_Service SHALL complete exactly one request, reject the other with a conflict error, and add exactly one Merge_Revision to the Target_Draft revision list in total.
5. IF a merge request is rejected under criterion 4, THEN THE Merge_Service SHALL leave the Working_Copy and Target_Draft revision list in the state produced by the request that completed.

### Requirement 7: Merge API

**User Story:** As a frontend developer, I want a documented HTTP endpoint for merging drafts, so that the Editor can trigger a merge.

#### Acceptance Criteria

1. THE Merge_API SHALL accept `POST /api/projects/{p}/manuscripts/{m}/drafts/{name}/merge` with an optional body containing `message` (1 to 256 characters) and `resolutions` (a list of 0 to 1,000 objects, each with `section_id`, `field` and `choice`).
2. WHEN a merge succeeds, THE Merge_API SHALL respond with HTTP status 200 and the updated Target_Draft in the existing Draft response shape.
3. IF the request body fails validation, THEN THE Merge_API SHALL respond with HTTP status 422, return an error indicating each invalid field, and leave the Working_Copy and revision history unchanged. Validation failures include a `message` that is empty or longer than 256 characters, a `resolutions` entry missing `section_id`, `field` or `choice`, and a `choice` value that is not one of the choices defined for resolutions.
4. IF the caller lacks the access required to commit revisions to the manuscript, THEN THE Merge_API SHALL respond with the same HTTP status as the existing commit endpoint and leave the Working_Copy and revision history unchanged.
5. IF the Source_Draft or the manuscript history does not exist, THEN THE Merge_API SHALL respond with HTTP status 404, return an error indicating which of the two was not found, and leave the Working_Copy and revision history unchanged.
6. IF the merge fails with `revision.no_changes`, THEN THE Merge_API SHALL respond with HTTP status 409, return an error identifying `revision.no_changes`, and leave the Working_Copy and revision history unchanged.
7. IF the merge fails with `revision.unsaved_changes`, THEN THE Merge_API SHALL respond with HTTP status 409, return an error identifying `revision.unsaved_changes`, and leave the Working_Copy and revision history unchanged.
8. IF the merge has Conflicts that the supplied `resolutions` do not resolve, THEN THE Merge_API SHALL respond with HTTP status 409, return a list containing every unresolved Conflict, each with `section_id`, `section_heading`, `field`, `kind`, `base`, `target` and `source`, and leave the Working_Copy and revision history unchanged.
9. WHEN the merge changes the Working_Copy, THE Merge_Service SHALL publish exactly one manuscript-changed event, the same event that restoring a revision publishes, so that the assistant index is refreshed.
10. IF the merge does not change the Working_Copy, THEN THE Merge_Service SHALL publish no manuscript-changed event.
11. THE docs/api.md file SHALL document the Merge_API request, the success response, and every error response listed in this requirement.
12. THE docs/architecture.md file SHALL describe merge semantics in the "Version control model" section.

### Requirement 8: Merge button and panel in the Editor

**User Story:** As a manuscript author, I want a working Merge button in the editor header, so that I can merge drafts without leaving the Editor.

#### Acceptance Criteria

1. WHILE draft tracking has started, the manuscript has at least two drafts, and no draft operation is in progress, THE Merge_Button SHALL be enabled.
2. WHILE draft tracking has not started, THE Merge_Button SHALL be disabled and its title SHALL state that draft tracking has not started.
3. WHILE draft tracking has started and the manuscript has exactly one draft, THE Merge_Button SHALL be disabled and its title SHALL state that at least two drafts are required.
4. WHILE a draft operation is in progress, THE Merge_Button SHALL be disabled.
5. WHEN the user activates the enabled Merge_Button, THE Merge_Panel SHALL open within 500 ms and list every draft except the current draft as a selectable Source_Draft, with no Source_Draft selected by default.
6. WHILE the Merge_Panel is open, THE Merge_Panel SHALL display the current draft name as the merge target.
7. WHILE no Source_Draft is selected, THE Merge_Panel SHALL keep its confirm control disabled.
8. WHEN the user selects a Source_Draft and activates the confirm control, THE Merge_Panel SHALL send exactly one merge request to the Merge_API containing the Source_Draft and the Target_Draft.
9. WHILE a merge request is in progress, THE Merge_Panel SHALL disable its confirm control and show a progress indication.
10. WHEN the merge succeeds, THE Editor SHALL reload the manuscript content, close the Merge_Panel and show a notice naming the Source_Draft and Target_Draft.
11. WHILE the Editor has Unsaved_Changes, THE Merge_Panel SHALL show a message asking the user to save before merging and SHALL keep its confirm control disabled.
12. IF the Merge_API responds with `revision.no_changes`, THEN THE Merge_Panel SHALL show a message stating that the Source_Draft has nothing new to merge, keep the Merge_Panel open, keep the selection, and leave the manuscript content unchanged.
13. IF the Merge_API responds with any other error or the request fails to complete within 30 seconds, THEN THE Merge_Panel SHALL show an error message, keep the Merge_Panel open, keep the selection, re-enable the confirm control, and leave the manuscript content unchanged.
14. WHEN the user closes the Merge_Panel without confirming, THE Merge_Panel SHALL close and send no request.
15. THE Editor SHALL remove the `TODO(API): MERGE` comment and the "Merge is not implemented" title once the Merge_Button is enabled.

### Requirement 9: Conflict resolution UI

**User Story:** As a manuscript author, I want to see each conflict and pick a side, so that I can finish the merge in one place.

#### Acceptance Criteria

1. WHEN the Merge_API responds with `revision.merge_conflict`, THE Merge_Panel SHALL list each Conflict with the section heading, the Field, the Target_Draft value and the Source_Draft value, in the order the Merge_API returned the Conflicts.
2. WHEN Conflicts are listed, THE Merge_Panel SHALL offer exactly two mutually exclusive choices, `target` and `source`, for each Conflict, with neither choice selected.
3. WHILE one or more Conflicts have no choice selected, THE Merge_Panel SHALL keep the merge confirm control disabled and SHALL expose its disabled state to assistive technology.
4. WHEN every Conflict has a choice selected and the user activates the merge confirm control, THE Merge_Panel SHALL resend the merge request with exactly one Resolution per Conflict and SHALL disable the merge confirm control until the Merge_API responds.
5. IF the resent merge returns new Conflicts, THEN THE Merge_Panel SHALL replace the list with the new Conflicts, SHALL keep the previous choice for each Conflict that has the same section heading and Field as a new Conflict, and SHALL leave unselected every Conflict with no matching previous choice.
6. WHEN the user changes the Source_Draft selection, THE Merge_Panel SHALL discard all previous choices and Conflicts and SHALL show no Conflict list until the Merge_API next responds with `revision.merge_conflict`.
7. THE Merge_Panel SHALL allow every control, including each choice control and the merge confirm control, to be reached and operated using only the keyboard (Tab, Shift+Tab, Space and Enter), and SHALL give every choice control an accessible name containing the section heading and the Field.
8. WHEN the user presses the Escape key while the Merge_Panel is open, THE Merge_Panel SHALL close and SHALL discard all unsent choices.
9. IF the resent merge request fails with a network error or a non-conflict error response, THEN THE Merge_Panel SHALL remain open, SHALL retain all selected choices, SHALL show an error indication stating that the merge failed, and SHALL re-enable the merge confirm control.

### Requirement 10: Verification

**User Story:** As a maintainer, I want automated tests for the merge, so that data loss regressions are caught.

#### Acceptance Criteria

1. THE project SHALL include at least one unit test for the Merge_Engine for each acceptance criterion in Requirements 2 to 5, and each test SHALL name the requirement number and criterion number it covers.
2. THE project SHALL include a property-based test that runs at least 100 generated cases, where each case merges a draft into an unchanged copy of itself, and the test SHALL assert that the result is `revision.no_changes` and that Requirement 3 criteria 12 and 13 hold.
3. THE project SHALL include a property-based test that runs at least 100 generated cases, where each case merges generated drafts, and the test SHALL assert that the merged snapshot has unique Section IDs, no `parent_id` cycles, and `ordinal` values among siblings that are consecutive integers starting at 0.
4. THE project SHALL include a Merge_Service test that submits a merge with at least one unresolved Conflict and asserts that the Revision_History and the Working_Copy are identical to their pre-merge state and that the merge is rejected with a conflict error.
5. THE project SHALL include Merge_API tests with at least one test for each of HTTP status codes 200, 404, 409 and 422, and each test SHALL assert the returned status code.
6. THE project SHALL include a frontend test that asserts the Merge_Button is enabled in each state where Requirement 8 permits merging and disabled in each state where it does not.
7. THE project SHALL include a frontend test for the Merge_Panel conflict flow that asserts the following sequence: conflicts are displayed, a resolution is selected for every Conflict, and the merge is submitted only after all Conflicts are resolved.
8. IF any test required by criteria 1 to 7 fails, THEN THE project's automated test run SHALL exit with a non-zero status and report the name of each failing test.