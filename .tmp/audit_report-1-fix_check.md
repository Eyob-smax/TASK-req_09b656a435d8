# Audit Report 1 Fix Check (Static Verification)

## Scope
- Verification mode: static-only
- Recheck date: 2026-04-19
- Not executed: app startup, Docker, tests, browser workflows
- Basis: re-check of the 5 issues listed in `.tmp/audit_report-1.md`

## Overall Result
- 5 / 5 issues are fixed

---

## Issue-by-Issue Recheck

### 1) Documentation and traceability out-of-sync
- Original status: Blocker
- Recheck result: **Fixed**

#### What was fixed
- `docs/requirement-traceability.md` no longer references the old forecast path and now points to `src/views/admin/ForecastView.vue`.
  - Evidence: `docs/requirement-traceability.md:183`
- `docs/design.md` now references the timestamp composable path (`composables/useTimestamp.ts`) rather than the stale `utils/datetime.ts` path.
  - Evidence: `docs/design.md:313`, `repo/frontend/src/composables/useTimestamp.ts:4`



#### Conclusion
- This issue now resolved.

---

### 2) Endpoint coverage policy overstated (missing explicit tests for key endpoints)
- Original status: High
- Recheck result: **Fixed**

#### Verification
- Admin export download is now explicitly tested (including hash and authorization checks).
  - Evidence: `repo/backend/api_tests/test_admin.py:279`, `repo/backend/api_tests/test_admin.py:292`
- Device rotate route is now explicitly tested (signed success and unsigned rejection).
  - Evidence: `repo/backend/api_tests/test_device_flow.py:326`, `repo/backend/api_tests/test_device_flow.py:371`
- Service catalog endpoint `/api/v1/services` is now explicitly tested.
  - Evidence: `repo/backend/api_tests/test_orders.py:328`, `repo/backend/api_tests/test_orders.py:333`

#### Conclusion
- The specific endpoint coverage gaps cited in report-1 are now closed.

---

### 3) Device-bound signing not consistently enforced for high-impact order/bargaining mutations
- Original status: High
- Recheck result: **Fixed**

#### Verification
- Order mutations now include signing dependencies for cancel, confirm-receipt, and advance.
  - Evidence: `repo/backend/src/api/routes/orders.py:137`, `repo/backend/src/api/routes/orders.py:153`, `repo/backend/src/api/routes/orders.py:167`
- Bargaining accept/counter/accept-counter now include signing dependency.
  - Evidence: `repo/backend/src/api/routes/bargaining.py:64`, `repo/backend/src/api/routes/bargaining.py:81`, `repo/backend/src/api/routes/bargaining.py:97`
- API spec signed-route inventory now includes these routes.
  - Evidence: `docs/api-spec.md:117`, `docs/api-spec.md:120`

#### Conclusion
- The previously identified signing-consistency gap is resolved.

---

### 4) Service catalog endpoint traceability inaccurate
- Original status: Medium
- Recheck result: **Fixed**

#### Verification
- Explicit `GET /api/v1/services` API test exists.
  - Evidence: `repo/backend/api_tests/test_orders.py:328`, `repo/backend/api_tests/test_orders.py:333`
- Traceability entry maps service endpoint to `test_orders.py`.
  - Evidence: `docs/test-traceability.md:88`

#### Conclusion
- This issue is resolved.

---

### 5) `run_tests.sh` profile flags inconsistent with compose file
- Original status: Medium
- Recheck result: **Fixed**

#### Verification
- `run_tests.sh` no longer uses `--profile build` and comments now describe default-profile behavior.
  - Evidence: `repo/run_tests.sh:11`, `repo/run_tests.sh:50`
- `docker-compose.yml` still has no `profiles` key on `frontend-builder`, which is now consistent with `run_tests.sh`.
  - Evidence: `repo/docker-compose.yml:79`

#### Conclusion
- The runbook consistency issue is resolved.

---

## Final Assessment
- Fixed: Issues 1, 2, 3, 4, 5

