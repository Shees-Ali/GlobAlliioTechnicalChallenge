# Feature 001: Event intake and dispatch
Status: Implemented, amended with FR-19 to FR-25 (idempotency, decision 11 in the log)
Builds on: baseline

Source: Initial Functional Specification: Gaming Notifications (sections 2, 3, 4, 6 and scenarios 1 to 4).

## Purpose
This is the core of the notification module. It receives an event from a simulated game or social component, works out who is notified, in which category and with what message, creates the notification and hands it to in-app delivery. It is also the first feature, so it establishes the baseline structure of the project (decided in the plan, not here).

## User stories
- As a player, I get a notification when I level up, acquire a notable item or complete a challenge, so that I know my progress was recognised.
- As a player, I get a notification when someone sends me a friend request, accepts mine, or follows me, so that I can respond to social activity.
- As a game or social backend developer, I submit an event to one entry point and do not need to know how the notification is built or delivered.
- As a producer that retries after a timeout or a broker redelivery, I resend an event with the same event ID so that the player is never notified twice.

## Requirements
Numbering continues across features and is never reused. Feature 001 uses FR-1 to FR-25 (FR-12 to FR-25 were added after owner review, so they sit below FR-11 in the text).

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

**Idempotency** (amendment, decision 11)
- FR-19: Every event carries an `event_id`, an opaque non-blank string of at most 128 characters chosen by the producer. It is the idempotency key. A missing or malformed `event_id` makes the event invalid under FR-15.
- FR-20: The first valid event with a given `event_id` is processed normally. A later event with the same `event_id` is not processed again: no notification is created and delivery is not invoked. The submitter is told the event was a duplicate, as a success and not as an error.
- FR-21: An `event_id` is used up only when the event has passed validation and the player lookups, immediately before delivery. A rejected event does not use up its ID, so a corrected resend with the same ID is accepted.
- FR-22: If delivery fails, the `event_id` is released, so resubmitting the event with the same ID is processed.
- FR-23: The `event_id` alone identifies an event. The rest of the payload is not compared, so the same ID with different content is a duplicate.
- FR-24: Using up an `event_id` is atomic. Concurrent submissions of the same ID cause exactly one delivery.
- FR-25: Duplicate detection holds for as long as the ID is retained. Retention is bounded, the oldest IDs are dropped past a capacity, and a dropped ID would be processed again.

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
| AC-18 | Given an event with no `event_id`, or one that is blank, not a string or longer than 128 characters, when it is submitted, then it is rejected with an error naming `event_id` and delivery is not invoked. | FR-19, FR-15 |
| AC-19 | Given the same event is submitted twice, when both are processed, then delivery is invoked exactly once. | FR-20 |
| AC-20 | Given a duplicate is submitted, when it is processed, then the submitter gets a duplicate outcome and not an error. Over HTTP this is `200` with `{"status": "duplicate"}`. | FR-20 |
| AC-21 | Given two events with identical content but different `event_id` values (two real level-ups to the same level), when both are submitted, then both are delivered. | FR-20 |
| AC-22 | Given an event rejected for an unknown player, when the corrected event is resent with the same `event_id`, then it is delivered. | FR-21 |
| AC-23 | Given delivery fails for an event, when the same `event_id` is resent, then the first call's error reached the submitter and the resend is delivered. | FR-22 |
| AC-24 | Given an event was processed, when a different payload arrives with the same `event_id`, then it is treated as a duplicate and not delivered. | FR-23 |
| AC-25 | Given many threads submit the same event at once, when all finish, then delivery was invoked exactly once. | FR-24 |
| AC-26 | Given the ID store is at capacity, when a new ID is claimed, then the oldest ID is dropped and a resend of that dropped ID is processed again. | FR-25 |

Preference behavior is out of scope here, so in this feature every processed event reaches delivery. Feature 002 adds the check (AC-5 to AC-8 of the functional spec).

## Edge cases
- An event for a recipient with no recorded preferences is processed like any other (no preference check exists in this feature).
- The same event submitted twice produces one notification. The second call returns a duplicate outcome (FR-20). The functional spec deferred duplicate handling to the technical decisions, and this is that decision.
- A producer that reuses an `event_id` for a different event has that event silently treated as a duplicate (FR-23). Known limitation.
- The ID store is in memory, bounded, and lost on restart, so after a restart or past its capacity a resent ID is processed again (FR-25). Known limitation, listed in the README at packaging.
- An event with a missing recipient or missing content detail, or of an unsupported type: rejected with an error (FR-15).
- Self-targeted social events: rejected (FR-16). Upstream normally prevents them, so this is a defensive check.
- Unknown player ID, as recipient or as acting player, for any event type: rejected (FR-14).
- Empty or whitespace-only item or quest name: rejected as malformed (FR-15).
- Unknown extra field in the payload: rejected as malformed (FR-15). Approved by the owner with the tasks, in line with the "malicious sender" reasoning behind FR-14.
- A payload that is not an object: rejected (FR-15).
- The module is independent of how the event arrived. The same payload gives the same outcome over HTTP, a WebSocket, a broker or a direct call (FR-1).

## Not in this feature
- Preference storage and checking (feature 002).
- The delivery dependency's contract and its no-guarantee semantics (feature 003).
- The runnable demonstration and its interface (feature 004).
- PvP events (optional in the brief, excluded from initial scope).
- How the user directory is implemented or populated (a simulated dependency here, shape decided in the plan).
- Upstream transport, message brokers, WebSocket handling, client rendering.
- Offline delivery, delivery retries, ordering, latency targets. (Duplicate-event handling is in scope, FR-19 to FR-25.)
- A shared or persistent ID store (the in-memory store sits behind an interface so one can replace it).
- Non-functional requirements (specified later, component by component).

## Open questions
None. All questions raised for this feature are resolved. The reasoning is in `docs/ai-process/README.md` (decisions 4 and 5).

| # | Question | Resolution | Where it landed |
|---|---|---|---|
| Q1 | A `Notification` class was said to be provided but was not attached. | We define our own. | FR-9 |
| Q3 | Who is notified when a friend request is accepted? | The original requester. Answered by the functional spec. | FR-6 |
| Q4 | What counts as a rare or valuable item? | The producer decides. The module notifies every item and challenge it receives. | FR-3 |
| Q9 | How does the module get display names? | Events carry IDs only. Names come from a user directory lookup. | FR-12, FR-13 |
| Q10 | What happens to an invalid event? | Rejected with an error returned to the sender. | FR-15 |
| Q11 | Are self-targeted social events notified? | No, they are invalid. | FR-16 |
| Q12 | How are item names shown? | As separate words. | FR-17 |
| Q13 | Is an event for an unknown player ID processed? | No, it is rejected for every event type. | FR-14 |
| Q14 | Spaces only, or also lowercase small words? | Spaces only ("Sword Of Azeroth"). | FR-17 |
| Q15 | Is a player with no delivery token valid? | Yes. What delivery does about it is decided in feature 003. | FR-18, feature 003 |
| Q16 | Should duplicate events be suppressed, and how does the module recognise one? | Yes. Producers send an `event_id`, which is the idempotency key. The owner called it a critical requirement. | FR-19, FR-20 |
| Q17 | When is an `event_id` recorded relative to delivery? | Claimed just before delivery, released if delivery fails. Rejected events never claim it. | FR-21, FR-22, FR-24 |
| Q18 | What if an `event_id` is reused with different content? | Treated as a duplicate. The ID alone is the key. | FR-23 |

## Traceability
| ID | Test | Status |
|---|---|---|
| AC-1 | `tests/core/test_service_level_up.py::test_level_up_delivers_one_game_notification_to_the_player` | Passing |
| AC-2 | `tests/core/test_service_game_events.py::test_item_acquired_notifies_the_player_with_a_readable_item_name` | Passing |
| AC-3 | `tests/core/test_service_game_events.py::test_challenge_completed_notifies_the_player_with_the_quest_name` | Passing |
| AC-4 | `tests/core/test_service_social_events.py::test_friend_request_from_3_to_1_notifies_user_1_about_user_3` | Passing |
| AC-5 | `tests/core/test_service_social_events.py::test_friend_accepted_by_1_notifies_user_3_about_user_1` | Passing |
| AC-6 | `tests/core/test_service_social_events.py::test_new_follower_notifies_the_followed_player_about_the_follower` | Passing |
| AC-7 | `tests/core/test_all_events.py::test_every_message_is_non_empty_readable_text` | Passing |
| AC-8 | `tests/core/test_service_level_up.py::test_delivery_has_been_invoked_by_the_time_handle_event_returns`, `tests/api/test_events_route.py::test_a_valid_event_returns_200_and_delivery_has_already_been_invoked` | Passing |
| AC-9 | `tests/core/test_service_game_events.py::test_every_submitted_item_is_notified_with_no_rarity_filter`, `tests/core/test_service_game_events.py::test_every_submitted_challenge_is_notified` | Passing |
| AC-10 | `tests/core/test_all_events.py::test_events_are_independent_of_each_other` | Passing |
| AC-11 | `tests/core/test_service_social_events.py::test_payloads_carry_ids_and_the_display_name_comes_from_the_directory` | Passing |
| AC-12 | `tests/core/test_service_level_up.py::test_a_game_event_looks_up_only_the_recipient`, `tests/core/test_service_game_events.py::test_game_events_look_up_only_the_recipient` | Passing |
| AC-13 | `tests/core/test_validation.py`, `tests/core/test_all_events.py` (missing, wrong type, blank, extra field, unsupported type), `tests/api/test_events_route.py::test_an_invalid_event_returns_422_with_the_reason_and_no_delivery` | Passing |
| AC-14 | `tests/core/test_service_rejections.py::test_a_self_targeted_social_event_is_rejected`, `tests/core/test_service_rejections.py::test_a_self_targeted_event_is_rejected_before_any_lookup` | Passing |
| AC-15 | `tests/core/test_service_rejections.py::test_an_unknown_recipient_is_rejected_for_game_events`, `..._for_social_events`, `tests/core/test_service_rejections.py::test_an_unknown_acting_player_is_rejected` | Passing |
| AC-16 | `tests/core/test_formatting.py::test_readable_name`, `tests/core/test_service_game_events.py::test_item_acquired_notifies_the_player_with_a_readable_item_name` | Passing |
| AC-17 | `tests/core/test_service_level_up.py::test_delivery_receives_the_recipients_token` | Passing |
| AC-18 | `tests/core/test_validation.py` (`event_id` cases), `tests/core/test_all_events.py::test_a_missing_event_id_is_rejected`, `tests/core/test_all_events.py::test_a_malformed_event_id_is_rejected`, `tests/api/test_events_route.py::test_an_event_without_an_event_id_returns_422` | Passing |
| AC-19 | `tests/core/test_idempotency.py::test_the_same_event_submitted_twice_is_delivered_once`, `tests/core/test_idempotency.py::test_a_duplicate_is_ignored_however_often_it_is_resent` | Passing |
| AC-20 | `tests/core/test_idempotency.py::test_a_duplicate_returns_a_duplicate_outcome_and_not_an_error`, `tests/api/test_events_route.py::test_a_duplicate_event_returns_200_with_a_duplicate_status` | Passing |
| AC-21 | `tests/core/test_idempotency.py::test_identical_content_with_different_ids_is_delivered_twice`, `tests/api/test_events_route.py::test_the_same_content_with_a_new_event_id_is_delivered_again` | Passing |
| AC-22 | `tests/core/test_idempotency.py::test_a_rejected_event_does_not_use_up_its_id`, `tests/api/test_events_route.py::test_a_rejected_event_can_be_resent_corrected_with_the_same_id` | Passing |
| AC-23 | `tests/core/test_idempotency.py::test_a_failed_delivery_releases_the_id_so_the_resend_is_delivered`, `tests/core/test_idempotency.py::test_once_delivered_after_a_failure_the_id_stays_used` | Passing |
| AC-24 | `tests/core/test_idempotency.py::test_the_same_id_with_different_content_is_a_duplicate` | Passing |
| AC-25 | `tests/core/test_idempotency.py::test_many_threads_submitting_one_event_cause_exactly_one_delivery` (with a racy-store control), `tests/core/test_in_memory_processed_events.py::test_concurrent_claims_of_one_id_yield_exactly_one_winner` | Passing |
| AC-26 | `tests/core/test_in_memory_processed_events.py::test_past_capacity_the_oldest_id_is_dropped`, `..._a_repeat_claim_does_not_refresh_the_age_of_an_id` | Passing |
