# Feature 001: Event intake and dispatch
Status: Reviewed by owner
Builds on: baseline

Source: Initial Functional Specification: Gaming Notifications (sections 2, 3, 4, 6 and scenarios 1 to 4).

## Purpose
This is the core of the notification module. It receives an event from a simulated game or social component, works out who is notified, in which category and with what message, creates the notification and hands it to in-app delivery. It is also the first feature, so it establishes the baseline structure of the project (decided in the plan, not here).

## User stories
- As a player, I get a notification when I level up, acquire a notable item or complete a challenge, so that I know my progress was recognised.
- As a player, I get a notification when someone sends me a friend request, accepts mine, or follows me, so that I can respond to social activity.
- As a game or social backend developer, I submit an event to one entry point and do not need to know how the notification is built or delivered.

## Requirements
Numbering continues across features and is never reused. Feature 001 uses FR-1 to FR-18 (FR-12 to FR-18 were added after owner review, so they sit below FR-11 in the text).

**Intake**
- FR-1: The module exposes an event-handling entry point that simulated game and social components submit events to. The module's responsibility starts when an event is submitted there.
- FR-2: Processing of an event starts when it is submitted, with no intentional batching or scheduled delay.
- FR-3: The module trusts the producer. It does not verify that the action happened, and it does not decide which items or challenges qualify. Every submitted event of a supported type is processed.

**Event types, categories and recipients**
- FR-4: The module supports these six event types: Level Up, Item Acquired, Challenge Completed, Friend Request, Friend Accepted, New Follower.
- FR-5: Each event type belongs to exactly one category. Level Up, Item Acquired and Challenge Completed belong to Game Events. Friend Request, Friend Accepted and New Follower belong to Social Events.
- FR-6: The recipient is determined from the event type:

| Event | Recipient |
|---|---|
| Level Up | the player who levelled up |
| Item Acquired | the player who obtained the item |
| Challenge Completed | the player who completed it |
| Friend Request | the player the request was sent to |
| Friend Accepted | the player who originally sent the request |
| New Follower | the player who was followed |

**Content**
- FR-7: Each notification carries a message that clearly describes the event in plain language. Exact wording is flexible.
- FR-8: The message includes the detail for its event type:

| Event | Message must include |
|---|---|
| Level Up | the new level |
| Item Acquired | the item name |
| Challenge Completed | the quest or achievement name |
| Friend Request | the requester's display name |
| Friend Accepted | the accepting player's display name |
| New Follower | the follower's display name |

**Notification and hand-off**
- FR-9: For each processed event the module creates one notification that identifies the recipient, the category, the event type and the message.
- FR-10: The module then invokes the in-app delivery dependency once with that notification and its recipient. What delivery does with it is specified in feature 003.
- FR-11: Events are processed independently. One event never changes the recipient, category or message of another.

**User lookup** (added after owner review, Q9)
- FR-12: Events identify players by ID only. They carry no display names.
- FR-13: The module resolves players by looking them up by ID in a user directory, a dependency simulated in this exercise. The recipient is looked up for every event, because the directory holds the recipient's delivery token (FR-18). The acting player's display name is looked up only for Friend Request, Friend Accepted and New Follower. Game events need no second lookup.
- FR-14: If any player ID in an event is not found in the user directory, the event is invalid and handled under FR-15. The module never processes an event for a player that does not exist. In normal operation producers do not send such events, so this also guards against forged or malicious submissions.
- FR-18: The user directory entry for a player holds the player's display name and the delivery token for the player's in-app notification channel, because the platform is assumed to deliver in-app notifications to a connected client. The module passes the recipient's token to the delivery dependency together with the notification (the delivery contract itself is specified in feature 003).

**Invalid events** (added after owner review, Q10 and Q11)
- FR-15: An invalid event is rejected with an error returned to the submitting component, and no notification is created and delivery is not invoked. The error says why the event was rejected (for example unsupported event type, or which required field is missing). An event is invalid when its type is unsupported, a required field is missing or malformed, a field that the event type does not define is present, or a player ID is unknown (FR-14).
- FR-16: A social event whose actor and target are the same player (for example a player following or sending a friend request to themselves) is invalid under FR-15.

**Name formatting** (added after owner review, Q12)
- FR-17: Item and quest or achievement names may arrive in compact form (for example `SwordOfAzeroth`). The message shows them as readable words separated by spaces. A name that already contains spaces is shown unchanged.

## Acceptance criteria
| ID | Given / When / Then | Covers |
|---|---|---|
| AC-1 | Given a Level Up event for player 1 with new level 15, when it is submitted, then delivery is invoked once for player 1 with a Game Events notification whose message contains "15". | FR-1, FR-4, FR-5, FR-6, FR-8, FR-9, FR-10 |
| AC-2 | Given an Item Acquired event for player 2 with item "SwordOfAzeroth", when it is submitted, then delivery is invoked once for player 2 with a Game Events notification whose message contains the item name. | FR-4, FR-5, FR-6, FR-8, FR-9, FR-10 |
| AC-3 | Given a Challenge Completed event for a player with a quest name, when it is submitted, then delivery is invoked once for that player with a Game Events notification whose message contains the quest name. | FR-4, FR-5, FR-6, FR-8, FR-9, FR-10 |
| AC-4 | Given user 3 sends a friend request to user 1, when the event is submitted, then delivery is invoked once for user 1 (not user 3) with a Social Events notification whose message contains user 3's display name. | FR-4, FR-5, FR-6, FR-8, FR-9, FR-10 |
| AC-5 | Given user 1 accepts the friend request from user 3, when the event is submitted, then delivery is invoked once for user 3 (not user 1) with a Social Events notification whose message contains user 1's display name. | FR-4, FR-5, FR-6, FR-8, FR-9, FR-10 |
| AC-6 | Given player A follows player B, when the event is submitted, then delivery is invoked once for B (not A) with a Social Events notification whose message contains A's display name. | FR-4, FR-5, FR-6, FR-8, FR-9, FR-10 |
| AC-7 | Given any of the six event types, when it is submitted, then the notification message is non-empty and describes the event in readable text. | FR-7 |
| AC-8 | Given an event is submitted, when the entry point returns, then delivery has already been invoked for it, with no timer, batch or second trigger needed. | FR-2, FR-10 |
| AC-9 | Given an Item Acquired event for any item name, when it is submitted, then it is notified; the module applies no rarity or value filter. Same for any Challenge Completed event. | FR-3 |
| AC-10 | Given two events for different recipients submitted one after the other, when both are processed, then each delivery call carries only its own recipient and message. | FR-11 |
| AC-11 | Given a Friend Request event carrying only player IDs, when it is submitted, then the message contains the requester's display name as held in the user directory. | FR-12, FR-13 |
| AC-12 | Given a game event (for example Level Up), when it is submitted, then only the recipient is looked up; no other player's display name is requested. | FR-13 |
| AC-13 | Given an event with an unsupported type, a missing required field, a field of the wrong type, or an unknown extra field, when it is submitted, then the submitter receives an error that names the reason, no notification is created and delivery is not invoked. | FR-15 |
| AC-14 | Given a Friend Request, Friend Accepted or New Follower event where actor and target are the same player, when it is submitted, then it is rejected as invalid and delivery is not invoked. | FR-16, FR-15 |
| AC-15 | Given an event whose recipient ID, or whose acting player ID, is not in the user directory, when it is submitted, then it is rejected as invalid with an error naming the unknown player, and delivery is not invoked. This holds for game events too. | FR-14, FR-15 |
| AC-16 | Given an Item Acquired event with item `SwordOfAzeroth`, when it is submitted, then the message shows the name as separate words ("Sword Of Azeroth" or equivalent). A name already containing spaces appears unchanged. | FR-17 |
| AC-17 | Given a valid event whose recipient has a delivery token in the user directory, when it is submitted, then delivery is invoked with that recipient's token along with the notification. | FR-13, FR-18 |

Preference behavior is out of scope here, so in this feature every processed event reaches delivery. Feature 002 adds the check (AC-5 to AC-8 of the functional spec).

## Edge cases
- An event for a recipient with no recorded preferences is processed like any other (no preference check exists in this feature).
- The same event submitted twice produces two notifications. Duplicate handling is deferred (functional spec section 6).
- An event with a missing recipient or missing content detail, or of an unsupported type: rejected with an error (FR-15).
- Self-targeted social events: rejected (FR-16). Upstream normally prevents them, so this is a defensive check.
- Unknown player ID: rejected (FR-14, proposed).
- Empty or whitespace-only item or quest name: rejected as malformed (FR-15).
- Unknown extra field in the payload: rejected as malformed (FR-15). Assumption from the owner's "malicious sender" reasoning, to be confirmed.
- A payload that is not an object: rejected (FR-15).
- The module is independent of how the event arrived. The same payload gives the same outcome over HTTP, a WebSocket, a broker or a direct call (FR-1).

## Not in this feature
- Preference storage and checking (feature 002).
- The delivery dependency's contract and its no-guarantee semantics (feature 003).
- The runnable demonstration and its interface (feature 004).
- PvP events (optional in the brief, excluded from initial scope).
- How the user directory is implemented or populated (a simulated dependency here, shape decided in the plan).
- Upstream transport, message brokers, WebSocket handling, client rendering.
- Offline delivery, retries, ordering, duplicate-event handling, latency targets.
- Non-functional requirements (specified later, component by component).

## Open questions
| # | Question | Notes |
|---|---|---|
None open for this feature.

Resolved by the owner (moved to the decision log):
- Q15: a player with a directory entry but no delivery token is a valid event. The module passes what the directory holds, and the outcome is decided in feature 003 (delivery failure behavior).
- Q13: an unknown player ID is rejected for every event type, including game events (FR-14). Reason: such an event should never be sent, and processing it could serve a malicious sender.
- Q14: names are shown with spaces only, "Sword Of Azeroth" (FR-17).
- The user directory also holds each player's delivery token (FR-18).
- Q1: the `Notification` class was not provided, we define our own.
- Q9: events carry IDs only, names come from a user directory lookup (FR-12, FR-13).
- Q10: invalid events are rejected with an error to the sender (FR-15).
- Q11: self-targeted social events are invalid (FR-16).
- Q12: item names are shown as readable words (FR-17).
- Q3 and Q4 from `docs/spec/spec.md` are answered by the functional spec (Friend Accepted notifies the original requester; upstream decides which items qualify), reflected in FR-6 and FR-3.

## Traceability
| ID | Test | Status |
|---|---|---|
| AC-1 | TBD | Not started |
| AC-2 | TBD | Not started |
| AC-3 | TBD | Not started |
| AC-4 | TBD | Not started |
| AC-5 | TBD | Not started |
| AC-6 | TBD | Not started |
| AC-7 | TBD | Not started |
| AC-8 | TBD | Not started |
| AC-9 | TBD | Not started |
| AC-10 | TBD | Not started |
| AC-11 | TBD | Not started |
| AC-12 | TBD | Not started |
| AC-13 | TBD | Not started |
| AC-14 | TBD | Not started |
| AC-15 | TBD | Not started |
| AC-16 | TBD | Not started |
| AC-17 | TBD | Not started |
