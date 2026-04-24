# 📋 Conn2Flow Nexus AI — Specifications (SDD)

> **Spec-Driven Development (SDD)**: In this project, specifications are the **single source of truth**.
> All implementation, testing, and documentation derive from these artifacts.
> Every change starts here — spec first, then code.

## Methodology

This project adopts **SDD Spec-Anchored**:

1. **Spec-first**: Specifications are written before code
2. **Spec-anchored**: Specs live in the repository and evolve with the code
3. **Versioned**: Specs live in Git alongside the source code

### Lifecycle

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Specify    │───▶│    Plan     │───▶│    Task     │───▶│  Implement  │
│  (define)    │    │  (plan)     │    │ (decompose) │    │   (code)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       ▲                                                        │
       └────────────────── Feedback Loop ──────────────────────┘
```

### Rules

- **Never** change code without updating the corresponding spec
- Every PR must include spec changes when applicable
- Specs use declarative language (what, not how)
- Specs define contracts — the implementation may vary

## Source of Truth

The numbered spec set is the normative source of truth for the Nexus system:

- `specs/README.md` is the entry point and index
- `specs/00-system-overview.md` through `specs/10-testing.md` define behavior, contracts, and acceptance
- Incremental process artifacts exist to avoid rewriting the normative specs on every review round

Only update the numbered specs when a requirement, contract, acceptance criterion, or approved product/technical decision actually changes.

## Operational SDD Workflow

The project now uses an incremental SDD operating model around the approved specs:

| Artifact | Purpose |
|----------|---------|
| [process/00-START-HERE.md](./process/00-START-HERE.md) | Entry point for how to work with the spec set |
| [process/01-WORKFLOW.md](./process/01-WORKFLOW.md) | Review, change, and implementation flow |
| [change-requests/CHANGE-REQUEST-TEMPLATE.md](./change-requests/CHANGE-REQUEST-TEMPLATE.md) | Formal spec-change template |
| [decisions/DECISION-LOG.md](./decisions/DECISION-LOG.md) | Decision history and rationale |
| [implementation/BATCH-INDEX.md](./implementation/BATCH-INDEX.md) | Active and upcoming implementation batches |
| [reviews/REVIEW-TEMPLATE.md](./reviews/REVIEW-TEMPLATE.md) | Round-based review template |
| [validation/VALIDATION-CHECKLIST.md](./validation/VALIDATION-CHECKLIST.md) | Local, automated, and manual validation checklist |

This keeps the core specs stable while still allowing iterative review, batching, validation, and traceable decisions.

## Specification Index

| #  | Document | Description |
|----|----------|-------------|
| 00 | [system-overview.md](./00-system-overview.md) | System overview, purpose, and context |
| 01 | [architecture.md](./01-architecture.md) | System architecture, components, and data flow |
| 02 | [api-contract.md](./02-api-contract.md) | REST API contract (endpoints, schemas, status codes) |
| 03 | [event-schemas.md](./03-event-schemas.md) | Kafka event schemas (topics, payloads) |
| 04 | [data-models.md](./04-data-models.md) | Data models (Redis, Pydantic, state) |
| 05 | [llm-routing.md](./05-llm-routing.md) | Multi-model routing, fallback, and LLM providers |
| 06 | [worker-pipeline.md](./06-worker-pipeline.md) | Processing pipeline (LangGraph, workers, webhooks) |
| 07 | [infrastructure.md](./07-infrastructure.md) | Docker, compose, networking, volumes, healthchecks |
| 08 | [security.md](./08-security.md) | Authentication, HMAC, CORS, general security |
| 09 | [configuration.md](./09-configuration.md) | Environment variables, settings, validation |
| 10 | [testing.md](./10-testing.md) | Testing strategy, coverage, fixtures |

## Status

| Spec | Status | Version | Last Updated |
|------|--------|---------|--------------|
| 00 - System Overview | ✅ Approved | 1.0.0 | 2025-07-16 |
| 01 - Architecture | ✅ Approved | 1.0.0 | 2025-07-16 |
| 02 - API Contract | ✅ Approved | 1.0.0 | 2025-07-16 |
| 03 - Event Schemas | ✅ Approved | 1.0.0 | 2025-07-16 |
| 04 - Data Models | ✅ Approved | 1.0.0 | 2025-07-16 |
| 05 - LLM Routing | ✅ Approved | 1.0.0 | 2025-07-16 |
| 06 - Worker Pipeline | ✅ Approved | 1.0.0 | 2025-07-16 |
| 07 - Infrastructure | ✅ Approved | 1.0.0 | 2025-07-16 |
| 08 - Security | ✅ Approved | 1.0.0 | 2025-07-16 |
| 09 - Configuration | ✅ Approved | 1.0.0 | 2025-07-16 |
| 10 - Testing | ✅ Approved | 1.0.0 | 2025-07-16 |

## How to Use

### For Developers

1. **Before coding**: Read the spec corresponding to the feature
2. **When implementing**: Verify the code meets the spec
3. **When testing**: Use the spec as reference for test scenarios
4. **When reviewing**: Use the batch, review, decision, and validation artifacts instead of rewriting the numbered specs prematurely

### For AI (Coding Agents)

1. Read `specs/README.md` for general context
2. Read the specific spec before generating code
3. Validate generated code against the spec
4. Never generate code that contradicts an approved spec
5. Use the incremental workflow artifacts to record review feedback, scope the next batch, and separate spec changes from implementation comments
