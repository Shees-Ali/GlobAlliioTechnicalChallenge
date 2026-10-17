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

## Tools used

Updated whenever a tool is added or used differently.

| Tool | How it was used |
|---|---|
| Claude Code in the VS Code extension, model Claude Sonnet 5.5 | The only AI tool so far. Drafted the specs, plans and tasks, wrote tests and code, ran the suite, and kept the logs. It worked in one long session with the project owner. |
| `AGENTS.md` and `CLAUDE.md` | Standing instructions the agent reads at session start: spec-first workflow, one file at a time for review, test first, ask before adding dependencies, log the process. |
| Claude Code's structured question tool | Used when the agent needed an owner decision with options and tradeoffs. First use: the feature split (decision 3). Most other decisions were put as tables in chat or in the plan and answered in free text. |
| File read, write and edit tools; shell | Read the base docs at session start, wrote the docs and code, ran `pytest`, `git`, `curl` and `uvicorn`. |
| `pytest`, `uvicorn`, `curl`, a Python virtual environment | Verification. `pytest` after every task, and one hand run of the real app with `curl` before closing 001. |

Not used so far, so reviewers are not misled: subagents (the `spec-reviewer` and `test-writer` roles in CLAUDE.md), plan mode, any MCP integration, and any second AI tool. Plan mode was skipped for task 001-T1 even though it touched more than three files, because the reviewed `plan.md` and `tasks.md` already fixed the design. That was a judgment call, not an instruction followed.

How the agent was kept honest:
- Tasks T2 to T9 and T11 each started with a test that was run and seen to fail. Exceptions: T1, whose architecture test passes on an empty `core`, so it was checked by adding a probe import and seeing it fail; and T10, whose tests passed on arrival (decision 7).
- The agent stated its assumptions instead of hiding them. They are listed in decision 6.
- The owner reviewed each spec and plan before code and changed the agent's draft where it disagreed: names looked up from a user directory instead of carried in the event (4), the delivery token (5), FastAPI instead of the standard library only (6), and `httpx2` instead of `httpx` (8).

## Functional spec intake

**3. Split the functional spec component-wise into four features.**
- Prompt: the owner supplied the Initial Functional Specification (Gaming Notifications) and asked for spec documents, to be followed by non-functional specs, kept component-wise.
- Options offered: (a) four component features, (b) three flow-wise features, (c) one feature.
- Decision (owner): (a). Order: 001 event intake and dispatch, 002 user preferences, 003 in-app delivery, 004 demonstration.
- Produced: feature log rows in `docs/spec/tasks.md` and the draft `docs/features/001-event-intake-and-dispatch/spec.md`. Specs for 002 to 004 are drafted one at a time after the owner reviews the previous one.
- Mapping of functional spec acceptance scenarios: 1 to 4 to feature 001, 5 to 8 to feature 002, 9 to feature 004.
- Noted for review: the functional spec answers base open questions Q3 (Friend Accepted notifies the original requester) and Q4 (upstream decides which items qualify). Both are reflected in 001 and to be marked decided once the owner approves it. New open questions Q9 to Q12 raised in 001.

**4. Owner answers to 001 open questions.**
- Q1: no `Notification` class provided, we define our own.
- Q9: events carry IDs only. Display names come from a generalized user directory lookup, done only where the event type needs it. Reason given: the recipient arrives as an ID anyway, so a lookup is needed regardless.
- Q10: invalid events (unsupported type, missing field) are rejected with an error returned to the sender. Reason: the module is a mock of a production-grade system, and a production system should tell the producer its event was bad.
- Q11: self-targeted social events are invalid. Upstream should never allow them, so this is a defensive check.
- Q12: item names should read as words ("Sword of Azeroth"), agent to choose the exact approach. Agent proposed spaces only (Q14).
- Produced: FR-12 to FR-17 and AC-11 to AC-16 added to 001. FR-14 (unknown ID rejected) was the agent's proposal, raised as Q13.

**5. Owner confirmations and the delivery token.**
- Q13 confirmed: an unknown player ID is rejected for all event types. Reasoning from the owner: a real producer would never send an event for a non-existent user, and if someone forges one it could be malicious, so the module must reject it rather than process it.
- Q14 confirmed: spaces only.
- New from the owner: the user directory also holds each player's delivery (push) token, because the platform delivers in-app notifications to a connected client. This is why the recipient is looked up on every event. Produced FR-18 and AC-17, and revised FR-13, FR-14, AC-12 and AC-15. This extends the delivery call beyond "notification and recipient" in the functional spec, so feature 003 must specify it. New open question Q15 (player with no token).

**6. 001 spec approved, plan drafted.**
- Owner approved the 001 spec, including Q15 (no token is a valid event, outcome decided in feature 003).
- Prompt: write the plan and tasks for 001. Following the one-file-at-a-time rule, only `plan.md` was drafted, tasks wait for plan review.
- Produced: `docs/features/001-event-intake-and-dispatch/plan.md` with eight decisions marked Pending for the owner (language, raw-mapping entry point, registry of event definitions, exceptions for rejection, synchronous processing, in-memory directory, name formatting, field names).
- Decision from reviewing the draft: the owner rejected "standard library only". The module is to use FastAPI so WebSocket or other intake mechanisms can be added later. The plan now uses FastAPI in a thin `api` adapter while `core` stays free of web frameworks (P2), so a new intake is another adapter around the same `handle_event`. Dependencies updated to fastapi, uvicorn, pytest and httpx. Whether the `POST /events` route is built in 001 or left to 004 is a new Pending decision.
- Decision from the owner's question "how do we conform events to the model without Pydantic": agent offered (a) declarative field specs in core, (b) Pydantic in core, (c) Pydantic in the API only. Owner chose (a), and asked that intake and dispatch stay platform agnostic so FastAPI, WebSockets or RabbitMQ can all be adapters around the same core. Plan gained Validation and Intake neutrality sections. Spec FR-15, AC-13 and edge cases gained the unknown-extra-field rule.
- Assumed, not stated by the owner: unknown extra fields are rejected, and the `POST /events` route is built in 001. Remaining Pending plan rows were marked accepted when the owner asked for tasks. All three are to be confirmed or reversed.
- Produced: `tasks.md` with twelve test-first tasks (T1 to T12).
- Found while planning: CLAUDE.md refers to an "architecture test (AC-15)" but no spec defines it, and AC-15 in 001 means something else. Raised as risk R1 for the owner.

**7. Feature 001 implemented.**
- Owner resolved the AC-15 naming clash: AC-15 stays the unknown-player criterion, and CLAUDE.md now names the architecture test by its file (`tests/test_architecture.py`) with no AC number. Owner approved the tasks and asked for implementation.
- Built test first in twelve small commits (T1 to T12) on branch `feature/001-event-intake-and-dispatch`. Result: 207 passing tests, all 17 ACs traced to tests in the spec.
- The architecture test was checked for real by adding a probe file that imports fastapi to `core` and confirming the test failed, then removing it.
- Findings from implementing, not from the first draft:
  - The unknown-player check landed in T6 through the shared lookup helper, so the T9 unknown-player tests passed on arrival. T9's real new code was the self-target check, which runs before any directory lookup.
  - The T10 registry-wide matrix found no gaps, because the T5 validator already covered every case. It stays because it covers any future event type automatically.
  - Messages do not invent facts: the item message says "You've acquired Sword Of Azeroth!", not "legendary", since the module does not know rarity (FR-3).
  - `ConsoleDelivery` and `SAMPLE_USERS` were added so the app can run under uvicorn. They are placeholders that feature 003 and 004 replace.
  - Python 3.13 was used locally. The project requires 3.12 or newer.
- Hand-run under uvicorn: the four brief examples and two more valid events returned 200 and reached delivery with correct recipients and tokens. Self-targeted, unknown-player and unsupported-type events returned 422 with the reason code.
- Open for the owner: Starlette warns that `httpx` with its test client is deprecated and suggests `httpx2`. No change made, since the dev dependency list was approved as written.

**8. Dev dependency switched from httpx to httpx2.**
- Owner decision after the deprecation warning raised at the close of 001. `pyproject.toml` now lists `httpx2>=2.13`. The change was made and the 207 tests re-run inside the project `.venv` (checked that the interpreter prefix is `.venv`). The warning is gone.

## Prompt log

The owner's prompts that changed the direction of the work, quoted from the session (dictated, so lightly trimmed for filler). The right-hand column says what the prompt changed. Entries are added with each major decision or change.

| Decision | Owner prompt | What it changed |
|---|---|---|
| 3 | "I am providing you with the functional spec for the platform. Create relevant spec documents for the functional spec and then after that we will move on to the non-functional specs and we will keep it component-wise." | Started the work. The agent asked how to split the spec, offered three options, and the owner chose four component features. |
| 4 | "the events will not carry display names and the module will look them up from a user directory. The reason for that is that for the recipient, we are only going to receive an ID." | Added the user directory and FR-12, FR-13. Moved display names out of the event contract. |
| 4 | "if we actually receive an invalid event, we will reject and let the sending system know that the event type is invalid." | Added FR-15: invalid events are rejected with an error to the sender, not ignored or logged. |
| 5 | "the user directory will also contain ... the push notification token ... which is why I said we were looking the recipient up anywhere." | Added FR-18 and AC-17. The recipient is looked up on every event, and the delivery call carries the token. |
| 5 | "we should be rejecting that instead of processing it because that could be malicious or a threat actor could be sending that." | Confirmed FR-14: an unknown player ID is rejected for every event type, including game events. |
| 6 | "instead of it being only the standard Python library. The overall module is supposed to use FastAPI ... in future we can add WebSockets or any other mechanism for the intake" | Reversed the agent's draft. FastAPI became the framework, in a thin `api` adapter, with `core` kept framework free. |
| 6 | "How are we going to make sure that the events ... conform to the requirements ... without Pydantic" | The agent compared three validation options with tradeoffs. The owner chose declarative field specs in core. |
| 6 | "keep the intake and dispatch layer platform agnostic ... it could be WebSockets, or RabbitMQ, anything" | Added the Intake neutrality section: the core takes a mapping and raises a coded error, and each transport maps it itself. |
| 7 | "The architecture naming point should be resolved, so that the unknown player AC15 is the one that we are using ... I am happy with the task. Start with the actual implementation." | Resolved the AC-15 clash, edited CLAUDE.md, and started implementation. |
| 8 | "switch the dev dependency and make sure we are using venv" | Replaced `httpx` with `httpx2`, and the check was done inside `.venv`. |
| 9 | "The AI process record is strong on decisions but lighter on tool usage and representative prompts ... Add the actual tools used and meaningful prompt examples as the project develops" | Added the Tools used section and this log, and made the rule standing in CLAUDE.md. |

Agent prompts worth noting: the CLAUDE.md and AGENTS.md rules ("draft one file at a time", "ask before adding a dependency", "state the task ID and requirement IDs") shaped how the agent responded to every prompt above. Without them the agent would have drafted all four specs at once.
