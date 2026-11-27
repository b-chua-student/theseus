# Theseus test authoring

Use this context when asked to create tests for Theseus. Read the requested behavior, the implementation, and nearby tests before editing. Check the working tree and preserve existing changes.

## Feature specs

- For spec-driven work, use the approved scenarios in the feature's `gherkin.feature` and the verification tasks in `tasks.md`. Match each `S-###` in the task table to the corresponding `@S-###` tag.
- For spec-driven work, use the approved Gherkin outcomes as the source for test assertions. Create and run the scenario tests before changing application code, then verify that every scenario is covered by passing tests after implementation. Use the task's references for component context, as described in [AGENTS.md](../AGENTS.md).

## Scope

- Change only test files and test support needed by those tests, such as fixtures, test data, or test-runner configuration.
- Leave application code, production dependencies, CI workflows, and deployment configuration outside the change. If a test exposes an application bug, report the failing behavior and the test that reproduces it.
- Cover the requested behavior and relevant edge cases. For a regression, exercise the failing path through the entry point where the bug occurs.

## Choose the test type

| Type | What to exercise | Theseus example |
| --- | --- | --- |
| Unit | A behavior in isolation. Use fakes for dependencies outside the behavior being tested. | Call `CreateProject` with an in-memory repository and check the result. |
| Integration | Real components working together across a boundary. Other dependencies may use fakes. | Send a request through Flask's test client to exercise routing and validation, or round-trip a source through the MongoDB repository. |
| End-to-end | A user workflow through the running frontend and backend with test persistence. | Sign in, upload a text source, reload the page, and verify that the source remains visible. |

## Backend

- Put backend pytest files under `backend/tests/` and domain tests under `backend/tests/domain/<context>/`. Match the layout already used by that domain.
  - For `assistant`, `identity`, `manuscript`, `revision_history`, and `src_lib`, put tests alongside related tests in layer directories such as `models/`, `services/`, `infrastructure/adapters/`, or `api/`.
  - `project` groups tests by layer in files at the domain root, such as `test_models.py` and `test_api.py`.
- Name files `test_*.py` and test functions `test_<behavior>`. Reuse existing fixtures and in-memory adapters. Keep new fixtures in the test module unless several modules need them, then use their nearest shared `conftest.py`.
- Use `@pytest.mark.integration` on new integration tests and register the marker under `[tool.pytest.ini_options]` in the root `pyproject.toml` when first needed. pytest supports marking a whole module with `pytestmark = pytest.mark.integration` when every test in the file belongs to that stage.
- For live MongoDB tests, follow the existing test database configuration and fixture cleanup. Give concurrently running tests isolated data. Report dependency-related skips when summarizing verification.

## Frontend

- Colocate tests with the code they exercise under `frontend/src/`.
- Use `*.test.js` for Node's test runner and `*.spec.js` for Vitest. Check the neighboring suite when choosing a runner. A suffix selects the runner and can cover either unit or integration behavior.
- Reuse the existing Svelte Testing Library setup. Select controls by accessible role and name where practical and assert outcomes a user can observe.

## End-to-end

- Put browser workflows that span the running frontend and backend under a top-level `e2e/` directory when introducing that suite. Use an existing browser runner if one has been configured.
- Use isolated test accounts and data. Check the workflow through the UI and use assertions that wait for application state to settle.
- For pytest, apply `@pytest.mark.e2e` to each end-to-end test or set `pytestmark = pytest.mark.e2e` for an end-to-end-only module. Register `e2e` under `[tool.pytest.ini_options]` in `pyproject.toml`. Use `e2e` as the sole stage marker for these tests.
- If using Playwright, add the `@end-to-end` tag with `{ tag: '@end-to-end' }` in the test or suite declaration. Select tagged tests with `npx playwright test --grep @end-to-end` from the directory containing the Playwright config.

## Run and report

- Run the new or changed tests first, then the nearby suite when feasible. From the repository root, use `pytest backend/tests/path/to/test_file.py` for a backend file, `npm --prefix frontend test` for Node tests, or `npm --prefix frontend run test:components` for Vitest.
- For CI selection, run unit, integration, then end-to-end stages. From the repository root, run `pytest -m "not integration and not e2e"` for unit tests and `pytest -m integration` for integration tests once all existing tests have been classified. For pytest-based end-to-end tests in the top-level directory, run `pytest e2e/ -m e2e`. The current pytest configuration discovers `backend/tests/` by default. Untagged tests pass the unit filter, so check existing coverage before relying on it as a CI gate.
- Report the test files changed, what behavior they cover, the commands run, and any failures, skips, or verification blocked by missing dependencies.

## AI release checks

Use test adapters and mock provider calls in routine checks. Assert schema, required fields, validation status, and error behavior. Keep exact wording assertions for application-owned messages.

For prompt or AI logic changes, run the affected offline tests and record evaluation evidence. The [live evaluator](../scripts/eval_combined_context.py) uses Gemini and synthetic inputs. Use a scoped test key with a spending limit and record the model, prompt revision, and results. A scheduled live provider smoke test and its budget still need evidence. See the [AI feature write-up](ai-feature.md).
