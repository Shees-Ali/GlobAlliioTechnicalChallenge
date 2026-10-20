# Base Spec Blueprint

This file holds two things: the facts that come from the brief, and the template every feature spec copies. It contains no design decisions. Anything not stated in the brief is an open question, settled with the project owner and recorded in `docs/ai-process/README.md` (decision log).

## 1. What the brief says (source: `Coding_Challenge.pdf`)

**Scenario.** A real-time notification system for an online multiplayer gaming platform.

**Events to notify about**
- In-game: level up, item acquired (rare or valuable), challenge completed. PvP (attacked or defeated) is optional, "good to consider".
- Social: friend request, friend accepted, new follower.

**Other requirements**
- Channel: in-app only. The game client is assumed to have a way to receive notifications in real time; display is out of scope and may be mocked.
- Content: clear, concise, informative (the brief gives example messages for level up, item acquired and friend request).
- Preferences: simplified, enable or disable per category (for example "Game Events", "Social Events"), representable by a simple map.
- A `Notification` class is said to be provided (it was not attached, see open question Q1).
- Design the components for notification handling: interfaces, services, classes for sending, checking preferences, and talking to the game and social systems, with flexibility and maintainability in mind.
- Event handling: a way to receive events from different parts of the platform and pass them to the notification system. Dispatch: determine the notification type, create the `Notification`, check preferences, send.
- Example usage that shows events triggering notifications, using the brief's four example triggers:
  - `gameEngine.playerLeveledUp(1, 15)`
  - `gameEngine.itemAcquired(2, "SwordOfAzeroth")`
  - `socialSystem.friendRequestSent(3, 1)`
  - `socialSystem.friendRequestAccepted(1, 3)`

**Delivery and interview**
- The product must compile and run from a public GitHub repo, with build scripts. A README is recommended.
- Focus on the required features first. Polish and extras only after.
- AI use is encouraged. The prompts and the process are part of the deliverable.
- Follow-up interview: (1) the AI process, (2) defending the architecture, tradeoffs, hypothetical extensions, and how the system works.

## 2. Open questions and their status
Each is answered with the owner during the feature where it matters, then moved to the decision log.

| # | Question | Raised by | Settle in | Status |
|---|---|---|---|---|
| Q1 | The brief says a `Notification` class is provided but none was attached. Wait for the recruiter's reply, or define our own? | brief gap, email sent to the recruiter | first feature | Decided in 001: define our own. |
| Q2 | Language and shape: Python, Node, or both; one app or API plus separate frontend? | owner | first feature | Decided. Language in 001: Python with FastAPI, one app. Demo in 004: a script plus a page served by the same app, no separate frontend. |
| Q3 | Who is notified for `friendRequestAccepted(1, 3)`? | ambiguity in the brief | social events feature | Decided: the original requester (functional spec, FR-6 in 001). |
| Q4 | What counts as a "rare or valuable" item? | ambiguity in the brief | game events feature | Decided: the producer decides, the module notifies every item it receives (FR-3 in 001). |
| Q5 | Preference granularity beyond category? | brief says simplified | preferences feature | Decided in 002: per category only, Game and Social, on unless turned off (FR-26 to FR-28). |
| Q6 | Include PvP events? | brief says optional | after required scope | Closed: not built. The functional spec excludes PvP from the initial scope, and no feature was picked for it. Adding it is one event definition per PvP event (P4). Listed as out of scope in the README. |
| Q7 | Real-time mechanism and delivery guarantee | brief says assume a mechanism exists | delivery feature | Decided in 003: a simulated in-app channel records per token, live push is left to 004; one delivery attempt, the producer retries, and a failure is `503 DELIVERY_FAILED` (FR-37 to FR-47). Intake is transport neutral (001). |
| Q8 | Persistence and scale limits to state in the README | not covered by brief | packaging | Decided in 004: everything stays in memory in one process, and the limits are listed under Known limitations in `README.md` (FR-59). |

Questions raised inside a feature (numbered Q9 onward) live in that feature's `spec.md`. All of them, Q9 to Q29, are resolved.

## 3. Feature spec blueprint
Copy to `docs/features/NNN-name/spec.md` when the owner picks a feature.

```
# Feature NNN: <name>
Status: Draft | Reviewed by owner | Implemented
Builds on: <earlier features, or "baseline">

## Purpose
Why this feature exists and what the player or developer gets.

## User stories
- As a <who>, I <do what> so that <why>.

## Requirements
Numbered, testable statements of WHAT, not how. Use the next free FR number.
Continue the numbering from the last feature; never reuse a number.

## Acceptance criteria
| ID | Given / When / Then | Covers |
Use the next free AC number.

## Edge cases
Behaviors at the boundaries.

## Not in this feature
What is deliberately left for other features.

## Open questions
Questions for the owner. Resolved ones move to the decision log.

## Traceability
| ID | Test | Status |
```
