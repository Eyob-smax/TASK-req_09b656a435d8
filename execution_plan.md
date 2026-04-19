# General Instructions

Treat this project as a **full-stack offline-ready admissions and transaction operations web platform**: a Vue.js browser client in `repo/frontend/`, a FastAPI backend in `repo/backend/`, PostgreSQL as the primary transactional store, and local filesystem-backed storage for uploads, exports, watermarked PDFs, and operational logs. Keep the product fully functional inside a disconnected facility network with **no dependence on internet services, hosted payment providers, cloud storage, third-party identity providers, external CDNs, local modules or externally managed observability services**. Build the Vue application in `repo/frontend/`, but keep the production runtime as a **single local HTTPS deployment** that can serve the compiled frontend assets from the same deployment boundary as the FastAPI application unless a later prompt proves a separate static runtime is genuinely required and fully justified. Do not drift into a mock-only frontend, a backend-only delivery, or an architecture that weakens offline operation.

Use **stable, production-ready defaults** where the prompt is silent, and keep those defaults explicit everywhere:
- **Frontend:** Vue 3, TypeScript, Vite, Vue Router, Pinia, Vue Test Utils, Vitest, Playwright, IndexedDB-backed offline queue/cache support, and a service worker only where it materially improves offline asset caching or resumable upload recovery.
- **Backend:** Python 3.10.x, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL driver support, local background worker/scheduler primitives backed by PostgreSQL, structured logging, OpenTelemetry-style trace correlation, and Prometheus-style metrics exposure or equivalent local metrics capture without adding unjustified infrastructure.
- **Database:** PostgreSQL 14+.
- **Storage model:** PostgreSQL for relational state, local mounted directories for documents, generated exports, access logs, and forecasting snapshots, with metadata, hashes, audit trails, and retention policies tracked in the database.
- **Containerization:** `repo/docker-compose.yml`, `repo/frontend/Dockerfile`, and `repo/backend/Dockerfile`, with no undeclared host dependencies and no hidden setup steps.
- **Testing:** Frontend unit and browser workflow tests inside `repo/frontend/unit_tests/`; backend unit tests inside `repo/backend/unit_tests/`; backend API/integration tests inside `repo/backend/api_tests/`; `repo/run_tests.sh` must orchestrate the suites in a **docker-first** way without actually being run during these prompts.

Honor this repository contract exactly:
```text
TASK-2/
├── docs/
│   ├── design.md
│   ├── api-spec.md
│   ├── questions.md
│   ├── requirement-traceability.md
│   ├── test-traceability.md
│   └── ...
├── repo/
│   ├── README.md
│   ├── docker-compose.yml
│   ├── run_tests.sh
│   ├── frontend/
│   │   ├── Dockerfile
│   │   ├── src/
│   │   ├── public/
│   │   ├── unit_tests/
│   │   └── ...
│   └── backend/
│       ├── Dockerfile
│       ├── src/
│       ├── database/
│       ├── unit_tests/
│       ├── api_tests/
│       └── ...
├── sessions/                  # exists but must not be touched
├── prompt.md                  # already exists / original prompt source file(leave it if it doesnt exist its not that important)
├── execution_plan.md
└── metadata.json
```
`docs/questions.md` is the only ambiguity log for this project and must stay inside `docs/`. Do not create root-level `unit_tests/` or root-level `API_tests/`. Do not rename `run_tests.sh`. Do not create or modify anything inside `sessions/`. Do not create session traces, bugfix logs, trajectory files, review scratchpads, or any other session-style artifacts.

Create project-specific Claude memory before Prompt 1. Keep that project memory brief and limited to critical anti-drift reminders for this repository only. Create project-specific `CLAUDE.md` rules for this repository before Prompt 1. Place both in the repository’s Claude project context. Keep both project-scoped, not user-level. Lock those project rules to: the Vue + FastAPI + PostgreSQL stack; the strict `docs/` + `repo/` folder contract; `docs/questions.md` as the ambiguity log; offline-only operation; local HTTPS certificates; internal identity provider behavior; 15-minute JWT + refresh behavior; request-signature + nonce anti-replay rules; envelope encryption expectations; watermarking and SHA-256 verification requirements; order-state-machine invariants; immutable auditability; feature-flag and cohort-routing requirements; requirement-to-module traceability; requirement-to-test traceability; README and documentation honesty; and the ban on running Docker or tests yet. After creating the project memory and `CLAUDE.md`, output their contents for user review before proceeding with implementation work. Do not output their literal contents inside this plan(this plan is eneditable). Put explicitly parallel subagents are prohibited in plan mode nor agent mode. Exploration(only relevant codes) and implementation should be done by the main agent seqentially.

Architecture standards are non-negotiable:
- Keep the system modular and layered. Do not create god files, god components, god routers, or controller/service/repository pileups.
- Separate frontend views/components/stores/composables/service adapters from backend routers/schemas/services/domain rules/persistence/security/workers/telemetry modules.
- Keep real business logic in code, not in comments, TODO markers, or fake-success placeholders.
- Keep order state transitions, document review trails, refund handling, appeals, and config changes auditable and traceable.
- Use PostgreSQL transactions and explicit locking or concurrency-safe patterns where state-machine integrity matters.
- Centralize configuration. Avoid absolute local paths, undeclared environment variables, and host-only assumptions.
- Remove junk files, dead commented blocks, noisy debug prints, and duplicate placeholder assets before completion.
- Keep timestamp storage canonical in UTC/ISO form on the backend and render 12-hour display formatting in the frontend UI only.

Functional fidelity is mandatory. By the end of Prompt 10, implement the prompt’s explicit requirements truthfully, including at minimum:
- candidate profiles with application details, initial exam scores, transfer preferences, and role-appropriate editing/viewing flows;
- required-document upload and review with accepted file-type feedback for PDF/JPG/PNG, a 25 MB per-file limit, checklist completion tracking, versioned resubmissions, and visible statuses including “Needs resubmission” with a reason;
- fee-based service ordering in both fixed-price and bargaining modes, with up to three offers in 48 hours, one reviewer counter at most, explicit fallback or expiry handling, and a real backend order state machine;
- order timelines shown with 12-hour timestamps and states including pending payment, pending fulfillment, pending receipt, completed, canceled, refund in progress, and refunded;
- 30-minute pending-payment auto-cancel with clear UI banners and atomic rollback of capacity-limited slots or inventory when configured;
- after-sales service requests permitted within 14 days of completion;
- attendance exceptions for missed check-ins or late arrivals, proof uploads, routed review decisions, immutable approval trails, and searchable adjudication outcomes;
- staff/reviewer queues for order confirmation, voucher issuance, internal milestone updates, and appeal adjudication with consistent searchable statuses;
- FastAPI-backed validation and transactional guarantees for auto-cancel, refunds, rollback, and other state transitions;
- local username/password authentication with a minimum 12-character password policy, adaptive salted hashing, 15-minute JWT sessions, refresh-token handling, and an internal identity provider for SSO with no external dependencies;
- device-bound anti-replay request signing with a server-stored 5-minute nonce window;
- fine-grained RBAC plus row-level and column-level controls, masked sensitive fields by default, restricted document-download authorization, and role-safe UI exposure;
- watermarking for every export and downloaded PDF with username and timestamp, plus SHA-256 verification on upload and download;
- envelope encryption for sensitive data with locally managed keys;
- end-to-end HTTPS using locally provisioned certificates;
- unified structured logs, metrics, and traces for critical flows including login, upload, order state changes, and appeal approvals;
- a local config center with feature flags such as bargaining on/off and rollback on/off;
- canary release routing by user cohort implemented locally rather than through external traffic-management products;
- capacity and bandwidth forecasting using historical request-volume and document-size data;
- offline cache policy controls for static assets served by the same deployment, including cache hit-rate reporting from local access logs.
Do not replace any of these with simplified substitutes or undocumented shortcuts.

Security and validation must be designed early and enforced throughout:
- Enforce local auth only. Do not introduce Google, Microsoft, campus SSO, or any external IdP.
- Use adaptive salted password hashing such as Argon2id or equivalent. Never store plaintext passwords.
- Enforce route-level, function-level, object-level, and row/column-level access controls where relevant.
- Treat Candidates, Proctors/Teachers, Admissions Reviewers, and System Administrators as distinct role boundaries.
- Validate all body, query, path, header, file, and pagination inputs, including bargaining limits, document types, file sizes, after-sales windows, nonce freshness, and cohort-rule updates.
- Keep request-signature verification, nonce replay protection, watermarking, file-hash verification, and encryption responsibilities explicit and testable.
- Keep logs and error responses secret-safe. Never leak raw passwords, keys, signatures, unmasked PII, or decrypted sensitive payloads.
- Restrict document downloads and sensitive exports to approved roles only. Do not rely on frontend gating alone.

Data, files, and operational behavior must remain explicit:
- Store upload/export metadata, checksum values, audit records, order histories, offer histories, reviewer decisions, feature-flag history, cohort-routing rules, and forecasting outputs in inspectable persistence layers.
- Version candidate document submissions instead of overwriting prior reviewed files.
- Keep immutable approval and audit trails for attendance exceptions, order approvals, refund actions, feature-flag changes, and sensitive download/export actions.
- Keep local filesystem paths configurable and documented. Do not bake developer machine paths into code, Docker assets, or docs.
- Serve static assets with explicit cache policies and local access logging so cache hit-rate reporting can be derived from real logs.
- Implement canary behavior as a local cohort-assignment and config-resolution system, not as an external SaaS release platform.

Frontend expectations remain first-class because this is a full-stack product:
- Provide coherent role-aware navigation for Candidate, Proctor/Teacher, Admissions Reviewer, and System Administrator experiences.
- Show clear loading, empty, error, success, conflict, submitting, disabled, and retry states anywhere the core user journey depends on them.
- Make offline/pending/retry/conflict feedback visible and actionable. Do not silently drop queued actions.
- Keep sensitive fields masked by default in lists, details, exports, and previews unless the current role and workflow explicitly allow more detail.
- Keep 12-hour timestamp display consistent across order timelines, review decisions, queue histories, and notifications.

Documentation discipline is mandatory:
- Create `repo/README.md` early and keep it truthful throughout.
- Keep README limited to real behavior, real commands, real services, real ports, real storage paths, real test entry points, and real verification steps.
- Keep `docs/design.md`, `docs/api-spec.md`, `docs/questions.md`, `docs/requirement-traceability.md`, and `docs/test-traceability.md` synchronized with the implementation.
- Maintain requirement-to-module and requirement-to-test traceability throughout all prompts.
- Record every blocker-level or implementation-shaping ambiguity in `docs/questions.md` using `The Gap`, `The Interpretation`, and `Proposed Implementation`.
- Do not promise runtime success from documentation alone.

Docker and tests are readiness work only in this execution plan:
- Do not run Docker.
- Do not run the app.
- Do not run tests.
- Do not claim runtime success from documentation alone.
Author everything so later reviewers can execute `docker compose up` and `repo/run_tests.sh` without rewriting code or guessing configuration, but keep these prompts strictly in implementation + static-verification mode.

Shape the repository from day one for later static acceptance review:
- Keep documentation, code structure, routing, schemas, security boundaries, and test placement easy to audit statically.
- Keep endpoint definitions, request/response shapes, and test intent obvious from the source tree.
- Maintain an endpoint inventory using unique `METHOD + fully resolved PATH` entries once backend routes exist.
- Distinguish true no-mock HTTP/API coverage from mocked HTTP tests or non-HTTP unit tests.
- Keep frontend and backend test readiness balanced. Do not let a complex UI ship with negligible frontend tests.
- Keep `repo/run_tests.sh` aligned to the real repository structure and a docker-first execution model.

Stay laser-focused on the current prompt by default. When the user intentionally pairs prompts together, execute both prompts in sequence without blurring them into one scope blob. Preserve each prompt’s detail, traceability duties, documentation duties, and completion criteria while carrying them out in order. Treat pairing as a user convenience, not as permission to simplify, merge away, or weaken either prompt.

# Self-Test Acceptance Criteria

1. **Documentation and static verifiability**
   - Create clear startup, configuration, verification, and test instructions that match the repository exactly.
   - Keep documented entry points, service names, ports, storage paths, Docker assets, and test locations statically consistent.
   - Make the repository inspectable without requiring a reviewer to rewrite core code or guess missing setup.

2. **No material deviation from the Original Prompt**
   - Stay centered on admissions onboarding, attendance exceptions, fee-based ordering, bargaining, reviewer queues, security, observability, and offline-ready operation.
   - Do not weaken bargaining rules, watermarking, hash verification, signing, envelope encryption, cohort-based canary routing, or forecasting into toy substitutes.
   - Do not drift into a generic CRM, generic file manager, or generic e-commerce admin.

3. **Delivery completeness**
   - Deliver a real engineered product structure, not snippets, isolated screens, or placeholder routers.
   - Implement real state handling, persistence, validation, auditability, retry behavior, and policy enforcement.
   - Keep core docs present and synchronized throughout the build.

4. **Engineering structure and maintainability**
   - Keep module boundaries clear and layered across frontend, backend, database, security, workers, telemetry, and documentation.
   - Avoid giant files, chaotic coupling, dead scaffolding, and undocumented configuration behavior.
   - Keep the code extensible enough to support future admissions-service variants and policy changes without rewrites.

5. **Professional engineering details**
   - Enforce validation, structured error handling, meaningful logs, trace correlation, consistent API envelopes, and user-safe failure handling.
   - Keep frontend feedback states and backend failure responses credible for real operations staff and candidates.
   - Protect sensitive data in logs, responses, downloads, exports, and caches.

6. **Prompt understanding and implicit-constraint fit**
   - Model the real business boundaries of document review, bargaining windows, refund rollback, attendance exception routing, reviewer adjudication, and internal-only operations.
   - Make implicit rules explicit, especially around queue ownership, status transitions, timing windows, offline retries, watermark scope, and cohort routing.

7. **Testing readiness and coverage discipline**
   - Create frontend unit tests, backend unit tests, backend API/integration tests, and frontend browser workflow coverage where the UI is critical.
   - Keep tests inside `repo/frontend/unit_tests/`, `repo/backend/unit_tests/`, and `repo/backend/api_tests/`, with browser workflow tests nested under `repo/frontend/unit_tests/` rather than in a separate root folder.
   - Maintain requirement-to-test traceability and endpoint-to-test traceability using fully resolved `METHOD + PATH` entries.
   - Distinguish true no-mock HTTP/API tests from mock-heavy HTTP tests and non-HTTP unit/integration tests. Do not over-count mocked transport coverage as real endpoint coverage.
   - Cover happy paths, validation failures, unauthorized and forbidden access, not-found cases, conflicts, idempotency, state transitions, security boundaries, and prompt-specific invariants.
   - Keep frontend and backend test readiness balanced. Frontend unit tests must be visibly present through real test files, not inferred from package manifests alone.
   - Keep `repo/run_tests.sh` docker-first and truthful.
    - Do not rely on mock API tests as acceptance-grade substitutes for backend API/integration coverage on critical routes. No-mock tests should be dominant over mock tests. every single endpoint must have test coverage.

8. **Security priority**
   - Treat authentication, internal SSO, request signing, nonce replay defense, RBAC, row/column-level restrictions, approved-role downloads, encryption, watermarking, hashing, and secret-safe logging as high-priority review areas.
   - Keep these controls explicit in code, docs, and tests rather than implying them through comments or UI behavior.

9. **Full-stack UI and interaction credibility**
   - Provide a connected application shape with differentiated functional areas, role-aware navigation, visible interaction feedback, and policy-safe data presentation.
   - Make upload limits, document statuses, order banners, timers, review outcomes, and conflict states visible in the UI.
   - Avoid a superficially polished UI that does not close the underlying workflow.

10. **Final static audit awareness**
    - Make Prompt 10 perform a rigorous static sweep of repo structure, requirement coverage, business invariants, security boundaries, endpoint inventory, test placement, test sufficiency, Docker/service/port consistency, documentation honesty, and unresolved assumptions in `docs/questions.md`.
    - End the final prompt by telling the user to invoke the separate execution-plan reviewer workflow for an independent post-plan review, without attempting that review inside the implementation workflow.

# Original Prompt

Create a MeritTrack Admissions & Transaction Operations platform that unifies candidate onboarding, exam attendance exceptions, and fee-based ordering into one offline-ready experience. Users include Candidates, Proctors/Teachers, Admissions Reviewers, and System Administrators. In the Vue.js web interface, Candidates maintain a profile with application details, initial exam scores, and transfer preferences, and upload required documents with immediate feedback on accepted formats (PDF/JPG/PNG), a 25 MB per-file limit, required document checklist completion, and visible status such as “Needs resubmission” with a reason. For fee-based services (for example, an application review package or transcript evaluation), Candidates can place orders in either fixed-price mode (configured per item) or bargaining mode where they can submit up to three offers within 48 hours; the Reviewer can accept one offer or counter once, after which the order reverts to fixed-price or expires. The order journey is clearly presented with timestamps in 12-hour format and states including pending payment, pending fulfillment, pending receipt, completed, canceled, refund in progress, and refunded; orders auto-cancel after 30 minutes of inactivity at pending payment, with clear UI banners and inventory/slot rollback if the item is configured as capacity-limited. Candidates can request after-sales service within 14 days of completion, and they can file attendance exceptions when missed check-ins or late arrivals are flagged, uploading proof and tracking a routed review decision with an immutable approval trail. Staff screens focus on queues for order confirmation, voucher issuance, logistics-style status updates (internal milestones rather than external carriers), and appeal adjudication with consistent, searchable outcomes.

The backend uses FastAPI to enforce the order state machine, validate transitions, and persist all records in PostgreSQL with transactional guarantees so that auto-cancel, refunds, and optional inventory rollback are atomic. Authentication is strictly local username/password with a minimum 12-character password policy, salted hashing, 15-minute JWT sessions with refresh, and device-bound anti-replay using API signing plus a 5-minute nonce window stored server-side; SSO is implemented as an internal identity provider without external dependencies. Fine-grained RBAC governs page and API access, while row/column-level controls prevent unauthorized viewing of sensitive fields (for example masking SSNs to last four digits) and restrict document downloads to approved roles; every export and downloaded PDF is watermarked with username and timestamp, and files are verified via SHA-256 hash on upload and download. Sensitive data is encrypted at rest using envelope encryption with locally managed keys, and all traffic is end-to-end HTTPS using locally provisioned certificates. Observability is built in with unified structured logs, metrics, and traces for critical flows (login, upload, order state transitions, appeal approvals), plus a local config center for feature flags (bargaining on/off, rollback on/off), canary release routing by user cohort, and capacity/bandwidth forecasting based on historical request volumes and document size distributions; CDN references are replaced by offline cache policy controls for static assets served by the same deployment, including cache hit-rate reporting from local access logs.

# 10 Sequential Prompts

## Prompt 1 — Architecture framing, repo contract, and planning artifacts

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Lock the project type, stack, repository contract, documentation baseline, and truthful scaffolding so implementation starts from a stable FastAPI + Vue + PostgreSQL foundation instead of drifting into generic templates.

**Exact Scope**  
Work only on project framing artifacts and truthful scaffolding in `docs/`, `repo/`, `repo/frontend/`, and `repo/backend/`. Create the core structure, initial build/test manifests, initial metadata, and the first synchronized documentation set. Do not implement business workflows beyond the minimum structural anchors needed for later prompts.

**Implementation Instructions**
1. Classify this repository as a **full-stack offline-ready admissions and transaction operations platform** and make that explicit in `metadata.json`, `repo/README.md`, and `docs/design.md`.
2. Create the initial folder structure:
   - `repo/frontend/` with `src/`, `public/`, `unit_tests/`, and subfolders for `router/`, `stores/`, `services/`, `composables/`, `views/`, `components/`, `types/`, and `utils/`.
   - `repo/backend/` with source roots for `api/`, `schemas/`, `domain/`, `services/`, `persistence/`, `security/`, `workers/`, `telemetry/`, `storage/`, and `database/`.
   - `docs/design.md`, `docs/api-spec.md`, `docs/questions.md`, `docs/requirement-traceability.md`, and `docs/test-traceability.md`.
3. Choose and record the actual implementation stack with stable defaults:
   - Vue 3 + TypeScript + Vite + Vue Router + Pinia on the frontend.
   - Python 3.10 + FastAPI + Pydantic v2 + SQLAlchemy 2.x + Alembic on the backend.
   - PostgreSQL 14+ as the database.
   - Local filesystem-backed storage for documents, watermarked exports, access logs, and forecast snapshots.
   - Vitest + Vue Test Utils + Playwright for the frontend test toolchain.
   - Pytest + HTTPX + pytest-asyncio or equivalent for backend unit and API/integration tests.
4. Create a truthful `docs/design.md` that covers:
   - offline facility-network assumptions;
   - the candidate/staff/reviewer/admin role model;
   - the overall frontend/backend/PostgreSQL/local-storage topology;
   - the chosen same-deployment strategy for compiled Vue assets;
   - HTTPS and local certificate assumptions;
   - request-signature and nonce verification at a high level;
   - document-storage, watermarking, and hash-verification boundaries;
   - order-state-machine, exception-routing, config-center, observability, and forecasting module boundaries;
   - a requirement-to-module traceability table that maps each major prompt requirement to intended modules.
5. Create a truthful `docs/api-spec.md` that defines:
   - API grouping strategy;
   - request/response envelope conventions;
   - auth, refresh, and request-signature headers at a high level;
   - error model and validation-error shape;
   - idempotency-key conventions;
   - upload and resumable-upload placeholder contracts only where the endpoint category is real;
   - initial endpoint groups for auth/IdP, candidate profiles, documents, service catalog/orders, bargaining, after-sales, attendance exceptions, queues, admin config, observability, audit/export, and forecasting.
6. Create `docs/questions.md` first, using only blocker-level or implementation-shaping ambiguities and the exact format:
   - `The Gap`
   - `The Interpretation`
   - `Proposed Implementation`
   Capture practical assumptions for local payment handling, internal IdP boundaries, certificate provisioning, envelope-key storage, request-signing/device identity, bargaining resolution after a counter, rollback semantics, attendance-exception routing, watermark scope, cohort routing, forecasting method, and cache-hit reporting.
7. Create the first truthful `repo/README.md` with:
   - project overview;
   - exact stack;
   - repository structure;
   - offline/local constraints;
   - note that Docker and test execution are intentionally deferred at this stage;
   - only real commands, files, and paths that exist after this prompt.
8. Add initial package/build configuration:
   - frontend package manager config, Vite config, TypeScript config, Vitest config, and Playwright config scaffold;
   - backend dependency manifest, Alembic scaffold, application entrypoint scaffold, and basic config-loading skeleton;
   - `.gitignore` and config templates only if they are truthful and non-speculative.
9. Create `repo/docker-compose.yml`, `repo/frontend/Dockerfile`, and `repo/backend/Dockerfile` as **truthful scaffolding only**. Keep them aligned to the files that actually exist. If the production runtime will serve the built Vue assets through FastAPI, document that honestly instead of inventing a separate runtime service now.
10. Create the project-specific Claude memory and project-specific `CLAUDE.md` rules in the repository’s Claude project context, then output their contents for user review before continuing with later prompts.
11. Create `metadata.json` that reflects the real stack for this prompt, including:
   - `Project Type: Full stack`
   - the unedited original prompt
   - `frontend_language: TypeScript`
   - `backend_language: Python`
   - `frontend_framework: Vue.js`
   - `backend_framework: FastAPI`
   - `database: PostgreSQL`
   Do not add a `current_prompt` field.

**Contextual self-checks for this prompt**
- Keep documentation statically verifiable and internally consistent from the first commit.
- Keep the repo shape aligned to a real full-stack Vue + FastAPI + PostgreSQL project, not a backend-only starter or a fake frontend shell.
- Keep README limited to real files, real commands, and real constraints.
- Do not invent extra services, payment gateways, object stores, or CDN layers.
- Keep the same-deployment static-asset story honest from the start.

**Test-Authoring Instructions**
- Create the test directory structure now: `repo/frontend/unit_tests/`, `repo/backend/unit_tests/`, and `repo/backend/api_tests/`.
- Add only minimal scaffold tests that verify something real, such as frontend bootstrap importability, config-schema parsing, and backend app importability.
- Add a browser-workflow scaffold under `repo/frontend/unit_tests/` only if it verifies a real route shell or bootstrap behavior rather than a fake page.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Synchronize `docs/design.md`, `docs/api-spec.md`, `docs/questions.md`, `docs/requirement-traceability.md`, `docs/test-traceability.md`, `repo/README.md`, and `metadata.json`.
- Keep the Original Prompt unedited where it is recorded.
- Keep stack names, folder structure, asset-serving approach, and offline constraints identical across docs.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not try to build the whole project; laser focus on framing and truthful scaffolding only.
- Do not create placeholder business logic, fake APIs, or pretend integrations.
- Do not touch `sessions/`.
- Do not create root-level test folders.
- Do not put `questions.md` anywhere except `docs/`.

**Completion Criteria**
- The strict repo structure exists and reflects a real full-stack Vue + FastAPI + PostgreSQL project.
- Core planning docs exist and are synchronized.
- `docs/questions.md` captures blocker-level ambiguities with practical forward-moving assumptions.
- `repo/README.md`, Docker assets, and metadata are mutually consistent at this stage.
- Initial test folders exist in the correct locations.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 2 — Domain model, persistence design, API contracts, and policy backbone

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Define the domain truth, schema design, API contracts, state machines, and policy boundaries so the project’s admissions, documents, ordering, exception, and admin rules are settled before deeper implementation begins.

**Exact Scope**  
Focus on backend domain modeling, PostgreSQL schema and migration design, explicit backend request/response contracts, storage metadata, and related documentation. Do not build the full frontend or full backend workflows yet.

**Implementation Instructions**
1. Define backend domain entities, enums, and value objects for:
   - local users, credentials, refresh sessions, internal IdP clients, role assignments, row/column-scope policies, device registrations, API nonce records, and login-throttle records;
   - candidate profiles, application details, initial exam scores, transfer preferences, and profile-update history;
   - document requirements, checklist templates, uploaded-document metadata, file versions, status history, resubmission reasons, hashes, and access grants;
   - service catalog items, capacity limits, pricing modes, fixed-price policies, bargaining threads, offers, reviewer counters, offer windows, payment records, vouchers, order states, order-state history, fulfillment milestones, refunds, and rollback events;
   - after-sales requests, windows, dispositions, and linked refund/escalation records;
   - attendance anomalies, missed-check-in and late-arrival flags, proof uploads, routed review steps, immutable approval entries, and searchable outcome records;
   - feature flags, config versions, cohort definitions, canary-routing assignments, access-log summaries, cache-policy rules, forecasting inputs, and forecast snapshots;
   - audit events, export jobs, watermark policies, download restriction rules, telemetry correlation records, and trace identifiers.
2. Design the PostgreSQL relational schema and migrations in `repo/backend/database/` with explicit constraints and indexes for:
   - duplicate profile/order submissions and unique conflict boundaries;
   - up to three candidate offers per order within a 48-hour bargaining window;
   - one reviewer counter per bargaining thread;
   - capacity-limited slot reservation and rollback support;
   - order-state history ordering and transition validation;
   - document version ordering, checklist completion, and approved-role download authorization;
   - attendance-exception review ordering and immutable approval steps;
   - nonce freshness, device bindings, and request-signature replay prevention;
   - feature-flag history, cohort assignments, access-log aggregation, and forecasting datasets;
   - watermark/export auditing and hash-verification records.
3. Define the key business invariants in code and docs, including:
   - accepted document formats limited to PDF/JPG/PNG;
   - 25 MB per-file limit;
   - required checklist completion tracked independently from upload existence;
   - status transitions for uploaded documents, including “Needs resubmission” with a mandatory reason;
   - order states limited to pending payment, pending fulfillment, pending receipt, completed, canceled, refund in progress, and refunded;
   - auto-cancel after 30 minutes of inactivity only while pending payment;
   - up to three candidate offers within 48 hours in bargaining mode;
   - at most one reviewer counter per bargaining thread;
   - after-sales request eligibility limited to 14 days after completion;
   - atomic rollback of capacity-limited slots when policy allows and the order transition warrants it;
   - immutable attendance-exception approval history;
   - watermarking of every export and downloaded PDF;
   - hash verification on upload and download.
4. Expand `docs/api-spec.md` with concrete endpoint groups and payload contracts for:
   - auth, refresh, internal IdP, and session revocation;
   - candidate profiles, exam scores, transfer preferences, and document requirements;
   - uploads, resubmissions, downloads, and checklist/status endpoints;
   - service catalog, orders, bargaining, offers, counters, payments, vouchers, milestones, refunds, and after-sales;
   - attendance exceptions, proof uploads, routed reviews, and searchable outcomes;
   - config center, feature flags, cohort routing, audit search/export, telemetry summaries, forecasting, and cache-policy reporting.
5. Define error-envelope conventions, conflict/error codes, optimistic-concurrency semantics, and idempotency behavior for all mutation-heavy flows.
6. Create or expand `docs/requirement-traceability.md` so each major prompt requirement points to intended schema modules, endpoint groups, and planned tests.
7. Start an endpoint inventory in `docs/test-traceability.md` using unique `METHOD + fully resolved PATH` rows, even if some tests are deferred to later prompts.

**Contextual self-checks for this prompt**
- Keep the data model aligned to admissions operations and order workflows, not generic marketplace or CRM abstractions.
- Make later security, audit, watermarking, hash verification, and rollback behavior implementable without schema rework.
- Keep business invariants explicit in code and docs rather than relying on UI assumptions.
- Keep timestamp formatting concerns separated cleanly: canonical storage in the backend, 12-hour rendering in the frontend.

**Test-Authoring Instructions**
- Add backend unit tests for enum validation, document-format and file-size invariants, bargaining-offer limits, counter-once rules, auto-cancel timing calculations, after-sales windows, and exception-routing invariants.
- Add backend API contract tests for malformed payloads, expected conflict/error envelopes, and idempotency/conflict response shapes.
- Record whether each endpoint currently has planned true no-mock HTTP coverage, mock-heavy HTTP coverage, or only non-HTTP unit coverage.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Keep `docs/design.md`, `docs/api-spec.md`, `docs/questions.md`, `docs/requirement-traceability.md`, `docs/test-traceability.md`, and `repo/README.md` synchronized with the actual entities, invariants, endpoint groups, and storage choices.
- Record any newly discovered blocker-level ambiguity in `docs/questions.md` only.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not build the full frontend in this prompt.
- Do not use hardcoded JSON or spreadsheet-like mock data as a substitute for real domain/schema design.
- Do not skip document, bargaining, attendance-exception, observability, or config-center entities because they feel secondary.

**Completion Criteria**
- Domain entities, schema design, and API contracts are prompt-faithful and implementation-ready.
- Business invariants are explicit in code/docs.
- Critical contract and invariant tests exist but remain unexecuted.
- Endpoint inventory and requirement traceability have a real starting baseline.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 3 — Security foundation, internal identity, encryption, authorization, and shared backend infrastructure

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Implement the shared security and infrastructure primitives that every later workflow depends on: local auth, internal SSO, JWT/refresh handling, request signing, replay protection, encryption, masking, watermarking, hashing, validation, logging, traces, and reusable error handling.

**Exact Scope**  
Work only on backend security infrastructure and shared foundations, plus any minimal frontend auth/session plumbing needed to support later screens. Do not implement the full business workflows here.

**Implementation Instructions**
1. Implement backend authentication and session management with:
   - local username/password login only;
   - minimum 12-character password validation;
   - adaptive salted hashing such as Argon2id or equivalent;
   - 15-minute JWT access sessions with refresh-token handling;
   - login-throttle and anti-bot protections;
   - explicit session revocation and refresh rotation behavior.
2. Implement the internal identity-provider capability as a first-party FastAPI module with no external dependencies. Keep it limited to the repository’s own trust boundary and documented internal clients. Do not introduce third-party SSO products.
3. Implement request-signature verification and anti-replay handling suitable for a browser client and an offline facility network using an explicit browser-safe device-binding model:
   - WebCrypto-backed per-device asymmetric keypair generation with non-exportable private-key material where the platform supports it, with a documented fallback only if required by the final browser target and still bound to the device registration record;
   - signed challenge-based device enrollment and activation tied to the authenticated user and stored device registration metadata;
   - canonical request signing rules covering method, fully resolved path, selected headers, body hash, timestamp, nonce, and device identifier;
   - 5-minute nonce freshness enforcement stored server-side;
   - server-side signature verification, replay rejection, and signature-failure audit logging;
   - device-key rotation, revocation, and re-enrollment flows;
   - explicit backend/frontend storage-boundary rules for public keys, device identifiers, and any browser-held signing material.
4. Implement RBAC and data-scope authorization primitives for:
   - page and route access;
   - service/function-level enforcement;
   - object-level ownership checks;
   - row-level filtering and column-level masking for sensitive data;
   - approved-role document download restrictions.
5. Implement envelope encryption support for sensitive data at rest using locally managed keys:
   - key version metadata;
   - DEK/KEK separation or equivalent envelope model;
   - backend-only decryption boundaries;
   - masked serializer output by default;
   - last-four display behavior for SSN-like sensitive identifiers when applicable.
6. Implement SHA-256 verification support for uploads and downloads, plus watermarking helpers for generated exports and downloaded PDFs.
7. Implement reusable validation, idempotency, structured error envelopes, structured logging, metrics, and trace-correlation infrastructure.
8. Implement immutable audit-event writing with field-level diff support for sensitive state changes.
9. Add minimal frontend auth/session shell wiring:
   - login page shell;
   - guarded-route strategy;
   - role-aware navigation placeholders;
   - refresh/session-expiry handling;
   - unauthorized and forbidden-state handling.

**Contextual self-checks for this prompt**
- Keep security controls explicit and testable. Do not hide them behind comments or UI assumptions.
- Keep auth, replay defense, encryption, masking, watermarking, and hash verification in real code, not documentation-only stubs.
- Keep route-level, function-level, object-level, and row/column-level boundaries distinguishable in the implementation.
- Keep logs and error responses secret-safe.

**Test-Authoring Instructions**
- Add backend unit tests for password-policy validation, password hashing, JWT creation/refresh behavior, login throttling, signed device-enrollment challenge verification, nonce freshness, canonical request-signature verification, device-key rotation and revocation checks, encryption/decryption helpers, masking policies, watermark helpers, and file-hash verification helpers.
- Add backend API/integration tests for unauthenticated access, unauthorized access, signature failures, stale nonce rejection, throttled login, approved-role download enforcement, and secret-safe error responses.
- Add frontend unit tests for route guards, login error rendering, session-expiry handling, role-aware navigation gating, device-registration bootstrap helpers, and signature-failure handling.
- Add at least one frontend browser-workflow test for login-shell rendering and forbidden-route handling if the route already exists in a real form.
- Mark each new API/integration test as true no-mock HTTP, mock-heavy HTTP, or non-HTTP support coverage in `docs/test-traceability.md`.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Update `docs/design.md` with the security architecture, trust boundaries, key-management assumptions, device-registration/signing model, and auth/session flow.
- Update `docs/api-spec.md` with auth, refresh, IdP, signature, nonce, device-registration, error-envelope, and download-policy details.
- Update `docs/requirement-traceability.md` and `docs/test-traceability.md` with security modules and tests.
- Update `repo/README.md` only with real security/config information that now exists.
- Keep `docs/questions.md` honest about certificate and key provisioning assumptions.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not hardcode secrets, master keys, default passwords, or role bypasses.
- Do not leave encryption, watermarking, or hash verification as documentation-only ideas.
- Do not leak raw stack traces or sensitive fields to frontend responses.

**Completion Criteria**
- Security-critical primitives are implemented and reusable.
- Frontend auth shell foundations exist without overreaching into future business screens.
- Tests cover major security and auth failure paths.
- Docs reflect the actual security architecture and policies.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 4 — Core backend business engine: onboarding, documents, ordering, bargaining, refunds, after-sales, and attendance exceptions

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Make the backend’s primary business engine real: candidate onboarding, document-review state handling, fee-based ordering, bargaining, auto-cancel and rollback, after-sales, attendance exceptions, staff queues, and auditable transitions.

**Exact Scope**  
Work on backend services, repositories, state transitions, background jobs, persistence, and API handlers for the core business workflows. Keep frontend changes limited to API compatibility shims only.

**Implementation Instructions**
1. Implement candidate onboarding and profile logic:
   - profile create/read/update;
   - application details;
   - initial exam-score capture;
   - transfer preferences;
   - audit trails for sensitive changes.
2. Implement the document pipeline:
   - accepted file validation for PDF/JPG/PNG only;
   - 25 MB per-file validation;
   - required checklist tracking;
   - immediate validation response payloads;
   - versioned uploads and resubmissions;
   - statuses including draft, submitted, approved, rejected, and “Needs resubmission” with a required reason;
   - reviewer-side decision actions for approve, reject, and “Needs resubmission” with required reason capture, status history, and auditable reviewer identity;
   - approved-role download restrictions;
   - SHA-256 capture and download re-verification hooks.
3. Implement the service catalog and order state machine:
   - fixed-price mode and bargaining mode;
   - candidate offer submission capped at three offers in 48 hours;
   - reviewer accept flow;
   - reviewer counter flow limited to one counter per bargaining thread;
   - explicit transition to fixed-price or expiry after the bargaining window/counter rule;
   - order timeline/history persistence;
   - states limited to pending payment, pending fulfillment, pending receipt, completed, canceled, refund in progress, and refunded;
   - 30-minute pending-payment inactivity auto-cancel;
   - transactional rollback of capacity-limited slots when policy and state permit it.
4. Implement local payment/voucher/order-operations support consistent with the offline environment:
   - candidate payment-intent submission or proof/receipt submission flow within local trust boundaries, with validation, duplicate-submission protection, and state transitions out of pending payment only through explicit reviewer confirmation or auto-cancel;
   - payment or settlement records within local trust boundaries;
   - voucher issuance records;
   - payment confirmation and order confirmation queues;
   - fulfillment milestone tracking using internal statuses rather than carrier integrations.
5. Implement refund and after-sales logic:
   - after-sales requests allowed only within 14 days of completed orders;
   - refund initiation and refund-in-progress handling;
   - atomic refund + rollback handling where configured;
   - auditable reviewer decisions.
6. Implement attendance-exception workflow logic:
   - missed-check-in and late-arrival flags;
   - proof uploads;
   - routed review steps;
   - immutable approval trail;
   - consistent searchable final outcomes.
7. Implement staff/reviewer queue APIs for:
   - document review and resubmission-decision actions;
   - payment confirmation;
   - order confirmation;
   - voucher issuance;
   - fulfillment-status updates;
   - exception review and appeal adjudication;
   - searchable status and outcome filters.
8. Implement background jobs or worker processes for:
   - pending-payment timeout auto-cancel;
   - bargaining expiry handling;
   - rollback execution;
   - refund progression;
   - after-sales-window enforcement;
   - stale queue cleanup and audit-safe retries where needed.
9. Expose real backend endpoints for these workflows with validation, authorization, masking, idempotency, and audit writes all enforced.

**Contextual self-checks for this prompt**
- This is the highest business-risk stage. Keep logic real, persisted, and transactional.
- Do not fake order-state transitions, bargaining limits, auto-cancel, refund handling, or document-review outcomes.
- Keep rollback behavior atomic where the prompt requires atomic guarantees.
- Keep queue statuses, outcome enums, and approval trails consistent and searchable.

**Test-Authoring Instructions**
- Add backend unit tests for document validation, checklist completion logic, reviewer document-decision handling, resubmission handling, order-state transitions, offer limits, counter-once rules, bargain expiry, pending-payment auto-cancel timing, payment submission and reviewer confirmation rules, capacity rollback, refund transitions, after-sales windows, attendance-exception routing, and queue filter logic.
- Add backend API/integration tests for:
   - profile update and audit behavior;
   - document upload validation, review decisions, and resubmission;
   - order creation in fixed-price and bargaining modes;
   - payment-intent or proof/receipt submission, reviewer payment confirmation, offer submission, reviewer accept, reviewer counter, bargain expiry, and state-history responses;
   - auto-cancel and rollback paths;
   - refund and after-sales flows;
   - attendance-exception filing, proof upload, routed review, and searchable outcomes.
- Cover validation failures, unauthorized and forbidden responses, not-found cases, conflicts, idempotency paths, and policy-denied downloads.
- Classify critical route tests as true no-mock HTTP wherever the real FastAPI route stack is available.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Update `docs/design.md` with stepwise flow descriptions for onboarding, documents, document adjudication, order transitions, payment submission/confirmation, bargaining, refunds, after-sales, attendance exceptions, and queue operations.
- Update `docs/api-spec.md` with real request/response examples, transition rules, and conflict codes.
- Update `docs/requirement-traceability.md` and `docs/test-traceability.md` to tie these modules and routes to tests.
- Update `repo/README.md` only with backend capabilities that now truly exist.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not move business rules into controllers or route handlers only.
- Do not replace transactional guarantees with “best effort” comments.
- Do not skip audit writes for status changes, approvals, refunds, rollbacks, or sensitive downloads.

**Completion Criteria**
- The core backend business engine is implemented with real persistence, validation, concurrency-safe transitions, and auditability.
- Critical backend workflow tests exist and are meaningful.
- Docs and contracts reflect the real implementation state.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 5 — Frontend shell, offline-ready client architecture, and secure service layer

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Build the Vue application shell and offline-ready client architecture so later business screens sit on a maintainable, security-aware, policy-aligned frontend foundation.

**Exact Scope**  
Focus on frontend app structure, routing, layout shells, shared stores, service adapters, offline cache/queue primitives, request-signature support, and reusable UI primitives. Do not build every business screen in full yet.

**Implementation Instructions**
1. Implement the frontend application shell with:
   - Vue Router;
   - authenticated and unauthenticated layout shells;
   - role-aware navigation groups for Candidate, Proctor/Teacher, Admissions Reviewer, and System Administrator;
   - route guards aligned to backend auth and role rules;
   - global loading/error/unauthorized patterns.
2. Implement Pinia stores, composables, and service modules for:
   - auth/session state and refresh handling;
   - device registration and request-signing key state;
   - candidate profile/application state;
   - document requirements and upload state;
   - service catalog and order state;
   - bargaining timers and offer history;
   - attendance exceptions and proof-upload state;
   - reviewer queue state;
   - admin config, audit, telemetry, and forecasting summaries.
3. Implement a typed frontend API layer that handles:
   - JWT/session attachment;
   - WebCrypto-backed device registration bootstrap, signed challenge enrollment, and device-identifier persistence aligned to the backend security model;
   - canonical request-signature header generation covering method, path, selected headers, body hash, timestamp, nonce, and device identifier;
   - nonce lifecycle handling and signature-failure recovery;
   - idempotency-key generation where the frontend owns the action;
   - normalized error mapping;
   - backend conflict surfaces without hiding them behind generic toasts.
4. Implement the offline-ready client foundation:
   - IndexedDB-backed caching for critical reference data and pending actions;
   - local persistence for resumable uploads and offline-safe mutations;
   - retry and conflict-reconciliation hooks;
   - explicit offline, reconnecting, and conflict banners;
   - local cache-policy controls for static assets only where they align with the final deployment story.
5. Implement reusable UI primitives needed by later screens:
   - forms and field groups;
   - tables/lists with empty states;
   - status chips and queue badges;
   - 12-hour timestamp and timeline rendering primitives;
   - countdown/timer components for bargain windows and payment timeouts;
   - upload panels, checklist widgets, banner/toast patterns, modal/drawer patterns, and masked-value display helpers.
6. Implement role-safe download/export gates and frontend masking helpers aligned to backend policies.
7. Create the first real login screen and post-login dashboard shell with accurate route placeholders and no fake data-path shortcuts.

**Contextual self-checks for this prompt**
- Keep the frontend shaped like a connected application, not a component gallery or static admin template.
- Make offline/pending/retry/conflict behavior explicit in the architecture rather than hand-waving it away.
- Keep sensitive data masking, download gating, and role-aware navigation aligned to backend policy decisions.
- Keep 12-hour display formatting consistent in shared utilities rather than duplicating formatting logic per screen.

**Test-Authoring Instructions**
- Add frontend unit tests for route guards, auth-store behavior, session refresh behavior, role-aware navigation visibility, device-registration bootstrap helpers, request-signature header generation, nonce lifecycle handling, offline queue persistence helpers, resumable-upload state helpers, error normalization, masked-value helpers, and 12-hour timestamp formatting.
- Add frontend unit tests for cache rehydration, pending-action queue state, and conflict-banner rendering primitives.
- Add initial frontend browser-workflow tests under `repo/frontend/unit_tests/` for login-shell navigation, unauthorized-route redirects, signature-failure handling, and an offline-banner or reconnect-banner path if the real shell supports it.
- Record `Frontend unit tests: PRESENT` in `docs/test-traceability.md` only when real frontend test files exist and import or execute real frontend modules.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Update `docs/design.md` with frontend architecture, store/service boundaries, offline queue/cache design, shared component boundaries, and the browser-side request-signing model.
- Update `repo/README.md` to describe the actual frontend module layout and state architecture.
- Update `docs/requirement-traceability.md` and `docs/test-traceability.md` with frontend mappings.
- Update `docs/api-spec.md` only if frontend-driven contract refinements became necessary.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not build all business screens in this prompt.
- Do not hardcode fake workflow results into stores, route guards, or views.
- Do not bypass backend policies in the frontend for convenience.

**Completion Criteria**
- A maintainable frontend shell and offline-ready architecture exist.
- Shared stores, services, and primitives are ready for real screens.
- Frontend tests cover the client foundation and offline/error-state primitives.
- Documentation stays synchronized with the actual client structure.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 6 — Primary user workflows and core full-stack screens

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Implement the main user-facing flows and screens so the application already supports the central day-to-day operations for candidates, proctors/teachers, reviewers, and administrators.

**Exact Scope**  
Build the highest-priority frontend screens and connect them to the real backend logic from earlier prompts. Do not finish every secondary admin/reporting surface yet.

**Implementation Instructions**
1. Implement candidate-facing onboarding screens:
   - profile and application-detail forms;
   - initial exam-score capture and editing;
   - transfer-preference management;
   - role-safe display of existing profile information;
   - clear save, validation, and conflict feedback.
2. Implement candidate document-management screens:
   - required-document checklist;
   - upload and resubmission flows;
   - immediate accepted-format and 25 MB limit feedback;
   - visible document status badges;
   - “Needs resubmission” display with reason;
   - approved-role download behavior and hash-verification result display where applicable.
3. Implement candidate ordering screens:
   - service catalog and item detail;
   - fixed-price ordering flow;
   - bargaining mode with up to three offers, countdown visibility, offer history, and counter visibility;
   - pending-payment action flow for local payment submission, proof/receipt upload or confirmation entry, duplicate-submit protection, and clear transition feedback when reviewer confirmation is required;
   - order timeline with 12-hour timestamps;
   - banners for pending payment timeout risk, cancellation, refund-in-progress, and refunded outcomes;
   - pending fulfillment, pending receipt, completed, and after-sales request actions.
4. Implement candidate attendance-exception screens:
   - anomaly display for missed check-ins or late arrivals;
   - proof-upload flow;
   - routed review status;
   - immutable decision history presentation.
5. Implement proctor/teacher and reviewer workflow screens:
   - document review queues with approve, reject, and “Needs resubmission” actions plus required reason capture;
   - payment confirmation and order review/confirmation queues;
   - offer acceptance/counter actions;
   - voucher issuance;
   - fulfillment milestone updates using internal statuses;
   - attendance-exception review and appeal adjudication;
   - searchable consistent outcome views.
6. Keep all screens connected to real service-backed data and show meaningful loading, empty, error, success, conflict, and disabled states.
7. Keep masked values masked by default, respect download restrictions, and keep timeline/date rendering consistently in 12-hour format.

**Contextual self-checks for this prompt**
- Keep the flows truly end-to-end from UI to real backend logic. Do not ship static screens that only look complete.
- Make bargaining timers, payment-timeout banners, document statuses, review actions, and review outcomes visible and actionable.
- Keep role-based action visibility and search/filter outcomes aligned to backend permissions.
- Keep user-visible failure states credible. Do not hide policy conflicts or transition failures.

**Test-Authoring Instructions**
- Add frontend unit tests for candidate profile editing, document upload validation states, checklist rendering, resubmission status rendering, bargaining timers, pending-payment submission states, order-state banners, after-sales eligibility display, and attendance-exception filing flows.
- Add frontend unit tests for reviewer document-review actions, reviewer queue filters, payment confirmation actions, voucher issuance actions, milestone-update states, appeal adjudication flows, and outcome badge rendering.
- Add frontend browser-workflow tests for at least the highest-risk UI paths: candidate document upload, fixed-price or bargaining order placement, pending-payment submission, reviewer document-review action flow, and reviewer queue action flow.
- Add backend API/integration tests that support the same flows from the server side, including validation failures, policy denials, conflict paths, document-review decisions, payment-confirmation transitions, and timeline/history responses.
- Update `docs/test-traceability.md` to reflect balanced frontend/backend coverage for these primary flows.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Update `docs/design.md` with the screen map, role-to-screen matrix, and workflow descriptions.
- Update `repo/README.md` to describe only the screens and flows that now genuinely exist.
- Update `docs/api-spec.md`, `docs/requirement-traceability.md`, and `docs/test-traceability.md` if any contracts or mappings changed.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not leave screens disconnected from real backend logic.
- Do not skip empty/error/conflict/submitting states.
- Do not expose restricted data by default in the UI.

**Completion Criteria**
- The main candidate and staff/reviewer workflows are available end-to-end through real frontend/backend integration.
- Required UI states and role-aware flows are implemented.
- Tests cover primary screen logic and critical failure states.
- Docs reflect the real user-facing application shape.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 7 — Secondary required modules: admin controls, config center, observability, forecasting, and cache/reporting surfaces

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Complete the remaining required modules that materially affect prompt completeness: security/admin surfaces, local config center, canary cohort routing, observability, forecasting, audit/export restrictions, and cache-hit reporting.

**Exact Scope**  
Focus on system-administrator surfaces, backend support for operational reporting, local rollout controls, and policy/reporting modules that make the platform operationally complete. Do not overbuild optional extras.

**Implementation Instructions**
1. Implement system-administrator security and policy surfaces for:
   - role and permission visibility;
   - row/column masking policy inspection;
   - approved-role document download policies;
   - watermark and export restrictions;
   - audit search by actor, date range, object, and action type.
2. Implement the local config center:
   - feature flags such as bargaining on/off and rollback on/off;
   - configuration version history;
   - change audit trails;
   - stable cohort definitions and per-user cohort assignments;
   - canary release routing decisions by user cohort;
   - UI/API surfaces that show which cohort/config a user currently receives.
3. Implement observability support and surfaces for:
   - structured logs with trace correlation;
   - metrics for login, upload, order state transitions, exception approvals, and critical queue actions;
   - trace identifiers and drill-down views or exportable summaries;
   - local-only visibility with no hosted telemetry services.
4. Implement capacity and bandwidth forecasting:
   - historical request-volume aggregation;
   - document-size distribution capture;
   - forecast calculations and persisted snapshots;
   - admin views or exportable summaries for forecast results.
5. Implement static-asset cache-policy controls and cache hit-rate reporting:
   - cache policy configuration aligned to same-deployment asset serving;
   - local access-log parsing or aggregation;
   - cache hit/miss reporting surfaced to administrators.
6. Implement export/report controls and histories for:
   - watermarked PDF or CSV generation where required;
   - export request history;
   - download audit visibility;
   - policy-denied export/download outcomes.
7. Finish any remaining admin/reporting APIs needed to make the prompt complete without inventing unrelated platform features.

**Contextual self-checks for this prompt**
- Secondary modules still count toward prompt completeness. Do not leave config center, observability, forecasting, or cache-hit reporting as TODOs.
- Keep admin/reporting surfaces grounded in real backend data and policies.
- Keep every admin/export surface aligned to masking, audit, and authorization rules.
- Keep canary routing local and inspectable rather than implying an external release platform.

**Test-Authoring Instructions**
- Add backend unit tests and API/integration tests for feature-flag evaluation, cohort assignment, canary-routing decisions, audit search filters, export restriction enforcement, watermark generation, telemetry metric emission, forecasting calculations, and cache hit-rate aggregation.
- Add frontend unit tests for admin config views, cohort/config display, observability summary rendering, forecasting result views, and export restriction UI handling.
- Add at least one frontend browser-workflow test for an administrator updating a feature flag or inspecting a cohort/config view if the real screen exists.
- Mark critical admin endpoints with true no-mock HTTP coverage where available.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Update `docs/design.md`, `docs/api-spec.md`, `docs/requirement-traceability.md`, `docs/test-traceability.md`, and `repo/README.md` with the now-implemented secondary modules.
- Keep `docs/questions.md` updated if any remaining deployment-policy ambiguity is still genuinely blocker-level.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not treat observability or cache-hit reporting as cloud-service integrations.
- Do not build vanity dashboards that are disconnected from real stored metrics or audit records.
- Do not over-invest in optional reporting features that are not required by the prompt.

**Completion Criteria**
- Remaining required admin, config, observability, forecasting, and export/reporting modules are implemented and documented.
- Tests exist for the major secondary risk areas.
- The product is functionally close to complete rather than demo-complete.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 8 — Test suite authoring, endpoint inventory, coverage hardening, and requirement-to-test traceability

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Harden the repository’s authored test corpus so it is positioned to exceed 90% coverage on critical logic and survive a later static acceptance audit. Target >90% coverage on tests.

**Exact Scope**  
Focus on tests, endpoint inventory, `repo/run_tests.sh`, and requirement-to-test traceability materials. Make code refactors only where necessary to improve testability or isolate side effects.

**Implementation Instructions**
1. Complete frontend unit tests across:
   - auth/session and route guards;
   - device registration, request-signature generation, and signature-failure handling;
   - profile and application flows;
   - document checklist, upload, review, resubmission, status, and masking behavior;
   - order placement, pending-payment submission, bargaining timers, offer history, state banners, after-sales eligibility, and exception filing;
   - reviewer queues, document-review actions, payment confirmation, milestone updates, and outcome search/filter UI;
   - admin config center, observability summaries, forecasting displays, and export/download restriction handling;
   - offline queue/cache, resumable upload state, and conflict-resolution states.
2. Complete frontend browser-workflow tests under `repo/frontend/unit_tests/` for the highest-risk user journeys:
   - login and route protection;
   - candidate document upload and status visibility;
   - fixed-price or bargaining order placement and timeline display;
   - pending-payment submission;
   - reviewer document-review action flow;
   - reviewer queue action flow;
   - admin feature-flag or config inspection flow if implemented.
3. Complete backend unit tests across:
   - auth, internal IdP, signed device enrollment, request signing, nonce replay protection, encryption, masking, watermarking, and hashing;
   - profile and document logic;
   - document-review decision handling and resubmission rules;
   - order state transitions, pending-payment submission/confirmation rules, bargaining rules, time-window rules, rollback behavior, refund logic, after-sales windows, and queue search behavior;
   - attendance-exception routing and immutable approval records;
   - feature flags, cohort routing, telemetry aggregation, forecasting logic, and cache-hit calculations.
4. Complete backend API/integration tests across:
   - happy paths;
   - validation failures;
   - unauthorized and forbidden access;
   - not-found flows;
   - conflict and idempotency paths;
   - document-review, payment-confirmation, and security-sensitive download/export flows;
   - admin/config, observability, forecasting, and reporting endpoints.
5. Maintain an endpoint inventory in `docs/test-traceability.md` using unique `METHOD + fully resolved PATH` entries. For each endpoint, record:
   - mapped module(s);
   - mapped requirement(s);
   - mapped test file(s);
   - coverage classification: true no-mock HTTP, HTTP with mocking, or non-HTTP support coverage;
   - any remaining gap.
6. Keep a requirement-to-test mapping in `docs/test-traceability.md` or a dedicated subsection so each explicit prompt requirement points to concrete frontend tests, backend unit tests, and backend API/integration tests where applicable.
7. Finalize `repo/run_tests.sh` so it orchestrates frontend unit/browser tests, backend unit tests, and backend API/integration tests in a **docker-first** way without host-dependent assumptions.
8. Make small refactors only where necessary to keep production code testable and maintainable.

**Contextual self-checks for this prompt**
- Keep test guidance specific rather than generic. “Add tests” is not enough.
- Distinguish real endpoint coverage from mocked HTTP or direct-service invocation. Do not overstate coverage.
- Keep frontend and backend coverage balanced. This project requires credible frontend test presence, not backend-only coverage.
- Keep test intent statically understandable from the repository.

**Test-Authoring Instructions**
- This is the main test-authoring prompt. Keep tests maintainable, specific, and tightly tied to real business logic.
- Keep all frontend tests inside `repo/frontend/unit_tests/`, including browser workflow tests in a nested subfolder rather than a new root folder.
- Keep backend unit tests inside `repo/backend/unit_tests/`.
- Keep backend API/integration tests inside `repo/backend/api_tests/`.
- Record `Frontend unit tests: PRESENT` only if file-level evidence exists showing real frontend tests that import, render, or execute frontend modules.
- Prefer true no-mock HTTP coverage for critical FastAPI routes such as auth, document upload, document-review decisions, payment submission/confirmation, order transitions, attendance-exception review, and config updates.
- Keep assertions behavior-deep. Avoid shallow snapshots or boilerplate tests that do not verify meaningful outcomes.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Update `repo/README.md` with real test entry points, folder explanations, and any reviewer-needed role/bootstrap details that truly exist.
- Finalize `docs/test-traceability.md` so it shows requirement coverage, endpoint coverage, coverage classification, and remaining risk gaps.
- Update `docs/requirement-traceability.md`, `docs/design.md`, and `docs/api-spec.md` if tests required contract or module-boundary adjustments.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not add shallow snapshot-only tests that miss business rules.
- Do not place tests outside the required folders.
- Do not leave `repo/run_tests.sh` inconsistent with the real test setup.

**Completion Criteria**
- Test coverage is authored broadly enough to credibly exceed 90% on critical logic once executed later.
- `repo/run_tests.sh` exists and truthfully orchestrates the test suites.
- Requirement-to-test and endpoint-to-test traceability are inspectable and current.
- Docs reflect the actual test structure and coverage intent.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 9 — Dockerization, config hardening, same-deployment asset serving, and documentation synchronization

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Finalize the container assets, runtime configuration discipline, certificate/key assumptions, storage paths, and cross-document synchronization so the repository is ready for later execution without hidden setup surprises.

**Exact Scope**  
Work on Dockerfiles, `docker-compose.yml`, runtime config loading, local HTTPS certificate handling notes, service names/ports, startup docs, same-deployment asset serving, and final README/design/api-spec synchronization. Do not run Docker. Do not run tests.

**Implementation Instructions**
1. Finalize `repo/frontend/Dockerfile` and `repo/backend/Dockerfile` so all build and runtime dependencies are explicitly declared.
2. Finalize the production deployment approach for the Vue assets and keep it truthful everywhere. If the backend serves the compiled Vue assets for the final runtime, make that explicit in Docker, compose, and docs. Add a separate runtime frontend service only if the implemented architecture truly requires it.
3. Finalize `repo/docker-compose.yml` with the minimal justified runtime service set needed for later verification:
   - `backend` as the HTTPS application entry point;
   - `postgres` as the persistent store;
   - and only any additional service that the actual implementation genuinely requires.
4. Choose and freeze the real service names and ports. Keep them identical across:
   - frontend config;
   - backend config;
   - Dockerfiles;
   - `docker-compose.yml`;
   - README;
   - API docs;
   - health/version/config references.
5. Harden configuration handling:
   - no absolute paths;
   - no host-only packages or global tools;
   - no undocumented environment variables;
   - honest handling of local HTTPS certificate paths and trust assumptions;
   - honest handling of encryption-key files or mounted secrets;
   - explicit upload/export/log directories;
   - explicit static-asset cache policy settings;
   - explicit feature-flag/config-center seed behavior if it exists.
6. Add any necessary deployment-support assets for certificate loading, local storage directories, and access-log paths, but keep them non-secret and truthful.
7. Update `repo/README.md` so it includes only real information:
   - project overview;
   - exact stack;
   - repository structure;
   - startup command(s);
   - services and ports;
   - config notes;
   - verification method;
   - test entry points;
   - offline/local-storage/static-asset constraints;
   - certificate and encryption-key assumptions documented honestly.
8. Perform a static cross-check for Docker/README/config alignment and fix mismatches immediately, including port spoofing, service-name mismatches, and asset-serving inconsistencies.

**Contextual self-checks for this prompt**
- Keep Docker and README authenticity as pass/fail concerns rather than nice-to-haves.
- Keep the container story minimal, explicit, and host-independent.
- Keep the same-deployment asset-serving story truthful and consistent.
- Keep certificate/key/storage assumptions honest. Do not imply auto-provisioning that does not exist.

**Test-Authoring Instructions**
- Add or update tests for config parsing, startup defaults, certificate-path validation, asset-manifest loading, storage-path resolution, and any runtime configuration code introduced in this prompt.
- Update `docs/test-traceability.md` if new config or deployment code paths require test coverage.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Synchronize `repo/README.md`, `docs/design.md`, `docs/api-spec.md`, `docs/requirement-traceability.md`, and `docs/test-traceability.md` with the finalized config and container setup.
- Make sure docs describe only real services, real ports, real paths, and real verification steps.
- Keep `docs/questions.md` honest about unresolved certificate, key, or deployment assumptions.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not introduce unnecessary sidecars, reverse proxies, or hidden build helpers.
- Do not leave service-name or port mismatches anywhere.
- Do not promise fully automated certificate provisioning if the repo does not truly implement it.

**Completion Criteria**
- Docker assets are explicit, minimal, and internally consistent.
- Runtime and deployment assumptions are documented honestly.
- README, API spec, design docs, and code/config agree on service names, commands, ports, paths, and asset-serving behavior.
- The repo is statically ready for later `docker compose up` verification.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`

## Prompt 10 — Final static readiness audit before execution

Only do the scope of this prompt. Do not pre-implement future prompts.
Maintain requirement-to-module and requirement-to-test traceability.

**Objective**  
Perform a rigorous static completeness and consistency sweep so the repository is ready for later execution, self-test, and independent review without hidden surprises.

**Exact Scope**  
Audit the existing code, docs, tests, configs, Docker assets, and deployment assumptions. Fix only the gaps needed for completeness, honesty, and traceability. Do not run Docker, do not run tests, and do not add unrelated extra features.

**Implementation Instructions**
1. Perform a full original-prompt requirement audit and confirm every explicit requirement is accounted for in code, config, docs, or an honestly documented assumption in `docs/questions.md`.
2. Verify strict repo-structure compliance:
   - `docs/questions.md` exists in the correct location;
   - `repo/README.md`, `repo/docker-compose.yml`, `repo/run_tests.sh`, `repo/frontend/Dockerfile`, and `repo/backend/Dockerfile` exist;
   - `repo/frontend/unit_tests/`, `repo/backend/unit_tests/`, and `repo/backend/api_tests/` exist;
   - `sessions/` remains untouched;
   - no forbidden root-level test folders exist.
3. Perform a static security audit over:
   - auth entry points;
   - password policy and hashing behavior;
   - JWT/refresh handling;
   - internal IdP flows;
   - request-signature verification and nonce replay defense;
   - RBAC and row/column-level controls;
   - approved-role document-download restrictions;
   - watermarking and SHA-256 verification;
   - envelope-encrypted field handling;
   - secret-safe logs and error responses.
4. Perform a static business-logic audit over:
   - profile/application flows;
   - document upload/resubmission/checklist/status behavior;
   - bargaining limits and reviewer-counter rules;
   - order states and order-history timelines;
   - pending-payment auto-cancel and rollback atomicity;
   - refund and after-sales rules;
   - attendance-exception routing and immutable approval trails;
   - queue search/filter/status consistency;
   - feature flags, cohort routing, observability, forecasting, and cache-hit reporting.
5. Perform a static test-readiness audit:
   - confirm each major requirement maps to authored tests;
   - confirm happy paths, validation failures, unauthorized/forbidden cases, not-found cases, conflicts, idempotency, and security-sensitive flows are covered;
   - confirm frontend unit tests are visibly present;
   - confirm browser workflow tests are present for the highest-risk UI flows;
   - confirm backend API/integration tests distinguish true no-mock HTTP coverage from mock-heavy coverage;
   - confirm `repo/run_tests.sh` targets the real test locations and a docker-first toolchain.
6. Perform a final static Docker/README/config audit:
   - service names;
   - exposed ports;
   - startup commands;
   - verification steps;
   - asset-serving behavior;
   - port spoofing risks;
   - host-only dependency risks;
   - storage-path honesty;
   - documentation honesty.
7. Tighten any remaining code/doc/config mismatches discovered in this audit.
8. Update `docs/questions.md` with any final unresolved but material ambiguity. Do not leave hidden assumptions undocumented.
9. Update `docs/requirement-traceability.md` and `docs/test-traceability.md` so a reviewer can quickly trace requirement → module → endpoint → test.
10. After finishing the static sweep, output a short final note to the user explicitly telling them to invoke the separate **execution-plan reviewer** workflow for an independent post-plan review before beginning execution. Do not attempt that reviewer workflow inside this prompt.

**Contextual self-checks for this prompt**
- Keep this prompt shaped like a near self-test pass.
- Support every strong completion claim with static evidence inside the repository.
- Resolve Docker/README/test-placement/security-boundary mismatches before calling the repository ready.
- Keep unresolved assumptions visible in `docs/questions.md` instead of burying them.

**Test-Authoring Instructions**
- Add only the missing high-priority tests discovered during the static audit.
- Do not broaden coverage for unrelated low-risk areas while critical gaps remain.
- Keep the final test-traceability materials honest about true no-mock HTTP coverage versus other test types.
- Do **not** run tests yet.

**Documentation Update Instructions**
- Refresh `repo/README.md`, `docs/design.md`, `docs/api-spec.md`, `docs/requirement-traceability.md`, `docs/test-traceability.md`, and `docs/questions.md` so they match the final static state exactly.
- Make the repository easy for a reviewer to inspect quickly and accurately.

**Explicit Constraints / What Not To Do**
- Do not run Docker yet.
- Do not run tests yet.
- Do not add optional features that are not required by the original prompt.
- Do not leave undocumented assumptions, service/port mismatches, or traceability gaps.
- Do not touch `sessions/` or create session-style artifacts.

**Completion Criteria**
- Every explicit original-prompt requirement is either implemented or honestly captured as an external-input assumption in `docs/questions.md`.
- Repo structure, docs, tests, Docker assets, and configs are statically consistent.
- Security-sensitive areas and requirement-to-test coverage are easy to inspect.
- The repository is ready for later execution and independent review without hidden manual steps.

**Return at the end of this prompt**
- `files created/updated`
- `requirement coverage completed`
- `deferred items`
- `docs updated`
- `test files added`
- `any assumptions added to questions.md`
