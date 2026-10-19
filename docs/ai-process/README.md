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
| Claude Code's structured question tool | Used when the agent needed an owner decision with options and tradeoffs. Used for the feature split (decision 3) and for the three idempotency decisions (decision 11). Most other decisions were put as tables in chat or in the plan and answered in free text. |
| File read, write and edit tools; shell | Read the base docs at session start, wrote the docs and code, ran `pytest`, `git`, `curl` and `uvicorn`. |
| `pytest`, `uvicorn`, `curl`, a Python virtual environment | Verification. `pytest` after every task, and one hand run of the real app with `curl` before closing 001. |

Plan mode was used once, for the event-ID amendment (decision 11), because it changes a `core` interface and touches more than three files, as CLAUDE.md requires. The approved plan was saved and then implemented. It was skipped for task 001-T1 even though that touched more than three files, because the reviewed `plan.md` and `tasks.md` already fixed the design (a judgment call, not an instruction followed).

Not used so far, so reviewers are not misled: subagents (the `spec-reviewer` and `test-writer` roles in CLAUDE.md, and the exploration and planning agents that plan mode offers; the agent explored the code directly because it had written it in the same session), any MCP integration, and any second AI tool.

How the agent was kept honest:
- Tasks T2 to T9 and T11 each started with a test that was run and seen to fail. The same holds for T13 (validator), T14, T15, T16 (delivery failure) and T18; T17's concurrency test passed on arrival, so a control with a deliberately racy store proves it can detect a double delivery. Exceptions in the first round: T1, whose architecture test passes on an empty `core`, so it was checked by adding a probe import and seeing it fail; and T10, whose tests passed on arrival (decision 7).
- The agent stated its assumptions instead of hiding them. They are listed in decision 6.
- The owner reviewed each spec and plan before code and changed the agent's draft where it disagreed: names looked up from a user directory instead of carried in the event (4), the delivery token (5), FastAPI instead of the standard library only (6), and `httpx2` instead of `httpx` (8).

## Functional spec intake

**3. Split the functional spec component-wise into four features.**
- Prompt: the owner supplied the Initial Functional Specification (Gaming Notifications) and asked for spec documents, to be followed by non-functional specs, kept component-wise.
- Options offered: (a) four component features, (b) three flow-wise features, (c) one feature.
- Decision (owner): (a). Order: 001 event intake and dispatch, 002 user preferences, 003 in-app delivery, 004 demonstration.
- Produced: feature log rows in `docs/spec/tasks.md` and the draft `docs/features/001-event-intake-and-dispatch/spec.md`. Specs for 002 to 004 are drafted one at a time after the owner reviews the previous one.
- Mapping of functional spec acceptance scenarios: 1 to 4 to feature 001, 5 to 8 to feature 002, 9 to feature 004.
- Noted for review: the functional spec answers base open questions Q3 (Friend Accepted notifies the original requester) and Q4 (upstream decides which items qualify). Both are reflected in 001 and were marked decided once the owner approved it (decision 10). New open questions Q9 to Q12 raised in 001.

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
- Assumed, not stated by the owner: unknown extra fields are rejected, and the `POST /events` route is built in 001. Remaining Pending plan rows were marked accepted when the owner asked for tasks. All three were approved with the tasks and are marked as such in the plan (decision 10).
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
- Raised for the owner, resolved in decision 8: Starlette warns that `httpx` with its test client is deprecated and suggests `httpx2`. No change made, since the dev dependency list was approved as written.

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
| 10 | "Once you are done with this clean any pending or stale decisions, from these specs so that you know it is clean and finalized. Up until this point." | Triggered the sweep in decision 10: no pending items remain in the 001 spec, plan or tasks, and the base open-question table shows real statuses. |
| 11 | "is our event intake pipeline idempotent?" then "Yes, I would like an event ID to the payload because that is the very critical requirement. And log this decision to add an idempotency key which is going to be the event ID. And plan what would change and what files would change and tell me." | Found the intake was not idempotent. Plan mode, three owner decisions, then an amendment to 001. See decision 11. |
| 12 | "Let's move on to feature 002." | Started 002. The agent asked four preference questions before drafting, and the owner took all four recommendations. See decision 12. |
| 13 | "This is the functional spec, store it in docs to reference for future sessions and close the scenarios questions." | Saved the functional spec to `docs/functional-spec.md`. Checking it against the draft found the "no replay" gap, which became FR-36. See decision 13. |
| 14 | "let's plan out and clear the questions." | The agent drafted the 002 plan and put its four main design choices to the owner, who took all four recommendations. See decision 14. |
| 15 | "implement but do not commit I will review first" | All seven tasks implemented with failing tests first, nothing committed. Plan mode was used for T2. See decision 15. |

Agent prompts worth noting: the CLAUDE.md and AGENTS.md rules ("draft one file at a time", "ask before adding a dependency", "state the task ID and requirement IDs") shaped how the agent responded to every prompt above. Without them the agent would have drafted all four specs at once.

**10. Spec cleanup, 001 closed out.**
- Prompt: clean pending or stale decisions from the specs so they are final up to this point (quoted in the Prompt log).
- Method: searched all docs for "Pending", "assumed", "to be confirmed", "proposed", "TBD" and "Open", then read the plan and spec in full.
- Changed in the 001 plan: the three "assumed" or "accepted without objecting" decision rows are now recorded as approved with the plan and tasks (the owner reviewed T5, T10 and T11, which build those choices, and said to start implementation). Risks R1 to R3 are recorded as resolved. The "needs owner approval" and "after the owner decides" wording is gone. Two "(proposed)" headings are now plain. The file list now matches the code (`sample_users.py`, `console_delivery.py`, test fakes). The "if the owner accepts the adapter" condition is removed.
- Changed in the 001 spec: the two "proposed" and "to be confirmed" edge cases are final, and the Open questions block (an empty table header) is replaced by a table of Q1, Q3, Q4 and Q9 to Q15 with each resolution and the FR it landed in.
- Changed in `tasks.md`: the stale `httpx` mention became `httpx2`.
- Changed in the base `docs/spec/spec.md` (edited at the owner's request): the open-question table now has a Status column. Q1 to Q4 are marked decided. Q5 to Q8 stay open, each with the feature that settles it.
- One thing to be honest about: the owner approved the three assumed items by approving the tasks, not by answering each one. That is recorded as it happened.
- Left unchanged on purpose: history in decisions 3 to 9 (they describe what was pending at the time), the FR-18 environment assumption that the platform delivers in-app, and the blueprints' own `OPEN` marker guidance.

**11. Event ID as the idempotency key (amendment to 001).**
- Trigger: the owner asked whether the intake is idempotent. It was not: the same valid event submitted twice produced two notifications and two delivery calls, because payloads had no ID and the module kept no state. This was a documented edge case, deferred by the functional spec (section 6). The owner called an event ID "a very critical requirement".
- Process: the agent stated what was and was not idempotent (rejections are, valid events were not), offered three options (leave deferred, producer-supplied event ID with a store, dedup in the HTTP adapter only), and recommended the second. The owner chose it and asked for a plan of what would change. The agent used plan mode, asked three questions, and wrote an approved plan before touching any file.
- Owner decisions: (1) amend 001 rather than create a new feature; (2) claim the ID just before delivery and release it if delivery fails, so concurrent copies cannot both deliver and failed deliveries can be retried; (3) the same ID with different content is treated as a duplicate. The event ID alone is the key.
- Not asked, decided by the agent and recorded in the plan: the ID is a non-blank string of at most 128 characters; the in-memory store is bounded to 10,000 IDs and drops the oldest; a duplicate returns success (`200` with `{"status": "duplicate"}`), not an error; a rejected event never uses up its ID.
- Produced: FR-19 to FR-25 and AC-18 to AC-26 in the 001 spec; a third seam `ProcessedEvents` with an in-memory implementation; `handle_event` now returns an `Outcome`; seven tasks (T13 to T19), each a commit. 306 tests pass.
- Findings from implementing, not from the plan:
  - The shared `service` fixture replaced five copies of the same fixture in the test modules, because the constructor change would have needed editing all of them.
  - The AC-22 tests (rejected events do not use up their ID) passed as soon as the claim was placed after validation. Only the delivery-failure tests needed the release code.
  - The concurrency test (AC-25) passed on arrival because the store's claim is atomic, so a control with a racy store was added to prove the test can fail.
  - The default app builds its service at import, so wiring the store into it had to happen in T15, earlier than the HTTP change in T18.
- Hand run under uvicorn: the same level-up twice returned `processed` then `duplicate` with one delivery. A new ID with identical content was delivered. A reused ID with different content returned `duplicate`. A missing or blank `event_id` returned `422`. An unknown-player event followed by its corrected resend with the same ID returned `422` then `processed`. Five deliveries were logged for five distinct processed events.
- Consequences recorded for later features: feature 003 must keep "delivery raises to signal failure", because releasing the ID depends on it. Feature 002 must decide whether a preference-suppressed event uses up its ID (recommended: yes). The README must list the limits: IDs are lost on restart and not shared across processes, a crash between claim and delivery can lose that notification, a reused ID is silently a duplicate, and a dropped ID can be processed again.

## Feature 002: User preferences

**12. Four owner decisions before the 002 spec was drafted.**
- Prompt: "Let's move on to feature 002." (quoted in the Prompt log).
- Process: the agent read the 001 spec, the service code and the decision log first. It found that the functional spec is not in the repo, so it could not see scenarios 5 to 8. Rather than draft and then rewrite, it asked four questions with the structured question tool, each with options and a recommendation.
- Owner decisions (all four recommendations accepted): (1) a missing setting is on, so a new player gets everything; (2) a suppressed event returns a new `suppressed` outcome as a success, like `duplicate`; (3) a suppressed event uses up its `event_id`, which settles the consequence left open in decision 11; (4) preferences change through a core call plus a thin HTTP route.
- Tradeoffs named to the owner: a `suppressed` status tells the producer about the player's preference (a mild information leak), and opt-out by default means a player must act to stop notifications.
- Produced: draft `docs/features/002-user-preferences/spec.md` with FR-26 to FR-35 and AC-27 to AC-38. FR-32 refines the wording of FR-21 in 001 (an ID is used up whether the event is delivered or suppressed). Open questions Q5 (granularity), Q19 (match against functional spec scenarios 5 to 8) and Q20 (reading preferences over HTTP).

**13. Functional spec saved to the repo, 002 open questions closed.**
- Prompt: "let's plan out and clear the questions", then, after the agent asked how to check scenarios 5 to 8, the owner asked which scenarios were meant, and then pasted the functional spec (quoted in the Prompt log).
- Found: the functional spec given in the 001 session was never saved to the repo, so the 002 draft cited scenarios the agent could not see. The agent said so rather than guess, offered a reconstruction, and the owner pasted the original. It is now kept verbatim at `docs/functional-spec.md`, and `AGENTS.md` points to it.
- Owner decisions: Q5, per category only. Q20, no read route in 002.
- Decision from reviewing against the source, not from the first draft: scenarios 5 to 7 were already covered, but scenario 8 ("without replaying suppressed events") was only an edge case with no requirement or test. FR-36 was added and AC-35 widened to prove it. FR-27 now also says one player's settings do not affect another, matching section 5 of the functional spec. The spec now lists which AC covers each scenario.
- Noted, not changed: the functional spec's example message says "legendary Sword of Azeroth". The module still does not say "legendary", because it does not know rarity (decision 7, FR-3).

**14. 002 plan drafted, four design decisions.**
- Prompt: "let's plan out and clear the questions" (quoted in the Prompt log).
- Produced: draft `docs/features/002-user-preferences/plan.md`, with the options table put to the owner through the structured question tool.
- Owner decisions (all recommendations accepted): (1) a new `PreferenceStore` seam rather than a field on `UserRecord` or a dict in the service; (2) a separate `PreferenceService` in core that validates a raw mapping, so the route holds no rules; (3) `PUT /preferences` with player, category and value in the JSON body, chosen over a RESTful path because FastAPI would otherwise parse the path ID and return its own error format; (4) a new `InvalidPreferenceError` beside `InvalidEventError`.
- Found while planning, not in the spec: once the preference read sits after the event-ID claim, a failing store would use up the ID without delivering. The plan widens the release-on-failure `try` to cover everything after the claim, and adds a test for it.
- Then approved by the owner: the store returns only the recorded map and core applies the default ("yes as by default all notifications would be on"), and the store is a required constructor argument. Spec and plan marked reviewed. Produced: `tasks.md` with seven test-first tasks (T1 to T7). T2 changes the `NotificationService` constructor, so it is marked to run in plan mode first.

**15. Feature 002 implemented, left uncommitted for owner review.**
- Prompt: "implement but do not commit I will review first" (quoted in the Prompt log). This overrides the CLAUDE.md habit of one commit per task, so all of T1 to T7 sit in the working tree.
- Plan mode was used for T2, as CLAUDE.md requires, because it changed the `NotificationService` constructor (a `core` interface) and touched more than three files. The owner approved the short plan before any edit.
- Result: 362 passing tests (306 before 002). All twelve ACs (AC-27 to AC-38) are traced to tests in the spec.
- Test-first record: T1, T2, T3, T5 and T6 each started with a test run and seen to fail. In T4, the AC-34 test passed on arrival because T3 already claimed the ID before the check, as the tasks file predicted. The failing-store test was the one seen to fail, and it drove the code change.
- Findings from implementing, not from the plan:
  - The release-on-failure `try` now covers the preference read and the building of the notification as well as delivery, so a failing store gives the ID back.
  - The notification is now built after the preference check, matching the functional spec's flow (check preferences, then create the notification), so a suppressed event never builds a message.
  - One 001 test, `test_error_codes` in `tests/core/test_notification.py`, lists the exact set of error codes, so it was updated to add `UNSUPPORTED_CATEGORY`. This is the only edit to a 001 test's expectations.
  - The JSON-decoding step in the HTTP adapter is now shared by both routes.
- Hand run under uvicorn: Level Up processed; Game off; Level Up suppressed; Friend Request to the same player processed; Level Up for player 2 processed; Game on; resend of the suppressed ID duplicate; new Level Up processed; unsupported category and unknown player both 422; an invalid event with Game off 422, not suppressed. The console delivery logged exactly four deliveries, and the suppressed event was never delivered.
- For the README at packaging: preferences are in memory and lost on restart, and `PUT /preferences` has no authentication.
