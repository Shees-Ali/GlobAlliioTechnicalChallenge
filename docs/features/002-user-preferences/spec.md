# Feature 002: User preferences
Status: Implemented, merged to `main`
Builds on: 001 (event intake and dispatch)

Source: the brief ("enable or disable per category, representable by a simple map") and the Initial Functional Specification (`docs/functional-spec.md`), section 5 and acceptance scenarios 5 to 8 (mapped to this feature in decision 3).

## Purpose
A player can turn notifications off for a whole category, Game Events or Social Events, and back on again. The module checks the recipient's preference before delivery, so a disabled category is never delivered. The check sits between the checks 001 already does and the delivery call, and changes nothing else about how an event is handled.

## User stories
- As a player, I disable Game Events so that I am not interrupted by progress notifications, while still getting friend requests.
- As a player, I enable a category again and start receiving it from that point on.
- As a new player who never touched my settings, I receive every notification.
- As a producer, I am told when my event was valid but not delivered because of the player's preference, so I do not retry it.

## Requirements
Numbering continues from 001 (FR-1 to FR-25).

**Preferences**
- FR-26: Each player has an on or off setting for each category (Game Events, Social Events). A player's preferences can be represented as a simple map from category to on or off.
- FR-27: The setting for one category does not affect any other category, and one player's settings do not affect any other player.
- FR-28: A category with no recorded setting is on. A player with no recorded preferences receives every category. This includes a category added to the module later.

**Checking**
- FR-29: Before delivery, the module checks the recipient's setting for the event's category. If it is off, the event is suppressed: delivery is not invoked, and the submitter is told the event was suppressed, as a success and not as an error.
- FR-30: Only the recipient's preferences are checked. The acting player's preferences (for example the player who sent a friend request) have no effect.
- FR-31: Validation and player lookup (FR-14 to FR-16, FR-19) run before the preference check. An invalid event is rejected under FR-15 whatever the recipient's preferences, so a suppressed outcome always means the event was valid.

**Event IDs** (consequence of decision 11)
- FR-32: A suppressed event uses up its `event_id`. A later event with the same ID is a duplicate (FR-20), even if the recipient has enabled the category since. This refines FR-21: an ID is used up once the event passes validation and lookups, whether it is then delivered or suppressed. FR-22 (release on delivery failure) is unchanged.

**Changing preferences**
- FR-33: A player's setting can be changed per category, to on or off. The change applies to every event submitted after the change returns. Changing one category leaves the others as they were.
- FR-34: A change is rejected with an error naming the reason if the player ID is not in the user directory, the category is not one the module supports, or the value is not on or off. A rejected change leaves preferences unchanged.
- FR-35: Preferences can be changed over HTTP, through an adapter that holds no rules, in the same way events are submitted over HTTP in 001. The route's shape is decided in the plan.
- FR-36: Turning a category back on does not replay notifications suppressed while it was off. They are never delivered. (Added after checking against functional spec scenario 8, Q19.)

## Acceptance criteria
| ID | Given / When / Then | Covers |
|---|---|---|
| AC-27 | Given player 1 has turned Game Events off, when a Level Up for player 1 is submitted, then delivery is not invoked and the outcome is suppressed. | FR-26, FR-29 |
| AC-28 | Given player 1 has turned Game Events off, when a Friend Request to player 1 is submitted, then it is delivered. | FR-27 |
| AC-29 | Given player 1 has no recorded preferences, when one event of each of the six types is submitted for player 1 as recipient, then all six are delivered. | FR-28 |
| AC-30 | Given player 1 has turned Game Events off, when a Level Up for player 2 (no preferences) is submitted, then it is delivered. | FR-26, FR-27 |
| AC-31 | Given user 3 has turned Social Events off and user 1 has not, when user 3 sends user 1 a friend request, then user 1 is notified. | FR-30 |
| AC-32 | Given a suppressed event, when it is submitted over HTTP, then the response is `200` with `{"status": "suppressed"}`. | FR-29, FR-35 |
| AC-33 | Given player 1 has Game Events off, when an invalid Level Up for player 1 (for example with the new level missing) is submitted, then it is rejected with an error, not suppressed. Same for a Friend Request to player 1 from an unknown player when player 1 has Social Events off. | FR-31 |
| AC-34 | Given a Level Up for player 1 was suppressed, when player 1 turns Game Events on and the same event is resent with the same `event_id`, then the outcome is duplicate and delivery is not invoked. | FR-32 |
| AC-35 | Given a Level Up for player 1 was suppressed, when player 1 turns Game Events on, then delivery is not invoked for the suppressed event; and when a new Level Up with a different `event_id` is then submitted, delivery is invoked exactly once, for the new event only. | FR-33, FR-36 |
| AC-36 | Given player 1 has Game Events off, when player 1 turns Social Events off and then on, then Game Events is still off. | FR-27, FR-33 |
| AC-37 | Given a preference change for an unknown player, an unsupported category, or a value that is not on or off, when it is submitted, then it is rejected with an error naming the reason and no player's preferences change. | FR-34 |
| AC-38 | Given the running app, when Game Events is turned off for player 1 over HTTP and a Level Up for player 1 is then posted to `/events`, then the response is suppressed and delivery is not invoked. | FR-33, FR-35 |

Functional spec scenarios covered: 5 (AC-27), 6 (AC-28, AC-30), 7 (AC-29), 8 (AC-35, AC-36).

## Edge cases
- Turning off a category that is already off, or on when already on, succeeds and changes nothing.
- A duplicate takes precedence over the preference check. Resending an ID already used returns duplicate, whether the first event was delivered or suppressed (FR-32).
- A preference change made while an event for the same player is being handled may or may not apply to that event. It applies to every event submitted after the change returns (FR-33).
- A suppressed notification is dropped, not queued. Enabling the category later does not deliver it (FR-36).
- Preferences are held in memory and lost on restart, after which every player is back to all categories on (FR-28). Known limitation, listed in the README at packaging.
- Anyone who can reach the HTTP route can change any player's preferences. There is no authentication. Known limitation of the mock.

## Not in this feature
- Granularity finer than category, such as per event type or per friend (Q5).
- Reading preferences back over HTTP (Q20).
- Quiet hours, digests, or storing suppressed notifications for later.
- Authentication and authorisation of preference changes.
- Persistent or shared preference storage (the plan puts storage behind an interface).
- The delivery contract (feature 003) and the demo page (feature 004).

## Open questions
| # | Question | Agent recommendation | Status |
|---|---|---|---|
| Q5 | Is per-category the only granularity? (base open question) | Yes. The brief says "simplified" and names categories. | Decided (owner): per category only. FR-26. |
| Q19 | Does this spec match functional spec scenarios 5 to 8? | The owner supplied the functional spec, now at `docs/functional-spec.md`. | Decided: scenarios 5 to 7 were covered. Scenario 8's "without replaying" was only an edge case, so FR-36 was added and AC-35 widened. FR-27 now names other players too. |
| Q20 | Should there also be a way to read a player's preferences over HTTP? | Not in this feature. It is not needed to prove the ACs, and 004 can add it if the demo needs it. | Decided (owner): not in 002. |

Decided before drafting (owner, structured question tool), moved to the decision log when the spec is approved:
- Missing setting is on (FR-28).
- A suppressed event returns a new `suppressed` outcome, a success (FR-29, AC-32).
- A suppressed event uses up its `event_id` (FR-32).
- Preferences are changed through a core call and a thin HTTP route (FR-33, FR-35).

## Traceability
| ID | Test | Status |
|---|---|---|
| AC-27 | `tests/core/test_service_preferences.py::test_a_disabled_category_is_suppressed_and_not_delivered`, `tests/core/test_service_preferences.py::test_every_type_in_a_disabled_category_is_suppressed` | Passing |
| AC-28 | `tests/core/test_service_preferences.py::test_a_disabled_category_does_not_affect_the_other_category` | Passing |
| AC-29 | `tests/core/test_service_preferences.py::test_with_no_recorded_preferences_every_event_type_is_delivered`, `tests/core/test_in_memory_preferences.py::test_every_category_is_on_when_nothing_is_recorded` | Passing |
| AC-30 | `tests/core/test_service_preferences.py::test_one_players_setting_does_not_affect_another_player` | Passing |
| AC-31 | `tests/core/test_service_preferences.py::test_only_the_recipients_preferences_are_checked` | Passing |
| AC-32 | `tests/api/test_preferences_route.py::test_a_suppressed_event_returns_200_with_a_suppressed_status` | Passing |
| AC-33 | `tests/core/test_service_preferences.py::test_an_invalid_event_is_rejected_not_suppressed`, `tests/core/test_service_preferences.py::test_an_unknown_actor_is_rejected_not_suppressed` | Passing |
| AC-34 | `tests/core/test_service_preferences.py::test_a_suppressed_event_uses_up_its_id` (plus `tests/core/test_service_preferences.py::test_a_failed_preference_read_releases_the_id` for FR-22) | Passing |
| AC-35 | `tests/core/test_preferences.py::test_turning_a_category_back_on_does_not_replay_and_delivers_only_new_events` | Passing |
| AC-36 | `tests/core/test_preferences.py::test_changing_one_category_leaves_the_other_as_it_was` | Passing |
| AC-37 | `tests/core/test_preferences.py::test_a_bad_change_is_rejected_and_changes_nothing`, `tests/api/test_preferences_route.py::test_a_rejected_change_returns_422_with_its_code` | Passing |
| AC-38 | `tests/api/test_preferences_route.py::test_a_change_over_http_applies_to_the_next_posted_event`, `tests/api/test_preferences_route.py::test_the_default_app_shares_one_store_between_both_services` | Passing |
