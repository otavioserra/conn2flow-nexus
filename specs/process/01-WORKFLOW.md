# Conn2Flow Nexus SDD - Workflow

## Workflow goal

Create a clear cycle where:
- the numbered specs stay stable
- reviews happen in small rounds
- implementation happens in small batches
- validation is explicit
- decisions remain traceable

## Artifacts and ownership

### Numbered specs
Role:
- normative requirements and contracts
- acceptance basis
- implementation anchor

Typical owner:
- whoever is intentionally changing requirements
- the implementer after an approved change request

### `reviews/`
Role:
- round-based implementation feedback
- partial approvals
- non-normative comments

### `change-requests/`
Role:
- formal requirement changes
- explicit scope changes
- changes that affect the numbered specs

### `implementation/`
Role:
- break work into narrow, reviewable batches
- declare exact scope and validation target for each round

### `decisions/`
Role:
- preserve rationale and tradeoffs
- prevent repeated context loss

### `validation/`
Role:
- separate local automated checks from broader environment validation
- preserve acceptance evidence across rounds

## Collaboration modes

### Mode A - Requirement changes

Use when:
- a spec is wrong
- a new requirement appears
- an acceptance criterion must change

Flow:
1. Create a change request.
2. Review the impact.
3. Consolidate approved changes into the numbered specs.
4. Update affected batches and validation scope.
5. Implement only after the requirement change is explicit.

### Mode B - Requirement stays the same, but delivery needs review

Use when:
- the work needs approval or rejection
- you want a focused adjustment
- the next implementation step must be constrained

Flow:
1. Write a review.
2. Apply approved items to the batch.
3. Keep the numbered specs unchanged unless a real requirement changed.

### Mode C - Incremental implementation

This is the preferred operating mode.

Break work into batches such as:
- security contract hardening
- worker error handling tests
- live stack validation
- spec drift cleanup

Avoid large instructions such as:
- review the whole repo
- implement everything from the specs at once

## Suggested review markers

Use compact statuses in reviews:

- APPROVED
- ADJUST
- QUESTION
- OUT-OF-SCOPE
- DECIDED

Example:

### AUTH-01
Status: APPROVED
Comment: Production-only API key enforcement is correct.

### DEL-02
Status: ADJUST
Comment: Keep retry coverage local first; do not expand to live webhook validation in this batch.

## What happens when a review comes back

When a review is applied:
- requirement changes become change requests or numbered spec updates
- implementation-only comments stay in the batch and review artifacts
- validation scope is refreshed
- the next batch starts only after the current one is locally stable

## Ideal batch granularity

Prefer batches like:
- API key and delivery regression tests
- worker pipeline contract tests
- Docker health and live-stack validation

Do not mix all of these in the same batch unless there is a strong reason.