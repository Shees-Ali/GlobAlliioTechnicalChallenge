# Feature 003: In-app delivery
Status: Implemented, merged to `main`
Builds on: 001 (event intake and dispatch), 002 (user preferences)

Source: the brief ("in-app only, the game client is assumed to have a way to receive notifications in real time, display may be mocked") and the Initial Functional Specification (`docs/functional-spec.md`), section 2 "Downstream notification delivery" and section 4. Settles base open questions Q7 (delivery mechanism and guarantee) and Q15 (player with no delivery token).

## Purpose
001 hands each notification to a delivery dependency, but only a logging placeholder stands behind it. This feature defines the delivery contract: what the module promises when it invokes delivery, what happens when a player has no channel, and what a producer is told when delivery fails. It replaces the placeholder with a simulated in-app channel that records what each client would have received, so tests and the demo (004) can see it.

## User stories
- As a player with a connected client, I receive each notification addressed to me on my in-app channel.
- As a producer, when delivery fails I am told to retry, distinct from being told my event is invalid, so I retry only when it can help.
- As a producer, when the recipient has no in-app channel I am told so, and I do not retry an event that cannot be delivered.
- As a developer or reviewer, I can see what each player's client would have received without running a game client.

## Requirements
Numbering continues from 002 (FR-26 to FR-36).

**Delivery contract**
- FR-37: Delivery is invoked at most once for each processed event, with the notification and the recipient's delivery token. It is one attempt: the module does not retry and does not queue. (Settles Q7.)
- FR-38: Invoking delivery means the notification was handed to the in-app channel. It does not mean the player received, displayed or read it (functional spec section 4).
- FR-39: Delivery signals failure by raising a delivery error. The event's ID is then released (FR-22) and the submitter receives a delivery-failed error saying a retry may succeed. It is distinct from the invalid-event error (FR-15).

**No channel** (settles Q15)
- FR-40: If the recipient has no delivery token, or the token is blank, delivery is not invoked. The submitter is told the event was undeliverable, as a success and not as an error, because retrying cannot help.
- FR-41: An undeliverable event uses up its `event_id`, like a suppressed one (FR-32). A resend with the same ID is a duplicate, even if the player has a token by then. This is deliberate (owner, Q24): in-app notifications are in-game popups, so replaying a backlog when the player connects would flood them with popups at once. The platform is assumed to keep a notification history the player can look back through, so a dropped popup is not lost information.
- FR-42: The preference check (FR-29) comes before the token check. An event in a category the recipient has turned off is suppressed, whether or not the recipient has a token.

**Simulated channel**
- FR-43: The simulated in-app channel records each delivered notification against the token it was delivered to, in delivery order, and logs it. What was delivered to a token can be read back.
- FR-44: The simulated channel replaces the logging placeholder in the running app.
- FR-46: The simulated channel keeps at most the 100 most recent notifications per token. Past that, the oldest for that token is dropped. The limit is one named constant, so it can be changed in one place. (Q22)
- FR-47: The simulated channel can be built with a set of unreachable tokens. Delivering to one of them raises a delivery error (FR-39), so the failure path can be shown in the running app and the demo. (Q23)

**HTTP**
- FR-45: Over HTTP, a delivery failure is answered with `503` and the reason code `DELIVERY_FAILED`. An undeliverable event is answered with `200` and `{"status": "undeliverable"}`.

## Acceptance criteria
| ID | Given / When / Then | Covers |
|---|---|---|
| AC-39 | Given player 1 has token `token-1`, when a valid Level Up for player 1 is submitted, then the simulated channel holds exactly that notification under `token-1`. | FR-37, FR-43 |
| AC-40 | Given two notifications delivered to one token and one to another, when the channel is read, then each token holds only its own notifications, in the order delivered. | FR-43 |
| AC-41 | Given a recipient with no delivery token, when a valid event for them is submitted, then delivery is not invoked and the outcome is undeliverable. | FR-40 |
| AC-42 | Given an event was undeliverable, when the same `event_id` is resent after the player gets a token, then the outcome is duplicate and delivery is not invoked. | FR-41 |
| AC-43 | Given a recipient with no token who has the event's category turned off, when the event is submitted, then the outcome is suppressed, not undeliverable. | FR-42 |
| AC-44 | Given delivery raises a delivery error, when an event is submitted, then the submitter receives a delivery-failed error, and a resend with the same `event_id` is delivered once delivery works again. | FR-37, FR-39 |
| AC-45 | Given a delivery failure, when the event is submitted over HTTP, then the response is `503` with code `DELIVERY_FAILED` and a message. | FR-39, FR-45 |
| AC-46 | Given a recipient with no token, when the event is submitted over HTTP, then the response is `200` with `{"status": "undeliverable"}`. | FR-40, FR-45 |
| AC-47 | Given the running app, when a valid event is posted, then the simulated channel, not the placeholder, holds it. | FR-44 |
| AC-48 | Given an event is processed, when `handle_event` returns, then delivery was invoked exactly once, and never retried after a failure. | FR-37 |
| AC-49 | Given a recipient whose token is blank, when a valid event for them is submitted, then delivery is not invoked and the outcome is undeliverable. | FR-40 |
| AC-50 | Given a token already holds the limit of notifications, when one more is delivered to it, then the oldest for that token is dropped, the newest is kept, and other tokens are untouched. | FR-46 |
| AC-51 | Given a channel built with `token-x` as unreachable, when a notification is delivered to `token-x`, then a delivery error is raised and nothing is recorded; delivery to other tokens still works. | FR-47, FR-39 |

## Edge cases
- A token that is present but blank is treated as no token (FR-40, Q21).
- A delivery error is the only failure mapped to `503`. Any other unexpected exception still releases the ID (FR-22) but is answered as a server error (`500`), because it signals a bug rather than an unavailable channel.
- Duplicate wins over everything: a resent ID returns duplicate whether the first outcome was processed, suppressed or undeliverable.
- The simulated channel is in memory and lost on restart. Known limitation, listed in the README at packaging.
- A notification recorded by the channel is not removed when read. Reading is for inspection, not a client inbox.

## Not in this feature
- Live push to a client over WebSocket or SSE, and connection management (004 if the demo needs it, functional spec section 2).
- Offline delivery, store-and-forward, read receipts, internal retries, ordering across tokens, latency targets.
- Notification IDs or timestamps on the notification itself (not in the brief).
- A way to read the channel over HTTP (004 decides, with the demo).
- How a token is issued or refreshed (the user directory owns it, FR-18).
- The notification history a player can look back through. Assumed to be kept by the platform, outside this module (FR-41).

## Open questions
| # | Question | Agent recommendation | Status |
|---|---|---|---|
| Q21 | Is a blank token (`""`) the same as no token? | Yes. A blank token cannot address a channel. | Decided (owner): yes. FR-40, AC-49. |
| Q22 | Should the channel keep only the most recent notifications per token? | Yes, the last 100 per token, oldest dropped. | Decided (owner): yes, 100 for now, held in a constant. FR-46, AC-50. |
| Q23 | Should the simulated channel be able to fail on purpose so the `503` path can be shown? | Yes, a set of unreachable tokens given to the channel when it is built. | Decided (owner): yes. FR-47, AC-51. |
| Q24 | Should an undeliverable notification still reach the player once they get a token (release the ID, or hold it and send on connect)? | Raised by the owner. Agent offered releasing the ID so the producer can resend, holding it until connect, or keeping FR-41. | Decided (owner): keep FR-41. Replaying would flood the player with in-game popups, and the platform is assumed to keep a notification history. |

Decided before drafting (owner, structured question tool), moved to the decision log when the spec is approved:
- No token: new `undeliverable` outcome, a success, ID used up (FR-40, FR-41).
- The simulated channel is an in-memory record per token. Live push is left to 004 (FR-43).
- One attempt, the producer retries. No internal retries or queue (FR-37).
- Delivery failure over HTTP is `503` with `DELIVERY_FAILED` (FR-45).

## Traceability
| ID | Test | Status |
|---|---|---|
| AC-39 | `tests/core/test_service_delivery.py::test_a_processed_event_is_held_by_the_channel_under_the_recipients_token` | Passing |
| AC-40 | `tests/core/test_in_app_channel.py::test_each_token_holds_only_its_own_notifications_in_order` | Passing |
| AC-41 | `tests/core/test_service_delivery.py::test_a_recipient_with_no_token_is_undeliverable` | Passing |
| AC-42 | `tests/core/test_service_delivery.py::test_an_undeliverable_event_uses_up_its_id` | Passing |
| AC-43 | `tests/core/test_service_delivery.py::test_a_turned_off_category_is_suppressed_even_with_no_token` | Passing |
| AC-44 | `tests/core/test_service_delivery.py::test_a_delivery_failure_reaches_the_caller_and_the_resend_is_delivered` | Passing |
| AC-45 | `tests/api/test_delivery_route.py::test_a_delivery_failure_returns_503_with_delivery_failed`, `tests/api/test_delivery_route.py::test_any_other_delivery_exception_is_not_reported_as_503` | Passing |
| AC-46 | `tests/api/test_delivery_route.py::test_an_undeliverable_event_returns_200_with_undeliverable` | Passing |
| AC-47 | `tests/api/test_delivery_route.py::test_the_default_app_delivers_to_the_simulated_channel`, `tests/api/test_delivery_route.py::test_the_default_app_has_a_player_with_no_token`, `tests/api/test_delivery_route.py::test_the_default_app_has_a_player_whose_channel_is_unreachable` | Passing |
| AC-48 | `tests/core/test_service_delivery.py::test_a_failed_delivery_is_attempted_exactly_once` | Passing |
| AC-49 | `tests/core/test_service_delivery.py::test_a_recipient_with_a_blank_token_is_undeliverable` | Passing |
| AC-50 | `tests/core/test_in_app_channel.py::test_past_the_limit_the_oldest_for_that_token_is_dropped`, `tests/core/test_in_app_channel.py::test_the_default_limit_is_the_named_constant` | Passing |
| AC-51 | `tests/core/test_in_app_channel.py::test_an_unreachable_token_raises_and_records_nothing` | Passing |

## Amendment (decision 34): notification identity and what the delivery contract guarantees
Source: the external review of `e316a6c`. A delivery that took effect and then raised was released and retried, and delivered twice, and the notification carried nothing a receiver could use to drop the repeat. Refines FR-37 and FR-38.

**Requirements**
- FR-64: A notification carries the `event_id` of the event that produced it, so a receiver can drop a repeat by that ID. The module makes one delivery attempt per processing attempt. A failed attempt can be retried using the same `event_id`. An uncertain delivery outcome (the delivery took effect, then raised) can produce a duplicate, and a receiver can use the `event_id` to drop it. The module does not by itself guarantee at-least-once delivery: its state is in memory, undeliverable events are dropped by design (FR-41), there is no durable pending work, and producer retries are not enforced. It supports an at-least-once workflow only when combined with producer retries and durable storage.

**Acceptance criteria**
| ID | Given / When / Then | Covers |
|---|---|---|
| AC-67 | Given a valid event with `event_id` `evt-9`, when it is delivered, then the notification handed to the channel carries `event_id` `evt-9`. Given a delivery that takes effect and then raises, when the event is resent with the same ID, then both deliveries carry the same `event_id`. | FR-64 |

**Traceability**
| ID | Test | Status |
|---|---|---|
| AC-67 | `tests/core/test_service_delivery.py::test_a_notification_carries_the_event_id_of_its_event`, `::test_a_repeat_after_an_uncertain_outcome_carries_the_same_event_id` | Passing |
