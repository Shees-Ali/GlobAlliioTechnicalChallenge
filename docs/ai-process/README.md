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
