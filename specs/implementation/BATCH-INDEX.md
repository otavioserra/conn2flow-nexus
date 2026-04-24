# Batch Index

## How to use

Each batch is a small review and implementation unit.

Rule:
- do not open the next batch before the current one is locally stable and reviewable

## Batches

### BATCH-001 - Security and delivery contract hardening
- Status: LOCAL VALIDATION COMPLETE
- Focus:
  - API key enforcement behavior
  - delivery worker success/failure behavior
  - retry handling and signature header assertions
  - local validation for the new regression slice
- File: implementation/BATCH-001-current-scope.md

### BATCH-002 - Worker pipeline service tests
- Status: PENDING
- Focus:
  - task processor behavior
  - Redis/Kafka service-level tests
  - alignment with specs/06-worker-pipeline.md and specs/10-testing.md

### BATCH-003 - Live stack validation and spec drift check
- Status: PENDING
- Focus:
  - Docker Compose health validation
  - API to worker smoke flow
  - config/spec drift review