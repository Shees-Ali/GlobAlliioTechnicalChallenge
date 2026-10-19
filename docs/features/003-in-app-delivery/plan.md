# Plan: Feature 003 In-app delivery

Implements: [spec.md](spec.md)
Status: Implemented, awaiting owner review before commit

## 1. Summary
`handle_event` gains one more check after the preference check: a missing or blank token returns a new `Outcome.UNDELIVERABLE` and the ID stays used. The delivery contract gets a typed failure, `DeliveryError` in `core`, which the HTTP adapter maps to `503 DELIVERY_FAILED`. A simulated `InAppChannel` replaces `ConsoleDelivery`. It records notifications per token in a bounded deque (limit in the constant `MAX_NOTIFICATIONS_PER_TOKEN = 100`), logs each one, and raises `DeliveryError` for tokens it was built to treat as unreachable.

## 2. Technical context
- Language and framework: unchanged.
- New dependencies: none.
- Storage: in memory (the channel's record), lost on restart.
- Testing approach: unit tests for the channel and the service, `TestClient` tests for the two new HTTP answers, one hand run under uvicorn.
- Constraints: functional spec sections 2 and 4 (delivery is simulated, invoking it does not mean the player saw it), FR-22 (release on failure) and AC-8 (delivery invoked before return) from 001.

## 3. Constitution check
- [x] P1 Spec first: tasks cite FR-37 to FR-47 and AC-39 to AC-51.
- [x] P2 Core has no framework dependencies: `DeliveryError` and the token rule are plain Python. The `503` lives only in `api/`.
- [x] P3 Abstractions at seams likely to change: no new seam. `NotificationDelivery` already protects against the change to real WebSocket push. Its contract is tightened, not widened.
- [x] P4 Open for extension, closed for modification: a real channel is another `NotificationDelivery` that raises `DeliveryError` on failure. Nothing in `core` changes.
- [x] P5 Simplest thing that meets the brief: one attempt, no retries, no queue, no live push.
- [x] P6 One command to run, one to test: unchanged.
- [x] P7 Tests prove the spec: section 6 maps all thirteen ACs.
- [x] P8 Honest scope: the channel is in memory and bounded, unreachable tokens are simulated, and the notification history is assumed to live elsewhere. All go to the README.
- [x] P9 Process is logged: decisions 16 to 18 so far.
- [x] P10 One feature at a time: no live push, no read route, nothing for 004.

## 4. Approach

### Files
```
src/notifications/core/
  errors.py         + DELIVERY_FAILED code, DeliveryError
  ports.py          NotificationDelivery.deliver(notification, token: str), contract in the docstring
  service.py        Outcome.UNDELIVERABLE, token check after the preference check
src/notifications/simulated/
  in_app_channel.py        new: InAppChannel, MAX_NOTIFICATIONS_PER_TOKEN = 100
  console_delivery.py      removed (FR-44)
  sample_users.py          + player 5 with no token, player 6 with an unreachable token
src/notifications/api/
  app.py            DeliveryError -> 503, default app uses InAppChannel
tests/
  core/test_in_app_channel.py         channel behaviour
  core/test_service_delivery.py       undeliverable, ordering, failure
  api/test_delivery_route.py          503 and undeliverable over HTTP, default app wiring
  fakes.py                            fakes typed to the new signature, a fake raising DeliveryError
  core/test_service_level_up.py       the Q15 test now expects UNDELIVERABLE (see R7)
  core/test_notification.py           error-code set gains DELIVERY_FAILED
```

### Interfaces
- `NotificationDelivery.deliver(notification, token: str) -> None`. The token is never missing or blank, because core filters those out first. On failure it raises `DeliveryError`. Returning means the notification was handed to the channel, not that the player saw it (FR-38).
- `DeliveryError(message)` in `core/errors.py`, with `code = ErrorCode.DELIVERY_FAILED`, the same shape as the other two errors so the adapter maps all three alike.
- `Outcome.UNDELIVERABLE = "undeliverable"`.
- `InAppChannel(unreachable_tokens: Iterable[str] = (), max_per_token: int = MAX_NOTIFICATIONS_PER_TOKEN)`, with `deliver(notification, token)` and `delivered_to(token) -> list[Notification]` (a copy, oldest first).

### Event flow (changes marked +)
```
handle_event(payload)
  -> validate, lookups, claim                               unchanged
     try:
       if category off: return SUPPRESSED                   unchanged, comes first (FR-42)
  +    if token is None or blank: return UNDELIVERABLE      ID stays used (FR-40, FR-41)
       build notification, delivery.deliver(notification, token)   one call, no retry (FR-37)
     except: release(event_id), re-raise                    unchanged, covers DeliveryError and anything else
  -> return PROCESSED
```

### HTTP
- `DeliveryError` from `handle_event`: `503 {"code": "DELIVERY_FAILED", "message": ...}`.
- Any other exception is not caught, so FastAPI answers `500` (spec edge case: a bug, not an unavailable channel).
- `UNDELIVERABLE`: `200 {"status": "undeliverable"}`, through the existing outcome mapping with no new code.

### Simulated channel
- A `dict[str, deque[Notification]]` with `deque(maxlen=max_per_token)`, under a `threading.Lock`. The deque drops the oldest by itself (FR-46).
- An unreachable token raises `DeliveryError` before anything is recorded (FR-47).
- Each delivery is logged the same way `ConsoleDelivery` logged it, so the uvicorn console still shows deliveries.

### How it connects
It changes only the end of 001's flow, after 002's preference check. The widened `try` from 002 already releases the ID on any failure, so no change is needed there. 004 can read `InAppChannel.delivered_to` for the demo, or add live push as another `NotificationDelivery`.

## 5. Options and decisions

| Decision | Options considered | Recommendation and why | Tradeoff accepted | Owner decision |
|---|---|---|---|---|
| Where "no token" is decided | (a) core, before delivery, (b) the delivery implementation reports it | (a). It decides the outcome and the ID (FR-40, FR-41), which are core rules. Every future channel then gets the same behaviour. | Core knows a token can be missing, which it already does from `UserRecord`. | (a) (owner) |
| Token type in the delivery contract | (a) `str` only, (b) keep `str \| None` | (a). Core filters missing and blank tokens, so the contract can promise a real token and channels need no `None` handling. | A change to a `core` interface, so that task runs in plan mode. | (a) (owner, with the decision above) |
| How failure is signalled | (a) a `DeliveryError` that channels raise, other exceptions stay `500`, (b) core wraps any exception from `deliver` into `DeliveryError` | (a). Matches the spec edge case: only a known channel failure means "retry later", while a bug should look like a bug. | A channel that raises something else gives the producer a `500`, not a `503`. The ID is still released. | (a) (owner) |
| Sample users for the hand run and demo | (a) add player 5 with no token and player 6 with an unreachable token, (b) change existing players 1 to 4 | (a). Players 1 to 3 are used by the brief's examples and 001's tests, so they stay as they are. | Two more seed users. | (a) (owner) |
| The logging placeholder | (a) remove `ConsoleDelivery`, the channel logs, (b) keep it beside the channel | (a). FR-44 says the channel replaces it, and the logging moves into the channel. | none | (a) (owner) |
| Where the limit constant lives | (a) `MAX_NOTIFICATIONS_PER_TOKEN` in `simulated/in_app_channel.py`, (b) a config module or environment variable | (a). The limit belongs to the simulated channel, and a config layer is not needed yet (P5). | Changing it means a code edit. | (a) (owner) |

## 6. Testing strategy

| AC | Test |
|---|---|
| AC-39 | Service with a real `InAppChannel`: a Level Up for player 1 leaves exactly that notification under `token-1`. |
| AC-40 | Channel unit test: two notifications to one token, one to another, each read back in order. |
| AC-41, AC-49 | Directory with a `None` token and a blank token: `UNDELIVERABLE`, recording fake has no calls. |
| AC-42 | Undeliverable, then the same ID with the player given a token (a second directory over the same store): `DUPLICATE`, no call. |
| AC-43 | No token and category off: `SUPPRESSED`. |
| AC-44 | Fake raising `DeliveryError` once: the error reaches the caller, the resend is `PROCESSED` with one delivery. |
| AC-45, AC-46 | `TestClient`: `503 DELIVERY_FAILED`, and `200 {"status": "undeliverable"}`. |
| AC-47 | `build_default_app()`: posting a Level Up for player 1 leaves it in the app's channel. Also player 6 gives `503` and player 5 gives `undeliverable`. |
| AC-48 | A counting fake that raises: exactly one call, no retry. |
| AC-50 | Channel with `max_per_token=3`: the fourth delivery drops the first, other tokens untouched. Also asserts the default equals `MAX_NOTIFICATIONS_PER_TOKEN`. |
| AC-51 | Channel built with `token-x` unreachable: `DeliveryError`, nothing recorded, other tokens still delivered. |

## 7. Risks and open questions
- R7: 001's Q15 test, `test_an_event_with_no_directory_token_is_still_delivered`, asserts that delivery receives `None`. Feature 003 deliberately changes that behaviour (Q15 left it to 003), so the test is rewritten to expect `UNDELIVERABLE`. It is the one 001 test whose expectation changes. `test_error_codes` also gains `DELIVERY_FAILED`.
- R8: the task that changes `NotificationDelivery` touches a `core` interface and more than three files, so it runs in plan mode first, as CLAUDE.md requires.
- R9: a test that needs the default app's channel has to reach it. Decided (owner): `build_default_app` keeps the channel on `app.state.channel`, a small hook in the adapter with no rule in it. A read route stays with 004.

## 8. Complexity tracking
None.

## 9. Extension notes
Live push in 004 is another `NotificationDelivery` (WebSocket or SSE) that raises `DeliveryError` when the client is gone. A real retry policy, if ever wanted, would wrap a channel as a decorator implementing the same interface, with no change in core.
