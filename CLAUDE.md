# CLAUDE.md — MeritTrack Admissions & Transaction Operations

## Stack (non-negotiable)
- **Frontend:** Vue 3 + TypeScript + Vite + Vue Router + Pinia + Vitest + Playwright + IndexedDB offline queue
- **Backend:** Python 3.10.x + FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic + PostgreSQL 14+
- **Auth:** Local username/password only — NO Google, Microsoft, campus SSO, or any external IdP
- **Storage:** PostgreSQL for relational state; local mounted directories for documents, exports, logs, forecasting snapshots

## Repository Contract (enforce strictly)
```
TASK-2/
├── docs/               ← design.md, api-spec.md, questions.md, requirement-traceability.md, test-traceability.md
├── repo/
│   ├── README.md
│   ├── docker-compose.yml
│   ├── run_tests.sh
│   ├── frontend/       ← Dockerfile, src/, public/, unit_tests/
│   └── backend/        ← Dockerfile, src/, database/, unit_tests/, api_tests/
├── sessions/           ← DO NOT TOUCH
├── execution_plan.md
└── metadata.json
```
- `docs/questions.md` is the **only** ambiguity log — keep it inside `docs/`
- Do NOT create root-level `unit_tests/` or `API_tests/`
- Do NOT rename `run_tests.sh`
- Do NOT create or modify anything inside `sessions/`
- Do NOT create session traces, bugfix logs, trajectory files, or review scratchpads

## Folder Structure Rules
- Frontend tests: `repo/frontend/unit_tests/` (browser workflow tests nest here too)
- Backend unit tests: `repo/backend/unit_tests/`
- Backend API/integration tests: `repo/backend/api_tests/`
- Browser workflow tests: nested under `repo/frontend/unit_tests/`

## Architecture Rules
- No god files, no god components, no god routers
- Layered: frontend (views/components/stores/composables/service adapters) vs backend (routers/schemas/services/domain/persistence/security/workers/telemetry)
- Real business logic in code — not comments, TODOs, or fake-success placeholders
- PostgreSQL transactions + explicit locking for state-machine integrity
- Centralized config — no hardcoded absolute paths, no undeclared env vars

## Security Invariants (enforce in code and tests)
- **Password:** min 12 chars, Argon2id adaptive salted hashing, never plaintext
- **JWT:** 15-minute access tokens + refresh token handling
- **Request signing:** device-bound API signing + 5-minute server-stored nonce window (anti-replay)
- **SSO:** internal identity provider only — zero external dependencies
- **RBAC:** route-level + function-level + object-level + row/column-level
- **Sensitive fields:** masked by default (e.g., SSN → last 4 digits); restricted document downloads to approved roles
- **Watermarking:** every export and downloaded PDF watermarked with username + timestamp
- **SHA-256:** verify on upload AND download
- **Envelope encryption:** sensitive data at rest, locally managed keys
- **HTTPS:** end-to-end using locally provisioned certificates
- **Logs:** never leak passwords, keys, signatures, unmasked PII, or decrypted payloads

## Business Invariants (enforce in state machine + tests)
- **Order states:** pending_payment → pending_fulfillment → pending_receipt → completed | canceled | refund_in_progress → refunded
- **Auto-cancel:** 30-minute inactivity at pending_payment; atomic rollback of capacity/slots if configured
- **Bargaining:** max 3 candidate offers within 48 hours; reviewer may counter once; then reverts to fixed-price or expires
- **After-sales:** within 14 days of completion only
- **Attendance exceptions:** proof upload + routed review + immutable approval trail
- **Document versioning:** resubmissions version, never overwrite reviewed files
- **File validation:** PDF/JPG/PNG only, 25 MB per-file limit, SHA-256 on upload/download

## Timestamp Rule
- Store all timestamps in UTC/ISO on backend
- Display all timestamps in 12-hour format in frontend UI only

## Observability (all local, no external services)
- Unified structured logs + Prometheus-style metrics + OpenTelemetry-style trace correlation
- Critical flows: login, upload, order state transitions, appeal approvals
- Local config center: feature flags (bargaining on/off, rollback on/off), cohort-based canary routing
- Capacity/bandwidth forecasting from historical request-volume and document-size data
- Cache hit-rate reporting from local access logs

## Deployment
- Single local HTTPS deployment serving compiled frontend assets from same FastAPI boundary
- `docker-compose.yml` must be complete and runnable with `docker compose up`
- `run_tests.sh` must be docker-first and truthful
- Do NOT run Docker or tests during implementation prompts

## Documentation Rules
- `repo/README.md`: real behavior, real commands, real services, real ports, real storage paths, real test entry points
- `docs/design.md`, `docs/api-spec.md`, `docs/requirement-traceability.md`, `docs/test-traceability.md`: kept synchronized
- `docs/questions.md`: every blocker-level ambiguity logged with The Gap / The Interpretation / Proposed Implementation
- Endpoint inventory: unique `METHOD + fully resolved PATH` entries
- Test traceability: distinguish no-mock HTTP/API tests from mocked or non-HTTP tests
- Every single endpoint must have test coverage

## What NOT to Do
- No external CDN, cloud storage, hosted payment providers, or third-party identity providers
- No mock-only frontend or backend-only delivery
- No simplified substitutes for bargaining, watermarking, hash verification, signing, encryption, canary routing, or forecasting
- No undocumented shortcuts
- No parallel subagents in plan mode or agent mode(CRITICAL)
- No session artifacts, trajectory files, or scratchpad documents

## When in plan mode AND when implementing a plan(this also applies to non-planned implementations)
- Always explicitly include the first two lines of each prompt given, objective and exact scope,contextual self check, Explicit constraints and completion criteria, make all of these copy pasted exactly into the plan document.
- DONT RUN PARALLEL SUBAGENTS ALL EXPLORATION (ONLY RELEVANT CODE) AND IMPLEMENTATION MUST BE DONE SEQUENTIALLY BY THE MAIN AGENT
