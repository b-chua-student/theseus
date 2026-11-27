# DevOps Requirements Summary

**CSP221A – Engineering AI-Native Products**

DevOps requirements are primarily addressed in **Module 3 (CI/CD and DevOps)** and **Module 8 (Deployment, Operations, and Maintenance)**. The objective is to establish an automated, secure, measurable, and reliable software delivery process.

## 1. CI/CD Pipeline Requirements

| Requirement | Description |
|---|---|
| Continuous Integration | Automatically build and test changes through pull requests. |
| Continuous Deployment | Automatically deploy every successful merge to `main`. |
| PR Pipeline | Run dependency installation, linting, formatting, type checking, tests, and builds. |
| Production Pipeline | Build, migrate the database, deploy, perform smoke tests, and notify the team. |
| Quality Gates | Block merging when required checks fail. |
| Branch Protection | Require pull requests, passing checks, and at least one approval. |
| Pipeline Optimization | Use caching, parallelization, and fail-fast execution to reduce runtime. |

**Expected result:** A reviewed pull request can be merged and deployed to production without manual server intervention.

## 2. Environment and Security Requirements

- Separate local, preview/staging, and production environments.
- Store credentials in CI/CD or hosting secret stores.
- Use environment-specific API keys with appropriate permissions.
- Configure spending limits for non-production AI keys.
- Maintain `.env.example` without exposing credentials.
- Implement dependency auditing and secret scanning.
- Ensure database migrations are automated and backward compatible.

## 3. AI-Specific CI/CD Requirements

| Requirement | Description |
|---|---|
| Mocked AI Tests | Avoid paid LLM calls during routine CI tests. |
| AI Evaluations | Execute evaluation tests when prompts or AI logic change. |
| Live Smoke Tests | Schedule limited live AI tests to verify provider functionality. |
| Output Validation | Test AI response schemas rather than exact generated wording. |
| Model Versioning | Pin model and prompt versions to support reproducibility. |
| Cost Control | Monitor AI usage and enforce spending limits. |

## 4. Deployment and Reliability Requirements

- Deploy the application to a publicly accessible production URL.
- Implement automated post-deployment health checks and smoke tests.
- Maintain a documented rollback procedure.
- Rehearse and measure rollback execution.
- Implement uptime monitoring and actionable alerts.
- Provide an AI kill switch to disable problematic AI functionality.
- Maintain database backups and test restoration.
- Document incident response and recovery procedures.

**Expected result:** The application can detect failures, recover from unsuccessful deployments, and continue operating reliably.

## 5. DevOps Metrics

Track the four DORA metrics:

| Metric | Purpose |
|---|---|
| Deployment Frequency | Measures how often changes reach production. |
| Lead Time for Changes | Measures the time from merge to deployment. |
| Change Failure Rate | Measures the percentage of deployments causing failures. |
| Time to Restore | Measures recovery time after deployment failures. |

Maintain a pipeline optimization log documenting execution times, successful runs, and improvements.

## 6. Required Documentation and Deliverables

| Deliverable | Description |
|---|---|
| CI/CD Workflow Files | Automated PR and production deployment pipelines. |
| `PIPELINE.md` | Pipeline architecture, stages, execution, and configuration. |
| Metrics Log | Pipeline performance and DORA metrics. |
| Optimization Log | Before-and-after measurements of pipeline improvements. |
| `.env.example` | Required environment variables without secret values. |
| Deployment Runbook | Instructions for deploying and verifying releases. |
| Rollback Runbook | Documented recovery procedure for failed deployments. |
| Maintenance Plan | Procedures for dependencies, models, credentials, and backups. |
| Handover Documentation | Instructions enabling other developers to operate the system. |
| Release `v1.0.0` | Tagged production release with a changelog. |

## 7. Requirements by Sprint

| Sprint | DevOps Responsibilities |
|---|---|
| **Sprint 1** | Establish repository, protected main branch, environments, and initial live deployment. |
| **Sprint 2** | Implement CI/CD pipelines, branch protection, secret management, metrics, and `PIPELINE.md`. |
| **Sprint 3** | Integrate AI-aware testing and evaluation into the pipeline. |
| **Sprint 4** | Implement monitoring, rollback, incident response, maintenance, and release management. |
| **Demo Day** | Demonstrate automated deployment, production verification, and recovery capabilities. |

## 8. Demo Day Requirements

The DevOps Engineer should be prepared to demonstrate:

1. A pull request automatically triggering the CI pipeline.
2. A failed quality check preventing a merge.
3. A successful merge automatically deploying to production.
4. Production health checks and smoke tests.
5. Pipeline performance and DORA metrics.
6. A working rollback procedure.
7. An AI kill switch and failure recovery.
8. A tagged `v1.0.0` release with documentation.

## Key Takeaway

The primary DevOps requirement is a complete CI/CD workflow that automatically validates, deploys, monitors, and supports recovery of the application.

By the end of Sprint 2, automated deployment should be operational. By Sprint 4, the system should also have monitoring, rollback capabilities, maintenance procedures, and sufficient documentation for another developer to operate it.
