# Conn2Flow Nexus SDD - Start Here

This workflow package exists to avoid two common problems:

1. Rewriting the numbered spec documents for every small review comment.
2. Mixing requirement changes, implementation review, and validation notes in the same place.

## Main rule

The normative source of truth is the numbered spec set:

- `specs/README.md`
- `specs/00-system-overview.md` through `specs/10-testing.md`

Only edit those files when a requirement, contract, acceptance criterion, or approved decision really changes.

For everything else, use incremental artifacts.

## Recommended flow

### Step 1 - Review the relevant numbered specs

Read the spec files that control the slice you are working on.

Mark only:
- real ambiguity
- missing requirement
- incorrect contract
- outdated acceptance criterion
- missing decision

If the change is a real requirement change:
- create or update a file in `change-requests/`
- then ask for that change request to be consolidated into the numbered specs

If the change is only implementation feedback for the current round:
- use `reviews/`
- do not rewrite the numbered specs yet

### Step 2 - Review by batch

Read `implementation/BATCH-INDEX.md` and then open the current batch scope.

The batch defines:
- what is included now
- what is deliberately excluded
- which files are in review
- which validations must run before the batch can be considered stable

### Step 3 - Record the review round

Copy `reviews/REVIEW-TEMPLATE.md` into a new review file when needed.

Each review should answer:
- what is approved
- what still needs adjustment
- what is open but not blocking
- whether the next batch can start

### Step 4 - Apply only approved work

After the round is recorded:
- consolidate approved requirement changes into the numbered specs when needed
- implement only the approved batch scope
- update decision log and validation checklist as part of the same loop

### Step 5 - Validate before advancing

After each implementation batch:
- run focused automated validation first
- update the validation checklist
- capture unresolved items in the review or decision log
- move to the next batch only after the current one is stable

## When to edit each artifact

### Edit the numbered specs when:
- the requirement changed
- the contract changed
- an acceptance criterion changed
- a decision is finalized and must become normative

### Edit `reviews/` when:
- you want to comment on a review round
- you want to approve only part of the batch
- you want to request implementation changes without changing the normative spec

### Edit `change-requests/` when:
- expected behavior changes
- scope changes
- a new requirement must be introduced or an old one removed

### Edit `implementation/` when:
- the work must be broken into smaller batches
- the next implementation slice must be reprioritized
- the current scope or validation target needs to be clarified

### Edit `validation/` when:
- you want to record regression checks
- you want to separate local checks from live-stack/manual checks

### Edit `decisions/` when:
- a tradeoff is accepted, rejected, or postponed
- you need to keep rationale so the same discussion is not reopened blindly later

## Golden rule

If the feedback is small, do not rewrite the numbered specs.

Create an incremental artifact, keep the source of truth stable, and then re-evaluate whether a real spec change is necessary.