# Batch 001 - Security and delivery contract hardening

## Objective

Validate and harden the most concrete gap between the approved specs and the current automated safety net: API authentication and webhook delivery behavior.

## Included in this batch

- establish the Nexus incremental SDD workflow artifacts
- add focused tests for `verify_api_key()` behavior
- add focused tests for `DeliveryWorker.process_message()`
- validate retry, failure, and signature behavior with mocks only

## Not included in this batch

- worker pipeline integration tests
- Docker/live-stack validation
- streaming behavior
- renaming configuration fields for spec wording alignment

## Files in scope

- specs/README.md
- specs/process/00-START-HERE.md
- specs/process/01-WORKFLOW.md
- specs/decisions/DECISION-LOG.md
- specs/implementation/BATCH-INDEX.md
- specs/implementation/BATCH-001-current-scope.md
- specs/validation/VALIDATION-CHECKLIST.md
- tests/test_security.py
- tests/test_delivery_worker.py

## What this batch should prove

### SEC-01
Production-only API key protection is enforced exactly when configured.

### SEC-02
Non-production requests are not blocked by API key enforcement.

### DEL-01
Delivery is skipped cleanly when no webhook URL exists.

### DEL-02
Successful delivery sends the expected headers and increments the delivered metric.

### DEL-03
Repeated non-2xx webhook responses end in `delivery_failed` state and failed metrics.

## Local validations required

- `pytest tests/test_security.py tests/test_delivery_worker.py -q`
- `pytest -q`

## Local validation completed

- focused batch validation passed: `8 passed`
- full suite validation passed: `41 passed`

## Expected outcome of this round

At the end of the batch, the repo should have:
- a usable SDD operating model around the numbered specs
- focused regression coverage for security and delivery contracts
- a clean handoff into batch 002