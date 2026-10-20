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
| Claude Code in the VS Code extension, model Claude Sonnet 5.5 | The main AI tool in the repository. Drafted the specs, plans and tasks, wrote tests and code, ran the suite, and kept the logs. It worked in one long session with the project owner. |
| `AGENTS.md` and `CLAUDE.md` | Standing instructions the agent reads at session start: spec-first workflow, one file at a time for review, test first, ask before adding dependencies, log the process. |
| Claude Code's structured question tool | Used when the agent needed an owner decision with options and tradeoffs. Used for the feature split (decision 3) and for the three idempotency decisions (decision 11). Most other decisions were put as tables in chat or in the plan and answered in free text. |
| File read, write and edit tools; shell | Read the base docs at session start, wrote the docs and code, ran `pytest`, `git`, `curl` and `uvicorn`. |
| `pytest`, `uvicorn`, `curl`, a Python virtual environment | Verification. `pytest` after every task, and one hand run of the real app with `curl` before closing 001. |
| Claude Code, model Claude Opus 5.5 (from feature 004) | Feature 004 was planned and built with Opus 5.5 instead of Sonnet 5.5, in the same VS Code extension and under the same `AGENTS.md` and `CLAUDE.md` rules. |
| Throwaway probe scripts in the agent's scratch folder | Used in 004 to check that tests and fixes really work: a deliberately racy `subscribe` to prove the concurrency test can fail, and an in-process uvicorn server to watch a real disconnect release a feed. Not kept in the repo. |
| Codex, in a separate chat | A second AI tool, used outside the repository workflow (decisions 30 to 32, recorded retrospectively). Before the repository work: reviewed the challenge for easily missed requirements, helped the owner write the initial functional specification, and brainstormed system boundaries with the owner. After the implementation: independent read-only reviews of the repository, including a fresh-clone install and test run, which found four issues (decision 32). Codex made no edits to application code, feature specs or tests. |
| Claude in Chrome (MCP) | Used for 004's browser check of the demo page (AC-60, decision 29). It was not connected on the first try (decisions 27 and 28), and the owner connected it. The agent drove the real page: clicks for the checkboxes and the resend button, and the page's own form handlers for the six event types. |

Plan mode was used four times, each time because the change touched a `core` interface or more than three files, as CLAUDE.md requires: the event-ID amendment (decision 11), 002-T2 (decision 15), 003-T2 (decision 20) and 004-T4 (decision 27). Each plan was approved by the owner and then implemented. It was skipped for task 001-T1 even though that touched more than three files, because the reviewed `plan.md` and `tasks.md` already fixed the design (a judgment call, not an instruction followed).

Not used, so reviewers are not misled: subagents (the `spec-reviewer` and `test-writer` roles in CLAUDE.md, and the exploration and planning agents that plan mode offers; the agent explored the code directly because it had written it in the same session). One second AI tool was used, Codex, in a separate chat for brainstorming the requirements and for independent read-only review (decisions 30 to 32). One MCP integration was used: Claude in Chrome, for the 004 browser check (decision 29).

How the agent was kept honest:
- Tasks T2 to T9 and T11 each started with a test that was run and seen to fail. The same holds for T13 (validator), T14, T15, T16 (delivery failure) and T18; T17's concurrency test passed on arrival, so a control with a deliberately racy store proves it can detect a double delivery. Exceptions in the first round: T1, whose architecture test passes on an empty `core`, so it was checked by adding a probe import and seeing it fail; and T10, whose tests passed on arrival (decision 7).
- Features 002 to 004 followed the same rule. Where a test passed on arrival, the agent broke the code on purpose from a backup copy, or used a throwaway probe, to show the test can fail (decisions 20 and 27). In 004 this caught a concurrency test that could never fail.
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
| 16 | "merge the changes back into main I have commited then then we will move to the 3rd feature" | 001 and 002 merged into `main` as two merge commits. Started 003 with four delivery questions. See decision 16. |
| 17 | "yes a blank token will count as no token, yes for now keep it at 100, and in a constant variable, yes for Q23 as well" | Closed Q21 to Q23. Added FR-46, FR-47 and AC-49 to AC-51. See decision 17. |
| 18 | "Does this mean that when a undelivered request is sent again it won't be delivered to the user? we need to make sure that we sent it", then "Nevermind the undelivered should consume event id based on the assumption that the notification history is mainatined, otherwise once the user gets the token they will get a lot of popups aat once since they are in game notifcations" | The owner challenged FR-41, weighed three options and kept it, adding the reason and the history assumption to the spec. See decision 18. |
| 19 | "draft the plan" | Spec taken as approved. Draft 003 plan with six decisions pending. See decision 19. |
| 20 | "Implement" | All six 003 tasks implemented test first, nothing committed. Plan mode for T2. Probes showed the tests that passed on arrival can fail. See decision 20. |
| 21 | "Let's move on to te last feature" | Started 004 on its own branch. The agent asked four questions before drafting, and the owner took all four recommendations. See decision 21. |
| 22 | "This does not mean that the user receives the event that they missed when they had no token, make sure of this. We need to avoid uneccesary popups in case of a late connect in a real scenario." | Accepted Q26 with a condition. Added FR-60 (feed items marked history or live) and AC-62 (no backlog after a token is issued). See decision 22. |
| 23 | "Q27 sounds good, a new dependency just to showcase a simple scenario is not justfied, automated tests already validate the functionality. Q28 Yes by token not by player id similar way a firebase push token works. Q29 Self contained" | Closed Q27 to Q29 as recommended. See decision 23. |
| 24 | "yes snake case with a camelcase comment in docs and file" | Closed Q25. Producers use snake_case, with the brief's camelCase names in a source comment and the README. See decision 24. |
| 25 | "yes draft it" | Spec taken as approved. Draft 004 plan with seven decisions pending. See decision 25. |
| 26 | "sounds good work on tasks" | Accepted D1 to D7 as recommended. Plan marked reviewed. Draft 004 tasks with eight test-first tasks. See decision 26. |
| 27 | "Implement and leave everything for review" | T1 to T7 implemented test first, nothing committed. Plan mode for T4. A probe showed the first concurrency test could not fail, and it was fixed. See decision 27. |
| 28 | "yes update the shared files and readme, and close any open questions. And then run a pass through the repo to make sure everything is marked close" | Base files updated with the owner's OK, Q6 and Q8 closed, checklist ticked after checking each item, stale statuses and tool notes fixed. The browser check stays open as 004-T9. See decision 28. |
| 29 | "I have run them but do a pass using the browser extension yourself as well once" | The owner ran the browser check, and the agent ran it again through Claude in Chrome. AC-60 and 004-T9 closed. See decision 29. |
| 33 | "Do it in main and leave them uncommited for me to review", then "Skip 4 I will later ask codex to do it do 1,2 and 3" | Claude Code fixed three of the four issues from the Codex review (decision 32) on `main`, test first, uncommitted. The AI log item was left to the owner and Codex. See decision 33. |
| 34 | "This was the review from another agent analyze this and validate", then "Let's go with sync routes and remove async since it is not needed ... We will also add B with the minimum changes and make sure that there is a proper lifecycle. And we will also add event ID to notification ... Bound our queue for feed in the channel itself. And in the docs, as a one page final architecture session, correcting the mistakes and also add a architecture diagram" | Claude Code reproduced the external review's findings by probe, then fixed A to D test first on `main`, uncommitted, and added `docs/architecture.md`. The owner corrected the agent's plan where it overstated the delivery guarantee. See decision 34. |

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

## Feature 003: In-app delivery

**16. Merge to main, four owner decisions before the 003 spec.**
- Prompt: "merge the changes back into main I have commited then then we will move to the 3rd feature" (quoted in the Prompt log).
- Merge: 001 had never been merged into `main`, so the agent merged the 001 branch and then the 002 branch, each with `--no-ff`, giving `main` one merge commit per feature. The suite passed on `main` (362 tests). Nothing was pushed. Branch `feature/003-in-app-delivery` was cut from `main`.
- Found while preparing 003: a delivery failure today reaches an HTTP producer as a bare `500`, which does not say whether a retry can help.
- Owner decisions (all four recommendations accepted, structured question tool): (1) a recipient with no token gets a new `undeliverable` outcome, a success, and the ID is used up (settles Q15); (2) the simulated channel is an in-memory record per token, with live push left to 004 (settles the mechanism half of Q7); (3) one delivery attempt and the producer retries, with no internal retries or queue (settles the guarantee half of Q7); (4) a delivery failure over HTTP is `503` with `DELIVERY_FAILED`.
- Produced: draft `docs/features/003-in-app-delivery/spec.md` with FR-37 to FR-45 and AC-39 to AC-48, and open questions Q21 (blank token), Q22 (bounded channel) and Q23 (a way to make the simulated channel fail on purpose for the demo).
- Agent choice put in the spec for review, not asked: the preference check comes before the token check, so an event the player turned off is suppressed whether or not they have a token (FR-42).

**17. 003 open questions closed.**
- Prompt quoted in the Prompt log. All three agent recommendations were accepted, and the owner added one detail: the per-token limit of 100 is held in a named constant.
- Q21: a blank token counts as no token (FR-40 widened, AC-49).
- Q22: the simulated channel keeps the 100 most recent notifications per token and drops the oldest (FR-46, AC-50).
- Q23: the simulated channel can be built with unreachable tokens that raise a delivery error, so the `503` path can be shown by hand and in the demo (FR-47, AC-51).

**18. FR-41 challenged and kept (Q24).**
- The owner questioned FR-41: an undeliverable event uses up its ID, so a resend after the player gets a token is a duplicate and never delivered.
- The agent confirmed that reading and admitted the flaw in its own reasoning: it had treated "no token" like "category turned off", although the player did not choose to miss it. It offered (a) release the ID so the producer can resend, (b) hold undelivered notifications and send them when the player connects, (c) keep FR-41.
- Owner decision: (c). In-app notifications are in-game popups, so sending a backlog on connect would hit the player with many popups at once. The platform is assumed to keep a notification history the player can look back through, so nothing is lost.
- Produced: FR-41 now states the reason, the history assumption is listed under "Not in this feature", and Q24 records the question.

**19. 003 plan drafted.**
- Prompt: "draft the plan". Taken as approval of the spec, which is marked reviewed.
- Produced: draft `docs/features/003-in-app-delivery/plan.md`. Six decisions are left Pending for the owner: no-token check in core, `str`-only token in the delivery contract, a typed `DeliveryError` (other exceptions stay `500`), two new sample users (5 with no token, 6 unreachable), removing `ConsoleDelivery`, and the limit constant in the channel module.
- Found while planning: 001's Q15 test asserts that delivery receives `None` for a player with no token. 003 changes that on purpose, so the test will be rewritten to expect `UNDELIVERABLE` (R7).
- Owner decisions on the plan (structured question tool, all recommendations accepted): "no token" is decided in core and the delivery contract takes a `str` token only; only a typed `DeliveryError` becomes `503`, other exceptions stay `500`; players 5 (no token) and 6 (unreachable token) are added to the sample users; tests reach the default app's channel through `app.state.channel`, and a read route stays with 004.
- The owner then approved the last two: `ConsoleDelivery` is removed and the channel does the logging, and `MAX_NOTIFICATIONS_PER_TOKEN = 100` lives in the channel's module. Plan marked reviewed. Produced: `tasks.md` with six test-first tasks. T2 changes the `NotificationDelivery` signature, so it is marked to run in plan mode first.

**20. Feature 003 implemented, left uncommitted for owner review.**
- Prompt: "Implement". Following the owner's standing preference from 002, nothing was committed.
- Plan mode was used for T2, because it changed the `NotificationDelivery` signature (a `core` interface) and touched more than three files. The owner approved the short plan first.
- Result: 385 passing tests (362 before 003). All thirteen ACs (AC-39 to AC-51) are traced to tests in the spec.
- Test-first record: T1, T2, T4 and T5 started with failing tests. The AC-43 test (suppressed beats undeliverable) passed on arrival, because the preference check already came first. In T4, the `undeliverable` answer and the `500` for other exceptions also passed on arrival, as the plan expected (no new code for either).
- All four T3 tests passed on arrival, as the tasks file predicted. To show they can still fail, the agent made two temporary deliberate breaks in `service.py`, working from a backup copy: releasing the ID on undeliverable (caught by the AC-42 test) and not releasing it on failure (caught by the AC-44 test). The file was restored and checked for leftovers. This is the same idea as the racy-store control in 001, done without keeping the broken code.
- Findings from implementing, not from the plan:
  - The service passes the token on unchanged, not a stripped copy, so a channel gets exactly what the directory holds. The blank check only decides whether to deliver.
  - 001's Q15 test was renamed and now expects `UNDELIVERABLE` (planned as R7). `test_error_codes` gained `DELIVERY_FAILED`. These are the only changed expectations in earlier tests.
  - `git rm` staged the removal of `console_delivery.py`. It was unstaged so that every change sits unstaged for the owner's review.
- Hand run under uvicorn: player 1 processed and logged by the channel; player 5 (no token) undeliverable; player 6 (unreachable) `503 DELIVERY_FAILED`, and its resend `503` again, which shows the ID was released; player 5's resend duplicate; Game off for player 5, then a new event suppressed; a Friend Request to player 5 undeliverable; one from player 5 to player 1 processed. The channel logged exactly two deliveries, both to player 1.
- For the README at packaging: the channel is in memory, keeps 100 notifications per token, and simulates unreachable tokens; the notification history is assumed to live outside the module.
- Base open questions Q5 and Q7, and 001's Q15, were settled in 002 and 003 but still showed as open. `docs/spec/spec.md` is a base file, so the agent asked before editing it. The owner said "Yes mark them as decided": Q5 and Q7 are now decided in the base table, and Q15's row in the 001 spec points to 003 FR-40 and FR-41. Q15 was never in the base table, because it was raised inside 001.

## Feature 004: Demonstration

**21. Four owner decisions before the 004 spec.**
- Prompt: "Let's move on to te last feature" (quoted in the Prompt log). 004 was already picked in the feature log, so the agent cut `feature/004-demonstration` from `main` and read the brief and functional spec sections that 004 serves (the brief's four example calls, scenario 9).
- Owner decisions (all four recommendations accepted, structured question tool): (1) the demo is a script plus a live page served by the same app, which settles the demo half of base Q2; (2) simulated producers take an injected submit function, so they stay transport neutral like the 001 intake; (3) live push to the page is Server-Sent Events, chosen over WebSocket (needs an extra dependency, and two-way is not needed) and polling (not real-time); (4) the README is part of 004, which settles Q8.
- Produced: draft `docs/features/004-demonstration/spec.md` with FR-48 to FR-59, AC-52 to AC-61, and open questions Q25 (producer method names), Q26 (feed receives history on connect), Q27 (how the page is tested without a browser framework), Q28 (feeds by token or player ID) and Q29 (page fires events or only watches).
- Not used: subagents and plan mode. The spec is one file, drafted for review.

**22. Q26 accepted with a condition: history on connect is not a replay.**
- Prompt quoted in the Prompt log. The owner accepted the recommendation that a feed receives what the channel already holds when it connects, but made sure this does not undo FR-41 (decision 18).
- Changes to the 004 spec:
  - FR-56 now says what the feed never sends: undeliverable and suppressed events (never delivered), and failed deliveries (never recorded). A player who gets a token later receives nothing from before.
  - New FR-60: each item a feed sends is marked history or live. Only live items are new notifications. The page shows history without a new-notification highlight, so a reload or late connect raises no popups. This is the same concern as FR-41, applied to the feed.
  - AC-58 now checks the history and live marks. New AC-62: an undeliverable event for a player with no token never reaches a token issued later.
- Came from review: the first draft (FR-56) already excluded undeliverable events, but did not stop a late-connecting client from showing past notifications as new. That gap was found only because the owner raised the popup case.
- Q25 and Q27 to Q29 were still open at this point.

**23. 004 open questions Q27 to Q29 closed.**
- Prompt quoted in the Prompt log. All three recommendations accepted.
- Q27: the page's interaction is checked by an automated test of its content plus a manual browser check. No Playwright or Selenium: a new dependency to show a simple scenario is not justified, and the automated tests already prove the behavior behind the page (AC-60).
- Q28: feeds are addressed by delivery token, not player ID, in the way a Firebase push token addresses a device (FR-55).
- Q29: the page is self-contained. It fires events and changes preferences through the existing routes (FR-57).
- Q25 (producer method names) was still open at this point.

**24. Q25 closed, all 004 spec questions resolved.**
- Prompt quoted in the Prompt log. The owner accepted snake_case and added a detail: the brief's camelCase name is kept as a comment beside each producer method in the source, as well as in the README. This keeps the code PEP 8 while a reviewer can still match each call to the brief's example.
- Changed: FR-48 states the naming and the comment, and FR-59 requires the README to show the brief's four calls next to ours.
- The 004 spec has no open questions left.

**25. 004 spec approved, plan drafted.**
- Prompt: "yes draft it" (quoted in the Prompt log). The spec is marked reviewed by owner.
- Produced: draft `docs/features/004-demonstration/plan.md`. No new dependencies and no change to `core`. Seven decisions are pending for the owner (D1 to D7): live push as subscriptions inside `InAppChannel`; a bounded live queue per feed that closes a feed that stops reading; one shared wiring function for the app and the script; demo routes in their own router; a recording wrapper for the duplicate step instead of an `event_id` argument; `python -m notifications.demo` as the script command; the page as a static HTML file in the package.
- Design point found while planning: the history snapshot and the live hand-off must be taken under the same lock as the channel's append. Otherwise a notification delivered while a feed connects is either lost or shown twice, which would break FR-60 (history or live, never both). This is why D1 recommends putting subscriptions in the channel and not in a wrapper.
- Testing limit recorded as R10: `TestClient` cannot read an endless SSE response, so the stream generator is tested directly with `asyncio.run`, and the route is checked by hand. pytest-asyncio was not added.

**26. 004 plan approved, tasks drafted.**
- Prompt: "sounds good work on tasks" (quoted in the Prompt log), after the owner checked that a new feed receives what the token already holds marked as history. The agent confirmed it (FR-60, AC-58) and made the plan summary say so in plain words.
- Owner decisions: D1 to D7 accepted as recommended. Plan marked reviewed by owner.
- Produced: `docs/features/004-demonstration/tasks.md` with eight test-first tasks. T4 touches more than three files, so it is marked to run in plan mode first. T8 includes the manual browser run that completes AC-60, and the delivery checklist in the base `tasks.md`, which needs the owner's OK to edit.

**27. Feature 004 implemented, left uncommitted for owner review.**
- Prompt: "Implement and leave everything for review" (quoted in the Prompt log). As in 002 and 003, nothing was committed.
- Result: 443 passing tests (385 before 004). AC-52 to AC-62 are traced to tests in the spec. T1 to T7 are ticked. T8 stays open until the browser check of the page (AC-60, manual half) is done.
- Test-first record: every task started with tests that were run and seen to fail (collection errors for T1, T2, T4, T6; ten failures for T3; twelve for T5; eight for T7).
- Plan mode was used for T4 (more than three files), and the owner approved the short plan.
- Found by checking, not by the plan:
  - The first version of the concurrency test (a delivery while a feed subscribes) could not fail. A probe with a deliberately racy `subscribe` passed it 20 times out of 20, because under Python's GIL the producer thread finished every delivery before the subscribe ran. The test's producer now yields after each delivery, and the test asserts that the subscribe landed mid-stream. After that the racy version failed every trial, and the real channel passed 30 runs out of 30.
  - Live items are handed to the feed's event loop with `call_soon_threadsafe`. If that loop has already ended, the feed is closed and delivery still succeeds (FR-58). A test covers it.
  - On reconnect, the browser's `EventSource` gets the full history again, so the page clears a feed's list on each `open`. Without this, a reconnect would show every notification twice.
  - Browsers allow about six HTTP/1.1 connections per host, and the page holds five open feeds, so a second tab may stall. The preference checkboxes start as "on" because there is no read route for preferences. Both are listed in the README instead of adding routes.
  - The demo script first printed the brief's camelCase calls as if they were ours. It now prints our snake_case call with the brief's next to it (Q25).
- Hand checks: the demo script output was read in full. Under uvicorn, `curl` on `/feeds/token-1` received a posted Level Up as `live`, and on reconnect as `history`. An in-process server showed one open feed while a client was connected and none after it disconnected (R11). An HTTP walk-through of every action the page sends behaved as specified: six events delivered, suppressed and then delivered again for player 4 with no replay, `503` for player 6, `422` for a self-targeted request, three `live` items on player 4's feed and three `history` items on reconnect.
- Not done: the browser check of the page itself. The Claude in Chrome extension was not connected. It needs the owner, or a later session with the extension.
- Base files not edited at this point, waiting for the owner's OK: the feature log rows for 002 to 004, the delivery checklist, and Q2 and Q8 in the base spec's open-question table (done in decision 28).

**28. Project close-out pass.**
- Prompt quoted in the Prompt log. The owner approved editing the base files and asked for every open item to be closed.
- Each checklist item was checked before it was ticked: the GitHub repository answers without signing in (public); a clean copy of every tracked and new file installed with the README's commands, passed all 443 tests and ran the demo script; a wheel build includes the demo page, so a normal install serves `/demo`.
- Base files changed: the feature log (002 and 003 merged, 004 awaiting review), all five delivery checklist items, and base questions Q2 (fully decided), Q6 (closed, PvP not built, out of scope in the README) and Q8 (decided in 004).
- Statuses: the 002 and 003 specs and plans said "awaiting owner review before commit", but both were merged. They now say merged.
- The Tools used section was stale. It said plan mode was used once (it was used four times) and that no MCP integration was tried (Claude in Chrome was tried in 004). Both are corrected, and the "kept honest" list now covers 002 to 004.
- Sweep method: searched every Markdown file for "Status", "Open", "Pending", "awaiting", "TBD", "TODO" and unticked boxes, then fixed each hit or left it on purpose. Left on purpose: the history in earlier decisions (it describes what was pending at the time), the blueprint templates in `docs/spec/` (their placeholders and empty boxes are the template), and the owner's `docs/functional-spec.md`, which keeps its own "Draft for discussion" status because it is the owner's source document.
- Not closed, and why: the browser check of the demo page (AC-60 manual half). The Claude in Chrome extension was still not connected, and ticking it without a run would be false. 004-T8 was split, so everything else is ticked and the browser check is its own task, 004-T9. 004 itself is implemented and waiting for the owner's review and commit.

**29. Browser check of the demo page (AC-60 manual half, 004-T9).**
- Prompt quoted in the Prompt log. The owner ran the check themselves and asked the agent to do one pass too, with the browser extension now connected.
- Port 8000 was held by another process that did not answer, so the agent left it alone and ran the app on port 8010.
- What the agent did in the page, and what it saw:
  - On load: six player columns. Eve is labelled "no in-app channel" with no feed, and Frank is labelled unreachable.
  - Level up for Alice: `processed`, and the message appeared in Alice's feed highlighted as new.
  - The other five event types: each `processed` and shown in the right player's feed (the brief's friend request from 3 to 1 in Alice's feed, the accept in Carol's).
  - A friend request from Bob to Bob: `422 SELF_TARGETED`, with the message shown on the page.
  - Dave's Game checkbox off (a real click): `updated`, then a level up for Dave was `suppressed`. Checkbox on again: the next level up was `processed`, and the suppressed one never appeared.
  - Eve: `undeliverable`. Frank: `503 DELIVERY_FAILED`. Resending Frank's event gave `503` again rather than duplicate, which is correct: a failed delivery releases its ID (FR-39).
  - A processed event for Bob, then "Resend last event" (a real click): `duplicate`.
  - Reload: all 8 delivered notifications came back as history, none highlighted, in the same feeds. Dave's suppressed level 20 was absent. No console errors.
- Result: AC-60 is passing, 004-T9 is ticked, and the 004 spec has no open items. 004 waits only for the owner's review and commit.

## Additional AI assistance: requirements brainstorming and independent review

Recorded retrospectively. This assistance happened in a separate Codex chat alongside the implementation work in Claude Code.

**30. Challenge review and initial functional specification.**
- Prompt (summary): review the coding challenge for common mistakes and easily missed requirements, then help clarify the functional scope.
- Tool used: Codex, with the challenge PDF, recruitment email and job description supplied as context.
- Findings: the six required events must all be covered, even though the example calls show only four. Friend Accepted was interpreted as notifying the original requester. The referenced `Notification` class was absent from the PDF.
- Scope clarified: the challenge permits simulated event producers and delivery. A broker, WebSocket server and game-client display are not required.
- Produced: an initial functional specification covering event triggers, recipients, content, category preferences, delivery assumptions and acceptance scenarios. The owner subsequently supplied this specification to Claude Code for the repository's feature-by-feature workflow.
- Proposed defaults, interpretations and extensions were identified separately from explicit challenge requirements.

**31. Owner-led technical brainstorming and system boundaries.**
- Prompt (summary): discuss a Python backend with replaceable intake, processing and delivery components.
- Owner direction: use Python because of recent backend experience and confidence explaining the implementation.
- Approach discussed: transport adapters submit events to a common processing entry point; notification rules remain independent of the incoming transport and outgoing delivery mechanism.
- Clarification from checking the PDF: receiving events into the module remains required, but upstream transport infrastructure can be simulated. The demonstration must show an event entering the module and producing a notification decision.
- Demonstration options considered: direct simulated producer calls, an HTTP-backed UI, RabbitMQ and WebSocket integration. These were options discussed, not implementation decisions made by Codex. Final choices were recorded through the Claude Code feature workflow.

**32. Independent read-only reviews and regression verification.**
- Prompt (summary): review the implementation against the challenge, identify concrete issues, and make no changes.
- Tools used: repository inspection, the existing Python environment and pytest, temporary in-memory probes, local HTTP/SSE requests, and a separate fresh clone and environment.
- Verification: the completed public submission installed successfully from a fresh clone, passed 443 tests and ran the scripted demonstration. Live HTTP/SSE checks covered delivery, preference suppression, duplicates, failure responses and history on reconnect.
- Issues identified: list/object preference categories caused a server error; demo checkboxes did not reflect saved preferences after reload; the README misstated event-ID retention; the AI log omitted this separate assistance.
- Follow-up verification after changes: 449 tests passed, malformed categories returned validation errors, the demo loaded current preferences, and the README described the 10,000-ID retention limit.
- Limitation: no browser was connected for the Codex review, so browser interaction was not independently rerun. Claude Code's browser verification remains recorded separately.
- Repository work by Codex was read-only. No application code, feature specs or tests were edited during these reviews.

**33. Fixes for the Codex review findings (Claude Code).**
- Prompt quoted in the Prompt log. The owner first asked Claude Code to check the four findings from decision 32 without changing anything. All four were confirmed: `PUT /preferences` with `"category": []` or `{}` returned `500`, while `POST /events` handled the same values with `422`. The owner then asked for fixes on `main`, uncommitted, for findings 1 to 3, and kept finding 4 (this log) for Codex.
- Finding 1: `PreferenceService.change` now checks that the category is a string before the set lookup, so a list or object gets `422 UNSUPPORTED_CATEGORY`, the same as `1` or `"pvp"`. Four failing tests were written first (core and HTTP).
- Finding 2: `GET /demo/players` now returns each player's current Game and Social settings, read on every request with the core's default-on rule (`is_enabled`), and the page starts each checkbox from them. The wiring exposes the preference store for this. Three failing tests were written first. The README limitation about the checkboxes was removed, since it no longer applies.
- Finding 3: the README now says the event-ID store keeps the most recent 10,000 IDs, so an event resent after that many newer ones is processed again. The limit was recorded in decision 11, but was left out when the README was written.
- Also: the 004 spec, plan and feature log now say merged to `main`, and the plan describes the new player-list field.
- Result: 449 passing tests. A run under uvicorn confirmed `422` for both malformed categories, and Dave's `game: false` in the player list after turning it off. The page was not rechecked in a browser after this change.

**34. Hardening after an external review of `e316a6c` (Claude Code).**
- Prompt quoted in the Prompt log. The owner pasted a second Codex review of the submitted commit `e316a6c` and asked Claude Code to analyse and validate it before changing anything.
- Validation: the agent reproduced every concrete finding with a throwaway probe script, without editing the repository. A: `async def` routes ran the synchronous core on the event loop; with a 150 ms delivery, three posts and a 10 ms timer all took 0.455 s. B1: a copy sent while the original was still delivering got `200 duplicate`, then the original failed and nothing was delivered. B2: with a store of capacity 1, an ID still in flight was evicted and the event was delivered twice. C: a delivery that took effect and then raised was retried and delivered twice, and `Notification` had no event ID. D: with a feed bound of 1, 5,000 deliveries left 5,001 callbacks queued on the loop. Also confirmed: no request body in the OpenAPI schema, the `uvicorn.error` logger, no CI or lockfile. One review claim was weaker than stated: the "stale" plan line checked was already marked as replaced.
- The agent also admitted that its own interview-preparation notes had overstated the design: "add a definition and nothing else changes" holds only for events shaped like the six, and `duplicate` and "effectively once" were wrong for in-flight copies and lost acknowledgements.
- Owner decisions (structured question tool, all recommendations taken): an in-flight copy gets `409 EVENT_IN_PROGRESS`, a retryable error rather than a success; the sync routes read the body with FastAPI `Body` plus one exception handler that keeps the existing `422 MALFORMED_FIELD` format; the work goes on `main`, uncommitted. The owner chose the scope: A, B with minimum change and a proper lifecycle, C, D and a one-page architecture document. E (producers make a new ID on each call), the logger, CI and a lockfile were kept as talking points.
- Decision from reviewing the plan, not the first draft: the owner rejected the plan's "at-least-once delivery" wording. Adding an event ID and allowing retries does not guarantee at-least-once delivery, because state is in memory, undeliverable events are dropped, there is no durable pending work and producer retries are not enforced. The guarantee is now stated as: one delivery attempt per processing attempt; failed attempts can be retried with the same event ID; an uncertain outcome can produce duplicates, and receivers can use the event ID to deduplicate. "Receivers dedupe" became "receivers can", since no receiver does.
- Spec first: an "Amendment (decision 34)" section in the 001, 003 and 004 specs, with FR-61 to FR-67 and AC-63 to AC-70, each traced to tests.
- Changes, each test first:
  - B: `ProcessedEvents.claim` returns `Claim.NEW`, `IN_PROGRESS` or `COMPLETED`, with a new `complete`. The in-memory store keeps IDs in progress in a set that is never evicted, and only completed IDs in the bounded record. `EventInProgressError` maps to `409`. A control run with the old two-state store made both lifecycle tests fail.
  - C: `Notification.event_id`, set by the service, and included in each feed item.
  - A: the two routes are plain `def`, so FastAPI runs the core in its thread pool. The new timing test failed at 0.455 s first, then passed 15 runs out of 15. The OpenAPI schema now shows a request body for both routes.
  - D: each feed counts its outstanding items and refuses before scheduling anything, so a stalled reader costs at most two callbacks before it is closed.
- Changed expectations in earlier tests: the store tests use `Claim` values; the AC-25 concurrency test now allows "in progress" as well as `duplicate` for the losing copies; the AC-21 test compares notification content apart from the event ID, since two events now have two identities.
- Docs: new `docs/architecture.md` with a component diagram and an event-ID lifecycle diagram in Mermaid, the processing order, the exact guarantees, the producer answers table, the concurrency model, and what extends cheaply versus what changes the model. The README links to it and its guarantee wording is corrected. A sweep for "at-least-once", "effectively once", "exactly once" and "dedupe" found the overstatements only in the agent's chat notes, not in the repository.
- Result: 461 passing tests (449 before). Re-running the review's probes: A 0.169 s with the timer on time (0.018 s); B1 `EVENT_IN_PROGRESS`; B2 delivered once; C two deliveries carrying the same `event_id` (the documented uncertain case); D three callbacks. A run under uvicorn confirmed processed, duplicate, `422` for invalid, `null` and missing bodies, and `event_id` in the feed.
- Not done: a browser pass of the page and a render check of the two Mermaid diagrams. The Claude in Chrome extension was not connected.
- This amends work already graded at `e316a6c`. The changes are on `main`, uncommitted, for the owner's review.
