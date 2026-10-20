# Feature 004: Demonstration
Status: Implemented, awaiting owner review before commit
Builds on: 001 (event intake and dispatch), 002 (user preferences), 003 (in-app delivery)

Source: the brief ("example usage that shows events triggering notifications", with `gameEngine.playerLeveledUp(1, 15)`, `gameEngine.itemAcquired(2, "SwordOfAzeroth")`, `socialSystem.friendRequestSent(3, 1)`, `socialSystem.friendRequestAccepted(1, 3)`; "a README is recommended") and the Initial Functional Specification (`docs/functional-spec.md`), section 2 "Demonstrated flow" and acceptance scenarios 1 and 9. Settles the demo half of base question Q2 (separate frontend or not) and Q8 (limits stated in the README).

## Purpose
001 to 003 built the module and prove it with tests, but nothing yet shows it working the way the brief asks: game and social systems firing events and players receiving notifications. This feature adds simulated producers with the brief's calls, a script that plays a full scenario with no server, and a page served by the app where each player's notifications appear live. It closes the project with the README.

## User stories
- As a reviewer, I run one command and see the brief's four example calls, and the other required events, produce the right notifications for the right players, with no server, broker or game client.
- As a reviewer, I open a page, fire events and change preferences, and watch each player's feed update live.
- As a developer, I write a game or social producer against a small set of calls and do not need to know how the event reaches the module.
- As a reviewer, I clone the repo and follow the README to install, run, test and demo it, and I can see its known limits.

## Requirements
Numbering continues from 003 (FR-37 to FR-47).

**Simulated producers**
- FR-48: A simulated game engine offers level up (player, new level), item acquired (player, item name) and challenge completed (player, challenge name). A simulated social system offers friend request sent (requester, recipient), friend request accepted (accepter, original requester) and new follower (follower, followed). The argument order matches the brief's examples. Methods use Python's snake_case (`player_leveled_up`). Each method's source carries a comment with the brief's camelCase name (`playerLeveledUp`), and the README shows both side by side. (Q25.)
- FR-49: Each producer call builds one event in the module's contract (001), with a new `event_id` per call, submits it, and returns the outcome. Producers do not decide recipients, messages or preferences. Those stay in the module.
- FR-50: Producers submit through a function given to them when they are built. They do not know whether the event goes in-process or over a transport. (Owner, before drafting.)

**Demo script**
- FR-51: One documented command runs the demo script. It needs no running server, broker, WebSocket or game client (functional spec scenario 9). It wires the same simulated dependencies and sample users as the running app, and submits in-process.
- FR-52: The script plays, in order: the brief's four example calls; challenge completed and new follower; a category turned off and an event in it suppressed; the category turned on again and the next event delivered, with no replay of the suppressed one; an event for player 5 (undeliverable); an event for player 6 (delivery failed); and a resend of an earlier `event_id` (duplicate). For each step it prints the call, the outcome and the message delivered, if any.
- FR-53: The script ends by printing what each player's channel holds.

**Live page**
- FR-54: The running app serves a demo page at a documented address.
- FR-55: The page shows one feed per sample player. A feed is addressed by delivery token, not player ID, the way a push token addresses a device (Q28). A notification delivered to a token appears in that token's feed without reloading, pushed over Server-Sent Events. (Owner, before drafting.) No other feed shows it.
- FR-56: When a feed connects, it first receives what the channel already holds for that token, in delivery order, then each new one as it is delivered. (Q26.) This is a view of what was delivered to that token, not a replay of anything missed:
  - Suppressed and undeliverable events were never delivered, so they never appear. A player who had no token when an event was processed does not receive it after getting a token, on any feed (FR-41, Q24).
  - A delivery that failed (FR-39) was never recorded, so it never appears either.
- FR-60: Each item a feed sends is marked as either history (already held when the feed connected) or live (delivered while the feed is open). Only live items are new notifications. The page shows history in the feed list without any new-notification highlight, so a late connect or reload never presents past notifications as new popups. A real client would follow the same rule.
- FR-57: The page can fire each of the six event types for chosen players and values, and turn each player's categories on and off, through the existing `POST /events` and `PUT /preferences` routes. It shows the outcome of each action (status or error code). (Q29.)
- FR-58: Pushing to the page never changes a delivery outcome. A feed that is closed, slow or absent does not make delivery fail or wait.

**README** (owner, before drafting; settles Q8)
- FR-59: The repository has a README with: what the project is; how to install, run the app, run the tests, run the demo script and open the demo page; the main features and the event contract with an example; the brief's four example calls next to the snake_case producer calls (FR-48); where the specs and the AI process log live; and a known limitations section that lists the limits recorded in decisions 11, 15 and 20 of the decision log.

## Acceptance criteria
| ID | Given / When / Then | Covers |
|---|---|---|
| AC-52 | Given a game engine built with a submit function that records what it is given, when level up is called with (1, 15), then it submits one valid `level_up` event for player 1, level 15, and returns the outcome the submit function returned. A second call submits a different `event_id`. | FR-48, FR-49, FR-50 |
| AC-53 | Given producers wired in-process to the sample users, when each of the six producer calls is made once, then each notification reaches the right player with the right content. In particular, friend request sent (3, 1) notifies player 1 about Carol, and friend request accepted (1, 3) notifies player 3 about Alice. | FR-48, FR-49 (scenarios 1 to 4) |
| AC-54 | Given no server is running, when the demo script is run, then it completes and reports, step by step, processed for the six events, suppressed, processed after re-enabling, undeliverable for player 5, delivery failed for player 6, and duplicate for the resend. | FR-51, FR-52 (scenario 9) |
| AC-55 | Given the demo script has run, when its final listing is read, then each player's channel holds exactly the notifications delivered to them, and the suppressed one is absent. | FR-52, FR-53 (scenario 8) |
| AC-56 | Given the running app, when the demo page address is requested, then it returns an HTML page. | FR-54 |
| AC-57 | Given a feed is open for player 1's token, when a valid Level Up for player 1 is posted, then the feed receives that notification. A feed open for player 2's token receives nothing. | FR-55 |
| AC-58 | Given player 1's token already holds two notifications, when a feed for that token connects and then a third is delivered, then it first receives the two, in order, marked as history, and then the third marked as live. | FR-56, FR-60 |
| AC-62 | Given a player with no token, and an event for them that was undeliverable, when the player later gets a token and a feed for that token connects, then the feed receives nothing from before. Only events processed after the token exists reach it. | FR-56 (FR-41) |
| AC-59 | Given a feed for player 1's token that has disconnected or stopped reading, when a valid event for player 1 is submitted, then the outcome is still processed and the channel holds the notification. | FR-58 |
| AC-60 | Given the demo page, when its content is checked, then it offers all six event types and the preference controls, and it posts to `/events` and `/preferences`. Manual check: in a browser, firing an event and toggling a preference shows the outcome and updates the right feed (recorded in the decision log). | FR-57 (Q27) |
| AC-61 | Given the repository, when the README is read, then it contains the install, run, test, demo script and demo page commands, and a known limitations section. | FR-59 |

## Edge cases
- A feed for a token that has nothing yet stays open and receives nothing until something is delivered.
- Player 6's feed never receives anything: the channel is unreachable, so nothing is recorded or pushed.
- Player 5 has no token, so the page has no feed to show for them. The page says so instead of showing an empty feed.
- A feed connecting while a notification is being delivered receives it once, not twice and not zero times, and marked either history or live, not both.
- Reloading the page shows the same feed, all of it as history. Nothing is presented as new.
- Opening the page twice gives two feeds per player, each receiving every notification.
- The script and the running app do not share state. The script wires its own in-memory dependencies, so running it does not change what the page shows.
- The page has no authentication. Anyone who can reach the app can read every feed. Listed in the README.

## Not in this feature
- A real game client, WebSocket delivery or connection management (functional spec section 2).
- Producers that submit over HTTP or a broker. FR-50 allows them, but the script does not need one and the page posts from the browser.
- Authentication, multiple processes, persistence. Listed as limitations in the README.
- PvP events (base Q6, still optional and out of the initial scope).
- A browser test framework. The page's interaction is checked by hand (Q27).

## Open questions
| # | Question | Agent recommendation | Status |
|---|---|---|---|
| Q25 | Producer method names: the brief's camelCase (`playerLeveledUp`) or Python's snake_case (`player_leveled_up`)? | snake_case, as the rest of the code is PEP 8. The README shows the brief's call next to ours. | Decided (owner): snake_case, with the brief's camelCase name as a comment in the producer file and shown in the README. FR-48, FR-59. |
| Q26 | Should a feed receive what the channel already holds when it connects? | Yes, so a page reload or a late connect shows the same feed. It reads the channel's bounded record (FR-46), so at most 100 per token. | Decided (owner): yes, with a condition. It must not deliver what the player missed while they had no token, and it must not cause popups on a late connect. FR-56, FR-60, AC-58, AC-62. |
| Q27 | How is the page's interaction tested, given no browser test framework? | An automated check of the page content (AC-60) plus a manual browser check, recorded in the decision log. Adding Playwright or Selenium is a new heavy dependency for one page. | Decided (owner): yes. A new dependency to show a simple scenario is not justified, and the automated tests already prove the behavior behind the page. AC-60. |
| Q28 | Are feeds addressed by delivery token or by player ID? | By token. The feed stands in for that client's connection, the channel is keyed by token, and the push path needs no directory lookup. The page gets the sample players and their tokens from the app. | Decided (owner): by token, the way a Firebase push token addresses a device. FR-55, AC-57. |
| Q29 | Should the page fire events and change preferences, or only watch while the script or curl drives it? | Fire and change, so the demo is self-contained in the interview. It uses the existing routes, so no new rules. | Decided (owner): self-contained. FR-57, AC-60. |

Decided before drafting (owner, structured question tool), moved to the decision log when the spec is approved:
- The demo is a script and a live page (settles the demo half of Q2: the page is served by the same app, not a separate frontend).
- Producers take an injected submit function (FR-50).
- Live push is Server-Sent Events (FR-55).
- The README is part of 004 (FR-59, settles Q8).

## Traceability
| ID | Test | Status |
|---|---|---|
| AC-52 | `tests/core/test_producers.py::test_level_up_submits_one_valid_event_and_returns_the_outcome`, `::test_each_call_gets_a_new_event_id`, `::test_each_call_builds_its_event_in_the_briefs_argument_order` | Passing |
| AC-53 | `tests/core/test_wiring.py::test_each_producer_call_reaches_the_right_player_with_the_right_content` | Passing |
| AC-54 | `tests/test_demo_script.py::test_the_script_reports_each_step_in_order_without_a_server` | Passing |
| AC-55 | `tests/test_demo_script.py::test_each_channel_holds_exactly_what_was_delivered`, `::test_the_suppressed_notification_is_not_replayed` | Passing |
| AC-56 | `tests/api/test_demo_routes.py::test_the_demo_page_is_served` | Passing |
| AC-57 | `tests/api/test_demo_routes.py::test_a_posted_event_is_pushed_to_its_tokens_feed_only`, `tests/core/test_channel_subscriptions.py::test_a_subscription_receives_only_its_own_tokens_deliveries` | Passing |
| AC-58 | `tests/core/test_channel_subscriptions.py::test_a_subscription_gets_what_the_token_holds_as_history_then_live`, `::test_a_delivery_while_subscribing_is_history_or_live_never_both_nor_neither`, `tests/api/test_demo_routes.py::test_the_stream_sends_held_notifications_as_history_then_new_ones_as_live` | Passing |
| AC-59 | `tests/core/test_channel_subscriptions.py::test_a_feed_that_stops_reading_is_closed_and_delivery_still_succeeds`, `::test_a_closed_subscription_receives_nothing_and_does_not_break_delivery`, `::test_delivery_still_succeeds_after_the_feeds_event_loop_has_ended` | Passing |
| AC-60 | `tests/api/test_demo_page.py` (all tests), plus the browser check run by the owner and by the agent (decision 29) | Passing |
| AC-61 | `tests/test_readme.py::test_the_readme_covers_it` | Passing |
| AC-62 | `tests/core/test_channel_subscriptions.py::test_an_undeliverable_event_never_reaches_a_token_issued_later` | Passing |
