# Validation Checklist

## Goal

Separate local automated validation from broader environment validation.

## Part A - Workflow integrity

- [x] numbered spec source of truth remains unchanged unless requirements changed
- [x] current batch is aligned with the numbered specs
- [x] decision log reflects the active implementation direction
- [x] reviewable scope is small and explicit

## Part B - Local automated checks for batch 001

- [x] `pytest tests/test_security.py tests/test_delivery_worker.py -q`
- [x] new tests are deterministic and mock-only
- [x] no production code behavior changed unintentionally

## Part C - Broader local regression

- [x] `pytest -q`

## Part D - Future live-stack validation

- [ ] `docker compose up -d`
- [ ] `docker compose ps` reports healthy services
- [ ] `GET /api/v1/health` returns healthy or expected degraded state
- [ ] submit a test task and observe worker flow
- [ ] verify webhook delivery against a controlled endpoint