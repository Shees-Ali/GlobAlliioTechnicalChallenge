# Plan Blueprint

This is the template for every feature plan. It decides nothing about any feature. Copy it to `docs/features/NNN-name/plan.md` when a feature is picked and its `spec.md` has been reviewed, then fill it in with the project owner.

## Rules for using this blueprint
- A plan answers "how", never "what". Requirements and acceptance criteria belong in the feature's `spec.md`.
- Plan only the feature in hand. Do not design for features that have not been picked.
- Every real choice goes in the options table with the owner's decision recorded. Do not pick silently.
- Keep it short. If a section has nothing to say, write "none" and move on.
- Nothing is implemented from a plan until the owner has reviewed it.

---

## Template

# Plan: Feature NNN <name>

Implements: link to `spec.md`
Status: Draft | Reviewed by owner | Implemented

## 1. Summary
Two or three sentences: what will be built and the approach in plain words.

## 2. Technical context
Only what this feature needs. Mark anything undecided as `OPEN`.
- Language and framework:
- New dependencies (each with a reason):
- Storage:
- Testing approach:
- Constraints from the brief or the base spec:

## 3. Constitution check
Tick each principle that applies and say in one line how this plan respects it. Anything that cannot be ticked goes to section 8.
- [ ] P1 Spec first
- [ ] P2 Core has no framework dependencies
- [ ] P3 Abstractions at seams likely to change
- [ ] P4 Open for extension, closed for modification
- [ ] P5 Simplest thing that meets the brief
- [ ] P6 One command to run, one to test
- [ ] P7 Tests prove the spec
- [ ] P8 Honest scope
- [ ] P9 Process is logged
- [ ] P10 One feature at a time, chosen with the owner

## 4. Approach
- What this feature adds or changes (files, modules, interfaces). List only what the feature needs.
- Data flow for the main path, in a few lines or a small diagram.
- How it connects to what already exists.

## 5. Options and decisions
One row per real choice. The owner fills the last column.

| Decision | Options considered | Recommendation and why | Tradeoff accepted | Owner decision |
|---|---|---|---|---|
| | | | | |

## 6. Testing strategy
Which acceptance criteria map to which kind of test (unit, API, end to end, manual). Keep it to a table or short list.

## 7. Risks and open questions
Things that could go wrong or are unclear. Each open question is for the owner to answer before tasks are written.

## 8. Complexity tracking
Only if a principle is bent. State which one, why it is needed, and the simpler alternative that was rejected. Otherwise "none".

## 9. Extension notes (optional)
One or two lines on how this feature could grow later. No design work for it now.
