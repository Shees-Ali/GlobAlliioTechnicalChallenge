# Gaming notifications

A real-time notification module for an online multiplayer gaming platform, built for the Globalli take-home challenge. Game and social systems submit events; the module works out who to notify, checks that player's preferences, builds the notification and hands it to the in-app channel.

Everything runs in one process with simulated dependencies. No broker, database, WebSocket server or game client is needed.

## Requirements
Python 3.12 or newer.

## Install
```
git clone https://github.com/Shees-Ali/GlobAlliioTechnicalChallenge.git
cd GlobAlliioTechnicalChallenge
python -m venv .venv
.venv\Scripts\activate            # Windows
source .venv/bin/activate         # macOS and Linux
pip install -e ".[dev]"
```

## Run the tests
```
pytest
```

## Run the demo script
```
python -m notifications.demo
```
No server needed. It plays the brief's four example calls, the other two required events, a category turned off and on again, a player with no in-app channel, a player whose channel is down, and a resent event, then prints what each player's channel holds.

## Run the app and the live demo page
```
uvicorn notifications.api.app:app
```
Open http://127.0.0.1:8000/demo. Each player's column is their in-app feed, updated live over Server-Sent Events. Use the form to fire any of the six events, the checkboxes to turn a player's Game or Social events on and off, and "Resend last event" to show a duplicate. Notifications already delivered load as plain history; only new ones are highlighted, so a reload never shows old notifications as new.

You can also post events directly:
```
curl -X POST http://127.0.0.1:8000/events -H "Content-Type: application/json" \
  -d '{"event_id": "evt-1", "type": "level_up", "player_id": 1, "new_level": 15}'
```

## Main features
- **Six event types**: level up, item acquired, challenge completed, friend request, friend accepted, new follower. Each produces a clear message for the right player, for example "Congratulations! You've reached level 15!" or "Player 'Carol' has sent you a friend request." Friend accepted notifies the original requester.
- **Validation**: unknown types, missing or malformed fields, unknown players and self-targeted social events are rejected with a reason code.
- **Idempotency**: each event carries an `event_id`. A resend of a completed ID returns `duplicate` and notifies no one. A copy sent while the first is still being processed gets `409 EVENT_IN_PROGRESS`, a retryable error, because the first may still fail.
- **Preferences**: each player can turn Game events and Social events on or off. Both are on until changed. A turned-off category suppresses the notification, and turning it back on does not replay it.
- **In-app delivery**: the module makes one delivery attempt per processing attempt. Failed attempts can be retried using the same event ID. An uncertain delivery outcome can produce duplicates; receivers can use the event ID, which every notification carries, to deduplicate. A player with no in-app channel gets `undeliverable`. A channel failure answers `503`.
- **Transport neutral core**: the rules live in `notifications.core`, which has no web framework imports (checked by a test). HTTP is one thin adapter around it, and runs the synchronous core in a thread pool so a slow delivery does not block other requests.

The design, a diagram and the exact guarantees are on one page: [docs/architecture.md](docs/architecture.md).

## The brief's example usage
The simulated producers use Python's snake_case names. Each method carries the brief's name in a comment.

| Brief | This project |
|---|---|
| `gameEngine.playerLeveledUp(1, 15)` | `game_engine.player_leveled_up(1, 15)` |
| `gameEngine.itemAcquired(2, "SwordOfAzeroth")` | `game_engine.item_acquired(2, "SwordOfAzeroth")` |
| `socialSystem.friendRequestSent(3, 1)` | `social_system.friend_request_sent(3, 1)` |
| `socialSystem.friendRequestAccepted(1, 3)` | `social_system.friend_request_accepted(1, 3)` |

They live in `src/notifications/simulated/producers.py` and are given a submit function, so the same producer can submit in-process (as the demo script does) or over any transport.

## HTTP interface
| Route | Purpose |
|---|---|
| `POST /events` | Submit an event. `200` with `{"status": "processed" \| "suppressed" \| "undeliverable" \| "duplicate"}`, `422` with `{"code", "message"}` for an invalid event, `409` with `EVENT_IN_PROGRESS` while another copy of the same `event_id` is still being processed, `503` with `DELIVERY_FAILED` when the channel is down. |
| `PUT /preferences` | `{"player_id": 1, "category": "game" \| "social", "enabled": false}`. `200` or `422`. |
| `GET /demo` | The live demo page. |
| `GET /demo/players` | The sample players, their delivery tokens and their current Game and Social settings. |
| `GET /feeds/{token}` | Server-Sent Events: what the token holds as `history`, then new deliveries as `live`. Each item includes the notification's `event_id`. |

Event payloads are flat JSON: `event_id`, `type`, and the type's fields.

| Type | Fields | Recipient |
|---|---|---|
| `level_up` | `player_id`, `new_level` | `player_id` |
| `item_acquired` | `player_id`, `item_name` | `player_id` |
| `challenge_completed` | `player_id`, `challenge_name` | `player_id` |
| `friend_request` | `requester_id`, `recipient_id` | `recipient_id` |
| `friend_accepted` | `accepter_id`, `requester_id` | `requester_id` |
| `new_follower` | `follower_id`, `followed_id` | `followed_id` |

Sample players: 1 Alice, 2 Bob, 3 Carol, 4 Dave, 5 Eve (no in-app channel, so events for her are undeliverable), 6 Frank (his channel is unreachable, so delivery fails with `503`).

## Project layout
```
src/notifications/
  core/        rules: event registry, validation, preferences, the service, ports (no framework)
  simulated/   in-memory stand-ins: user directory, preference store, event-ID store, in-app channel, producers
  api/         FastAPI adapter, demo routes and the demo page
  demo.py      the demo script
tests/         automated tests for each behavioural acceptance criterion, referenced by ID
docs/
  functional-spec.md   the functional spec the features trace to
  spec/                constitution, base spec, templates, feature log
  features/            spec, plan and tasks for each feature (001 to 004)
  ai-process/          the decision log, prompt log and tools used
```

## How it was built
Spec-driven with an AI agent (Claude Code), one feature at a time, each with a spec, a plan and test-first tasks reviewed by the project owner. The decisions, options considered, owner prompts and reversals are in `docs/ai-process/README.md`.

## Known limitations
- **Everything is in memory.** Preferences, used event IDs and delivered notifications are lost on restart and are not shared between processes, so the app must run as a single process.
- **Event IDs.** A reused ID is silently treated as a duplicate. The store keeps the most recent 10,000 completed IDs and drops the oldest, so an event resent after that many newer ones is processed again. IDs still being processed are never dropped. The store is in memory, so a restart forgets every ID. A persistent store would also need IDs left in progress by a crash to expire, or their retries would get `409` for ever.
- **Delivery is simulated.** The in-app channel records what each client would have received (the latest 100 per token) and fakes an unreachable channel for player 6. Delivery means "handed to the channel", not "seen by the player".
- **Delivery guarantee.** The module does not by itself guarantee at-least-once delivery: state is in memory, undeliverable events are dropped by design, there is no durable pending work, and producer retries are not enforced. A delivery that takes effect and then fails is released and can be delivered again by the retry; both copies carry the same `event_id`. It supports an at-least-once workflow only when combined with producer retries and durable storage.
- **No backlog.** A notification for a player with no in-app channel is not kept for later, by design, so a player is not flooded with popups when they connect. The platform is assumed to keep a notification history elsewhere.
- **No authentication.** Anyone who can reach the app can submit events, change any player's preferences and read any feed.
- **Demo page.** The page opens one connection per feed. Browsers allow about six connections per host over HTTP/1.1, so a second tab of the page in the same browser may stall.
- **Sample data is fixed.** The six sample players are built in; there is no way to add players at runtime.
- **Out of scope**: PvP events (optional in the brief), real WebSocket or push delivery, a message broker, persistence.
