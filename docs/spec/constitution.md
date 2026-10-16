# Constitution

Principles for the whole project. They are deliberately technology-neutral: language, framework and structure are decided per feature with the project owner and logged. If a decision conflicts with a principle, the decision changes, not the principle.

## Context
Globalli take-home: a real-time notification system for a gaming platform. The brief asks for the required features first, with polish if time allows. The follow-up interview covers (1) the AI process used and (2) a defense of the architecture and its tradeoffs.

## Principles

**P1. Spec first, code second.**
Behavior is defined in a feature's `spec.md` with requirement and acceptance criteria IDs before it is coded. If code and spec disagree, change the spec deliberately and log why.

**P2. Separate business logic from delivery mechanics.**
Rules about events, notifications and preferences should be testable without a web server, a browser or real storage.

**P3. Put abstractions where change is likely.**
Introduce an interface at a seam only when a feature plan names the change it protects against. No speculative layers.

**P4. Open for extension, closed for modification.**
Adding a new kind of event, channel or category should not require rewriting existing logic. Each feature plan says how this is met.

**P5. Simplest thing that meets the brief.**
No features beyond the brief unless the owner picks them, and optional items only after the required scope is complete and tested.

**P6. Easy to run and test.**
A reviewer can clone the repo and run it and its tests by following the README, with no undocumented setup.

**P7. Tests prove the spec.**
Every acceptance criterion maps to at least one automated test, written before or together with the code it covers.

**P8. Honest scope.**
Known limitations are written down in the README, not hidden.

**P9. The process is part of the deliverable.**
Prompts, options considered, decisions, who made them and reversals are logged in `docs/ai-process/README.md`.

**P10. One feature at a time, chosen with the project owner.**
A feature gets `docs/features/NNN-name/` with `spec.md`, `plan.md` and `tasks.md` only when it is picked, written in that order and reviewed by the owner before code. The constitution stays global. Each feature plan includes a constitution check against P1 to P10, using the blueprint in `docs/spec/plan.md`.

**P11. The owner decides, the agent proposes.**
The agent presents options, tradeoffs and a recommendation. The owner chooses. The choice is logged.
