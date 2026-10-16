# AI Process

This folder records how the solution is produced with AI assistance, as the brief requests.

## Decisions

**1. Use spec-driven development.**
The work is driven by written specs rather than by prompting straight to code. The approach follows GitHub Spec Kit in a minimal form: a spec, a plan and a task list for each feature, with tests proving the spec.

**2. Keep a small set of base files that set up how we work.**
- `docs/spec/constitution.md`: principles for the whole project.
- `docs/spec/spec.md`: facts from the brief, open questions, and the template for feature specs.
- `docs/spec/plan.md`: the template for feature plans.
- `docs/spec/tasks.md`: the feature log, the delivery checklist from the brief, and the template for feature tasks.
- `AGENTS.md` and `CLAUDE.md`: instructions for the AI agent.

These files set the process and make no design decisions. Features are picked one at a time with the project owner, who makes the key decisions. Each picked feature gets its own `spec.md`, `plan.md` and `tasks.md` in `docs/features/NNN-name/`.

Feature decisions are appended below as each feature is built.
