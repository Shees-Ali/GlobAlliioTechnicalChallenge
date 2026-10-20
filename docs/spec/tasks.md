# Tasks Blueprint

Holds the feature log, the delivery checklist taken from the brief, and the template every feature `tasks.md` copies. It contains no planned work of its own.

## Feature log
Features are chosen one at a time with the project owner. Add a row when one is picked.

| Order | Feature | Folder | Status |
|---|---|---|---|
| 1 | Event intake and dispatch | `docs/features/001-event-intake-and-dispatch/` | Implemented, amended with event-ID idempotency (decision 11) |
| 2 | User preferences | `docs/features/002-user-preferences/` | Implemented, merged to `main` |
| 3 | In-app delivery | `docs/features/003-in-app-delivery/` | Implemented, merged to `main` |
| 4 | Demonstration | `docs/features/004-demonstration/` | Implemented, awaiting owner review before commit |

## Delivery checklist (from the brief)
- [x] Project compiles and runs from a fresh clone using the provided scripts (checked in 004 on a clean copy: install, `pytest`, demo script)
- [x] Public GitHub repository (https://github.com/Shees-Ali/GlobAlliioTechnicalChallenge, 004 is on GitHub once pushed)
- [x] README explaining how to run it and the main features (`README.md`, feature 004)
- [x] AI process and prompts kept in the repo (`docs/ai-process/`)
- [x] Every required feature from the brief covered; optional ones only after (PvP, the only optional item, was not built: base Q6)

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
