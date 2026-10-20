# Plan: Feature 004 Demonstration

Implements: [spec.md](spec.md)
Status: Implemented, awaiting owner review before commit

## 1. Summary
Two simulated producers, `GameEngine` and `SocialSystem`, build events in the 001 contract and pass them to a submit function they are given. The wiring that `build_default_app` does today moves into one shared function, so the demo script (`python -m notifications.demo`) and the app use the same simulated dependencies. `InAppChannel` gains subscriptions. A subscriber gets a snapshot of what the token already holds, sent marked `history`, and then each new delivery, sent marked `live`. Both are taken under the channel's existing lock, so nothing is missed or sent twice, and no item is both history and live (FR-60). A new `api/demo.py` router serves the page, a player list and an SSE stream per token, with items marked `history` or `live`. The project closes with a root `README.md`.

## 2. Technical context
- Language and framework: unchanged (Python 3.12, FastAPI). SSE uses Starlette's `StreamingResponse`, already installed with FastAPI.
- New dependencies: none. No SSE library, no browser test framework (Q27), no pytest-asyncio (async code is tested with `asyncio.run` inside plain tests).
- Storage: unchanged, in memory. Subscriptions live only while a feed is open.
- Testing approach: unit tests for the producers, the subscriptions and the stream generator; a test that runs the script in-process; `TestClient` tests for the page and players routes; a content check of the page; a README check; one hand run under uvicorn in a browser (AC-60).
- Constraints: FR-41 and FR-60 (no backlog and no popups on a late connect), FR-58 (a feed never affects delivery), functional spec scenario 9 (no server for the script), P2 (nothing in `core` changes).

## 3. Constitution check
- [x] P1 Spec first: tasks cite FR-48 to FR-60 and AC-52 to AC-62.
- [x] P2 Core has no framework dependencies: `core` is not touched. SSE lives in `api/`, subscriptions in `simulated/`.
- [x] P3 Abstractions at seams likely to change: one small new type, the `Submit` callable the producers take (FR-50), because the producers' transport is what changes in a real platform. No new port in `core`: live push is a property of the simulated channel, not a rule.
- [x] P4 Open for extension, closed for modification: the demo routes are a separate router added by `build_default_app`; `create_app` and its intake routes do not change. A new event type needs one producer method and no other change.
- [x] P5 Simplest thing that meets the brief: one HTML file with plain JavaScript and `EventSource`, no build step, no frontend framework.
- [x] P6 One command to run, one to test: plus one documented command for the script.
- [x] P7 Tests prove the spec: section 6 maps all eleven ACs.
- [x] P8 Honest scope: the README lists every known limit (FR-59).
- [x] P9 Process is logged: decisions 21 to 24 so far.
- [x] P10 One feature at a time: this is the last picked feature. PvP stays out.

## 4. Approach

### Files
```
src/notifications/simulated/
  producers.py        new: Submit type, GameEngine, SocialSystem
  wiring.py           new: build_simulated() -> Simulated(service, preference_service, channel, users)
  in_app_channel.py   + subscribe(token) / Subscription, pushes each delivery to open subscriptions
src/notifications/demo.py                new: the script, run(print_line) and a __main__ guard
src/notifications/api/
  app.py              build_default_app uses build_simulated() and includes the demo router
  demo.py             new: router with GET /demo, GET /demo/players, GET /feeds/{token}
  static/demo.html    new: the page
pyproject.toml        package data for api/static/*.html
README.md             new
tests/
  core/test_producers.py           AC-52, AC-53
  core/test_channel_subscriptions.py   AC-58, AC-59, AC-62, ordering and isolation
  test_demo_script.py              AC-54, AC-55
  api/test_demo_routes.py          AC-56, AC-57, AC-60 content check
  test_readme.py                   AC-61
```

### Producers (FR-48 to FR-50)
- `Submit = Callable[[Mapping[str, Any]], Outcome]`.
- `GameEngine(submit)` with `player_leveled_up(player_id, new_level)`, `item_acquired(player_id, item_name)`, `challenge_completed(player_id, challenge_name)`.
- `SocialSystem(submit)` with `friend_request_sent(requester_id, recipient_id)`, `friend_request_accepted(accepter_id, requester_id)`, `new_follower(follower_id, followed_id)`.
- Each method has a comment with the brief's camelCase name, for example `# brief: gameEngine.playerLeveledUp(1, 15)` (Q25).
- Each call builds `{"type": ..., "event_id": str(uuid4()), <fields>}`, calls `submit`, returns its outcome, and lets its exceptions through (a `DeliveryError` reaches the caller).

### Shared wiring
`build_simulated()` builds the directory over `SAMPLE_USERS`, the preference store, the channel with `UNREACHABLE_TOKENS`, the processed-event store, `NotificationService` and `PreferenceService`, and returns them in a small dataclass with the user list. `build_default_app()` and the script both call it, so they cannot drift apart (FR-51). Each call builds new objects, so the script and the app never share state (spec edge case).

### Channel subscriptions (FR-55, FR-56, FR-58, FR-60)
```
subscribe(token) -> Subscription
  under the lock: history = list(record for token); register subscription
  returns Subscription(history, live queue)

deliver(notification, token)
  unreachable -> DeliveryError, nothing recorded, nothing pushed        (unchanged)
  under the lock: append to the record; for each subscription on token: offer(notification)
  log                                                                   (unchanged)

Subscription.offer(n)   never blocks, never raises into deliver:
  loop.call_soon_threadsafe(put_nowait); if the queue is full, the subscription is closed
Subscription.close()    removes it from the channel (called when the feed disconnects)
```
- Taking the snapshot and registering in the same lock as the append means a delivery is either in the history or in the live queue, never both, never neither (edge case).
- The live queue is an `asyncio.Queue` bound to the stream's event loop. `call_soon_threadsafe` lets `deliver` run on any thread: the request thread under uvicorn, `TestClient`'s portal thread, or plain code.
- Only delivered notifications are recorded or pushed. Suppressed, undeliverable and failed events never reach `deliver`'s append, so they can never appear on a feed (FR-56, AC-62). No new rule is needed: 003 already guarantees this.

### Stream and routes (`api/demo.py`)
- `GET /feeds/{token}` returns `text/event-stream`. It sends each history item as `event: history`, then each live item as `event: live`, with `data:` a JSON object `{recipient_id, category, event_type, message}`. A comment line every 15 seconds keeps the connection open. When the client disconnects, the subscription is closed in a `finally`.
- The generator is a plain async function over a `Subscription`, so it can be tested without an HTTP server (R10).
- `GET /demo/players` returns each sample player's ID, name, token (or `null`) and whether the token is unreachable. The page uses it to open one feed per token and to label players 5 and 6.
- `GET /demo` returns `static/demo.html`.

### Page (`static/demo.html`, FR-57, FR-60)
Plain HTML, CSS and JavaScript. One column per player with an `EventSource` on `/feeds/{token}`. `history` items are added to the list plainly. `live` items are added with a short highlight, which stands in for a popup. Player 5 shows "no in-app channel" and opens no feed; player 6 shows "channel unreachable". Forms fire each of the six event types with chosen players and values (`POST /events`, a new `event_id` per send, plus a "resend last" button to show `duplicate`), and Game and Social toggles per player (`PUT /preferences`). Each action's status or error code is shown.

### Script (`notifications/demo.py`, FR-51 to FR-53)
`run(print_line=print)` calls `build_simulated()`, makes `GameEngine` and `SocialSystem` with `submit = service.handle_event`, and plays the steps of FR-52 in order. Each step prints the brief-style call, the outcome (or `DELIVERY_FAILED`) and the message delivered, then the script prints each player's channel. It returns the list of step outcomes so the test can check them. The resend step re-submits a payload recorded by a small wrapper around `submit`, so the producers need no `event_id` parameter.

### How it connects
Producers sit in front of 001's `handle_event`; the page drives 001's and 002's existing routes; feeds read 003's channel. `core` is unchanged.

## 5. Options and decisions

| Decision | Options considered | Recommendation and why | Tradeoff accepted | Owner decision |
|---|---|---|---|---|
| D1 Where live push lives | (a) subscriptions in `InAppChannel`, (b) a separate broadcaster wrapping the channel as another `NotificationDelivery`, (c) the stream polls `delivered_to` | (a). The history snapshot and the live hand-off must share one lock with the append, or a notification delivered while a feed connects is lost or doubled. The channel already holds that lock. | The simulated channel gets a second job (record and push). A real platform would split them. | (a) (owner) |
| D2 A feed that stops reading | (a) a bounded live queue, and a full feed is closed (the browser reconnects and gets history), (b) drop new items for that feed only, (c) unbounded queue | (a). Delivery never waits or fails (FR-58), and the page recovers to a correct state by itself. (b) leaves a silent gap; (c) can grow without limit. | A very slow feed reconnects and sees recent items as history, not live. Queue size 100, the same as the channel record. | (a) (owner) |
| D3 Shared wiring | (a) one `build_simulated()` used by the app and the script, (b) the script wires its own copy | (a). FR-51 says the same dependencies; one function keeps them the same. | `build_default_app` is refactored, covered by its existing tests. | (a) (owner) |
| D4 Where the demo routes live | (a) a separate router in `api/demo.py`, added by `build_default_app`, (b) more parameters and routes in `create_app` | (a). The intake routes stay as they are (P4), and the tests that build `create_app` with fakes are not affected. | The default app has routes that an app built with `create_app` alone does not. | (a) (owner) |
| D5 How the script resends for the duplicate step | (a) a recording wrapper around `submit`, (b) an optional `event_id` argument on each producer method | (a). The producers keep the brief's argument lists exactly. | The script has a few lines of wrapper. | (a) (owner) |
| D6 Script command | (a) `python -m notifications.demo`, (b) a console script `notifications-demo` in `pyproject.toml`, (c) a `scripts/demo.py` file | (a). Works after the existing install with nothing new, and on every OS. | A slightly longer command than (b). | (a) (owner) |
| D7 Page delivery | (a) a static HTML file in the package, (b) HTML as a string in Python, (c) a separate frontend project | (a). Readable, no build step, served by the same app (Q2). Needs one `package-data` line. | Plain JavaScript, no components. | (a) (owner) |

## 6. Testing strategy

| AC | Test |
|---|---|
| AC-52 | Producer with a recording submit: `player_leveled_up(1, 15)` submits one `level_up` payload for player 1, level 15, that passes validation, and returns the submit's outcome. Two calls give different `event_id`s. |
| AC-53 | Producers wired to `build_simulated()`: each of the six calls once, then the channel holds the expected message under the expected token. Includes (3, 1) to player 1 about Carol and (1, 3) to player 3 about Alice. |
| AC-54 | `demo.run(lines.append)` in-process: the returned outcomes match FR-52's sequence exactly. No server is started. |
| AC-55 | Same run: the final listing for each player equals what was delivered; the suppressed message is absent. |
| AC-56 | `TestClient` on `build_default_app()`: `GET /demo` is `200` with `text/html`. |
| AC-57 | `asyncio.run`: subscribe to `token-1` and `token-2` on the default app's channel, post a Level Up for player 1 through `TestClient`, read the `token-1` stream: one `live` item with the message. `token-2` has nothing. |
| AC-58 | Channel with two delivered to `token-1`: the stream yields two `history` items in order; a third delivery yields one `live` item. |
| AC-59 | A subscription with a queue of size 1 that is never read: three deliveries all succeed, the channel holds all three, the subscription is closed. Also a closed subscription receives nothing and does not break delivery. |
| AC-60 | Content check of `demo.html`: all six event types, Game and Social controls, `/events`, `/preferences`, and `/feeds/`. Plus the manual browser run, recorded in the decision log. |
| AC-61 | `README.md` exists and contains `pip install -e`, `pytest`, `uvicorn notifications.api.app:app`, `python -m notifications.demo`, `/demo` and a "Known limitations" heading. |
| AC-62 | Two directories over one channel and processed store (the AC-42 pattern): an event for a player with no token is undeliverable; with a token, a new subscription's history is empty; a new event then arrives as `live`. |

## 7. Risks and open questions
- R10: `TestClient` cannot read an endless SSE response and stop cleanly; the test hangs. So the stream generator is tested directly with `asyncio.run`, and the route's wiring is checked by the hand run. The route itself is a few lines.
- R11: a disconnect must close the subscription, or closed feeds pile up. Starlette cancels the stream on disconnect, and the generator closes the subscription in `finally`. A unit test checks `finally` closes it; the hand run checks the real disconnect.
- R12: running `build_default_app` at import time already builds one set of objects. The refactor (D3) must keep `app.state.channel` the same object the service delivers to, which the existing AC-47 tests check.
- R13: the page posts arbitrary JSON to the real routes. Errors from the routes are shown on the page, not hidden, so it also demonstrates rejection (for example a self-targeted friend request).

## 8. Complexity tracking
None. The thread-safe hand-off (`call_soon_threadsafe`) is the one non-obvious piece, needed because `deliver` runs on a different thread from the stream in tests and may under uvicorn.

## 9. Extension notes
A real platform would replace the SSE feed with its WebSocket or push service as another `NotificationDelivery`, and producers would submit over a broker by passing a different `submit`. Neither needs a change in `core`.
