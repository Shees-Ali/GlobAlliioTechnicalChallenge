# Tasks Blueprint

Holds the feature log, the delivery checklist taken from the brief, and the template every feature `tasks.md` copies. It contains no planned work of its own.

## Feature log
Features are chosen one at a time with the project owner. Add a row when one is picked.

| Order | Feature | Folder | Status |
|---|---|---|---|
| 1 | Event intake and dispatch | `docs/features/001-event-intake-and-dispatch/` | Implemented, amended with event-ID idempotency (decision 11) |
| 2 | User preferences | `docs/features/002-user-preferences/` | Spec and plan reviewed, tasks drafted |
| 3 | In-app delivery | `docs/features/003-in-app-delivery/` | Picked, spec not started |
| 4 | Demonstration | `docs/features/004-demonstration/` | Picked, spec not started |

## Delivery checklist (from the brief)
- [ ] Project compiles and runs from a fresh clone using the provided scripts
- [ ] Public GitHub repository
- [ ] README explaining how to run it and the main features
- [ ] AI process and prompts kept in the repo (`docs/ai-process/`)
- [ ] Every required feature from the brief covered; optional ones only after

## Feature tasks blueprint
Copy to `docs/features/NNN-name/tasks.md` after the feature's plan is reviewed by the owner.

```
# Tasks: Feature NNN <name>

- [ ] NNN-T1 <small, test-first step> (FR-x, AC-y)
- [ ] NNN-T2 ...

## Done when
Every AC in the feature spec has a passing test, the traceability table is filled in,
earlier tests still pass, and the decision log has the feature's decisions.
```

Rules: each task is small enough to finish and review on its own, cites the requirement and AC IDs it serves, and starts with the failing test.
