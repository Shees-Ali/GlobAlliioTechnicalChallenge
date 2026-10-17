# AGENTS.md

Instructions for any AI coding agent working in this repository. Tool-specific files (for example `CLAUDE.md`) import this one.

## Project
Globalli take-home: a real-time notification system for a gaming platform. The brief is summarized in `docs/spec/spec.md`. The language, structure and every design choice are decided with the project owner, feature by feature, and recorded in the decision log. Do not assume any of them.

## How this project is built
Spec-driven, in a minimal Spec Kit style, in layers. The owner makes the key decisions; the agent proposes options and tradeoffs and records what was decided.

**Base files (`docs/spec/`) are blueprints, not designs**

| File | Purpose |
|---|---|
| `constitution.md` | Principles for the whole project. |
| `spec.md` | Facts from the brief, open questions, and the feature spec template. |
| `plan.md` | Template for feature plans. |
| `tasks.md` | Feature log, delivery checklist from the brief, and the feature tasks template. |

**Feature folders (`docs/features/NNN-name/`)** hold `spec.md`, `plan.md`, `tasks.md`. A folder exists only for a feature the owner has picked.

**Layers.** The first feature establishes the baseline (project structure, modules, categories, whatever the owner decides it needs). Each later feature builds on the layers beneath it and adds only what it needs. Do not set up structure ahead of the feature that needs it.

**Decision log.** `docs/ai-process/README.md` is part of the deliverable. It records the open questions, the options considered, who decided and why. Reviewers read it to see the thought process.

## Workflow (per feature)
1. **Pick**: the owner chooses the next feature and its scope.
2. **Specify**: draft `spec.md` from the blueprint, discuss it with the owner, revise. Open questions go to the owner.
3. **Plan**: draft `plan.md` from the blueprint. Fill the options table with real options and a recommendation; the owner records the decision. Revise.
4. **Tasks**: draft `tasks.md` after the plan is reviewed.
5. **Implement** one task at a time, failing test first, minimum code to pass, run the whole suite, tick the box.
6. **Close**: fill the traceability table, update the feature log, and write the feature's decisions and any reversals to the decision log.

Draft one file at a time and wait for review before the next. Never create files for features the owner has not picked. If code and spec disagree, stop and say so; change the spec deliberately and log why.

## Commands
Python 3.12 or newer.

```
python -m venv .venv
.venv\Scripts\activate            # Windows (source .venv/bin/activate on macOS and Linux)
pip install -e ".[dev]"           # install
pytest                            # test
uvicorn notifications.api.app:app # run, then POST JSON to http://127.0.0.1:8000/events
```

## Standards that apply regardless of design
- Constitution principles apply to every feature.
- Tests prove the spec. Every acceptance criterion has at least one automated test, referenced by ID.
- Keep dependencies few and justified in the plan.
- Do not commit secrets or virtual environments.
- Do not build beyond the picked feature.

## Writing style (README, docs, commit messages, comments)
- Plain, concise English. No marketing tone.
- Do not use em-dashes. Use commas, periods or parentheses.

## Do not
- Do not decide things the owner should decide. Ask, with options and tradeoffs.
- Do not pre-create plans, specs, tasks, modules or folders for later features.
- Do not rewrite spec files to fit the code without logging the change.
- Do not create a per-feature constitution. Use the constitution check in the feature's `plan.md`.
