@AGENTS.md

# Claude Code specifics

The shared rules live in `AGENTS.md` (imported above). This file adds only what is specific to Claude Code.

## Session start
- Read `docs/spec/constitution.md` and the feature log in `docs/spec/tasks.md` to find the current feature.
- Then read only that feature's `spec.md`, `plan.md` and `tasks.md`, plus the base blueprints in `docs/spec/` when writing a new feature file. Do not load every feature folder by default.

## Working mode
- For each task: state the task ID and the requirement IDs it covers, write the test, run it to see it fail, implement, run the full suite, then tick the checkbox in the feature's `tasks.md`.
- Use plan mode before any task that touches more than three files or changes an interface in `core`.
- Prefer small commits, one per task. Do not push unless asked.
- Ask before adding a dependency, changing a public interface, or editing the base files under `docs/spec/`. Editing the current feature's own docs is fine.
- Starting a new feature means asking the owner which feature is next, then writing its spec, plan and tasks one file at a time for review before any code. Never create files for features the owner has not picked.
- Bring key decisions and bottlenecks to the owner as questions with options and tradeoffs. Do not decide them silently.

## Process log (required)
This project is judged partly on the AI process. After any session that makes a notable decision, append to `docs/ai-process/README.md`:
- the prompt or instruction in one line (quote the owner's wording in the Prompt log table in `docs/ai-process/README.md`),
- what was produced,
- any decision that came from reviewing the output rather than the first draft,
- the tools used, if a new tool, subagent, plan mode or integration was used for the first time or differently (update the Tools used section, and say what was not used).

## Verification before saying "done"
- `pytest` passes.
- The architecture test (`tests/test_architecture.py`, no AC number, serves P2) passes.
- For API or SSE work, run the app with uvicorn and exercise the endpoint or the demo page once.
- Re-check the cited FR, NFR and AC IDs against the final behavior.

## Useful subagent roles (optional)
- **spec-reviewer**: given a task, checks the diff against the cited requirements and flags gaps or extra behavior.
- **test-writer**: given an AC, writes the failing test only.
Keep these read-only or test-only so implementation stays in the main session.
