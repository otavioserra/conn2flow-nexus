# Decision Log

## How to use

This file keeps implementation and product decisions traceable between rounds.

Suggested statuses:
- PROPOSED
- ACCEPTED
- REJECTED
- IMPLEMENTED
- SUPERSEDED

## Decisions

### D-001
- Status: ACCEPTED
- Topic: normative source of truth
- Decision: `specs/README.md` plus the numbered spec files are the normative source of truth for Conn2Flow Nexus.

### D-002
- Status: ACCEPTED
- Topic: incremental review model
- Decision: round feedback must live in `reviews/`, `implementation/`, `validation/`, and `change-requests/` instead of repeated rewrites of the numbered specs.

### D-003
- Status: ACCEPTED
- Topic: batch granularity
- Decision: implementation should proceed in narrow batches anchored to one concrete validation target.

### D-004
- Status: IMPLEMENTED
- Topic: first Nexus batch
- Decision: batch 001 should harden security and delivery behavior through focused automated tests before broader live-stack validation.

### D-005
- Status: ACCEPTED
- Topic: next validation layer
- Decision: after local regression hardening, the next batch should target worker/service tests and then Docker/live-stack validation.