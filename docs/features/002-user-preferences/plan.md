# Plan: Feature 002 User preferences

Implements: [spec.md](spec.md)
Status: Implemented, awaiting owner review before commit

## 1. Summary
Add a fourth seam, `PreferenceStore`, that holds each player's recorded category settings as a simple map, with an in-memory implementation. `handle_event` checks the recipient's setting after it claims the event ID and before it builds the notification, and returns a new `Outcome.SUPPRESSED` when the category is off. A small `PreferenceService` in `core` validates and applies changes from a raw mapping, the same way `handle_event` takes a raw event, and a thin `PUT /preferences` route exposes it over HTTP. The default-on rule lives in `core`, so no store has to reimplement it.

## 2. Technical context
- Language and framework: unchanged (Python 3.12, FastAPI in `api/` only).
- New dependencies: none.
- Storage: in memory, lost on restart (spec edge case, README at packaging).
- Testing approach: unit tests on the core with the recording delivery and an in-memory store, `TestClient` tests for the route, one end-to-end HTTP test for AC-38.
- Constraints from the brief and base spec: preferences "representable by a simple map", per category only (Q5), functional spec section 5 and scenarios 5 to 8.

## 3. Constitution check
- [x] P1 Spec first: every task cites FR-26 to FR-36 and AC-27 to AC-38.
- [x] P2 Core has no framework dependencies: the store interface and `PreferenceService` are plain Python. The route only decodes JSON and maps errors. The architecture test covers the new core files.
- [x] P3 Abstractions at seams likely to change: one new seam, `PreferenceStore`. The change it protects against: preferences move to a persistent, shared store (a database or a profile service), because in memory they are lost on restart and not shared across processes.
- [x] P4 Open for extension, closed for modification: a new category is a new `Category` value. It is on for everyone by default (FR-28) with no change to the store, the check or the route.
- [x] P5 Simplest thing that meets the brief: one category per change, no read route (Q20), no history, no queue of suppressed notifications.
- [x] P6 One command to run, one to test: unchanged.
- [x] P7 Tests prove the spec: section 6 maps all twelve ACs.
- [x] P8 Honest scope: in-memory preferences and the unauthenticated route go into the README limitations.
- [x] P9 Process is logged: decisions 12 to 14 in `docs/ai-process/README.md`.
- [x] P10 One feature at a time: nothing for 003 or 004. The delivery contract and the demo stay untouched.

## 4. Approach

### Files
```
src/notifications/core/
  ports.py          + PreferenceStore protocol
  errors.py         + UNSUPPORTED_CATEGORY code, InvalidPreferenceError
  preferences.py    new: is_enabled() default-on rule, PreferenceService.change(payload)
  service.py        constructor takes the store, Outcome.SUPPRESSED, the check
src/notifications/simulated/
  in_memory_preferences.py   new: dict of player -> {category: bool} under a lock
src/notifications/api/
  app.py            create_app(service, preference_service), PUT /preferences, default wiring
tests/
  conftest.py       + preferences and preference_service fixtures, service gets the store
  core/test_preferences.py              change validation, default rule
  core/test_service_preferences.py      suppression, independence, event IDs
  core/test_in_memory_preferences.py    store behaviour
  api/test_preferences_route.py         route and the end-to-end AC-38 test
  (five existing direct NotificationService(...) calls gain the store argument)
```

### Interfaces
- `PreferenceStore.get(player_id) -> Mapping[Category, bool]` returns only what is recorded, possibly empty. `PreferenceStore.set(player_id, category, enabled) -> None`.
- `is_enabled(store, player_id, category) -> bool` is `store.get(player_id).get(category, True)`. This is the only place the default lives (FR-28).
- `PreferenceService(directory, store).change(payload)` takes `{"player_id": 1, "category": "game", "enabled": false}`. It raises `InvalidPreferenceError(code, message)` or returns `None`.
- `NotificationService(directory, delivery, processed_events, preferences)` (this changes the constructor, a `core` interface). `Outcome` gains `SUPPRESSED = "suppressed"`.

### Event flow (changes marked +)
```
handle_event(payload)
  -> validate, self-target check, recipient and actor lookups      unchanged, still first (FR-31)
  -> processed_events.claim(event_id)          if already claimed: return DUPLICATE
     try:
  +    if not is_enabled(store, recipient, category): return SUPPRESSED   ID stays used (FR-32)
  +    notification = Notification(...)          now built after the check, as in the functional spec flow
       delivery.deliver(notification, token)
     except: release(event_id), re-raise
  -> return PROCESSED
```
The claim comes before the check so that a duplicate always wins over suppression (spec edge case) and a suppressed event uses up its ID. The `try` now covers everything after the claim, so a failing preference read releases the ID just as a failing delivery does. Today only `deliver` is inside it.

### Change flow
```
PreferenceService.change(payload)
  -> payload is a mapping                      else MALFORMED_FIELD
  -> player_id, category, enabled present      else MISSING_FIELD
  -> no other keys                             else MALFORMED_FIELD
  -> player_id is a PlayerId                   else MALFORMED_FIELD
  -> category is a Category value ("game", "social")   else UNSUPPORTED_CATEGORY
  -> enabled is a bool (not 0 or 1)            else MALFORMED_FIELD
  -> directory.get(player_id) exists           else UNKNOWN_PLAYER
  -> store.set(player_id, category, enabled)
```
Every check runs before `set`, so a rejected change writes nothing (FR-34). The order (shape first, lookup last) matches events. It reuses `PlayerId` from `validation.py`.

### HTTP
- `PUT /preferences` with the body above. `200 {"status": "updated"}` on success. `422 {"code", "message"}` on rejection, the same shape as `/events`.
- `POST /events` returns `{"status": "suppressed"}` for the new outcome (AC-32) with no other change.
- The default app builds one `InMemoryPreferenceStore` and passes it to both services, so a change made over HTTP applies to the next posted event (AC-38).

### How it connects
It builds on 001's service, directory and event-ID store. 003 is untouched: delivery still raises to signal failure, which the widened `try` relies on. 004 can add a read route or a toggle on the demo page on top of `PreferenceService`.

## 5. Options and decisions

| Decision | Options considered | Recommendation and why | Tradeoff accepted | Owner decision |
|---|---|---|---|---|
| Where preferences are stored | (a) new `PreferenceStore` seam, (b) a field on `UserRecord` in the directory, (c) a plain dict passed to the service | (a). Preferences are written at runtime, while the directory is a read-only stand-in for the user service. A real platform would likely keep settings in their own table or service. | A fourth interface. | (a) (owner) |
| Store shape and where the default lives | (a) store returns the recorded map, core applies default on, (b) store answers `is_enabled` and applies the default itself | (a). It matches "a simple map" in the brief, and the default (FR-28) is a rule, so it belongs in core, written once. A database store then cannot get it wrong. | Callers go through `is_enabled`, not the store directly. | (a) (owner): "by default all notifications would be on" |
| Where change rules live | (a) separate `PreferenceService` in core taking a raw mapping, (b) a method on `NotificationService`, (c) the route validates and core takes typed values | (a). The route stays rule-free (FR-35), any future adapter shares the checks, and `NotificationService` keeps one job. | Two services to wire in the app. | (a) (owner) |
| Route shape | (a) `PUT /preferences` with player, category and value in the JSON body, (b) `PUT /players/{id}/preferences/{category}` with `{"enabled": false}`, (c) `PATCH /players/{id}/preferences` with a partial map | (a). All input is raw JSON that core validates, with the same error shape as `/events`. In (b), FastAPI parses the path, so a bad ID gets FastAPI's error format, or the adapter has to convert it (a rule in the adapter). (c) changes several categories at once, which FR-33 does not need. | Less RESTful URL. Easy to defend: it mirrors `POST /events`. | (a) (owner) |
| Error type for rejected changes | (a) new `InvalidPreferenceError` beside `InvalidEventError`, sharing `ErrorCode`, (b) reuse `InvalidEventError`, (c) rename to a shared base | (a). The names stay accurate and nothing in 001 changes. The adapter catches both. | Two near-identical classes. A shared base can come later if a third appears. | (a) (owner) |
| Order of the check and the claim | (a) claim, then check, (b) check, then claim | (a). Required by FR-32 and the duplicate-wins edge case. Listed so the reason is visible, not a real choice. | none | Follows from the spec |
| Constructor change | (a) store is a required argument, (b) optional, defaulting to "all on" | (a). Explicit wiring, and core would otherwise need a default store, which belongs in `simulated/`. | Five test call sites and the app change. | (a) (owner) |

## 6. Testing strategy

| AC | Test |
|---|---|
| AC-27 | Store has Game off for player 1: Level Up returns `SUPPRESSED`, zero delivery calls. |
| AC-28 | Same store: a Friend Request to player 1 is delivered. |
| AC-29 | Empty store: one event of each type for player 1, six deliveries. Parametrised over the registry so a new type is covered too. |
| AC-30 | Game off for player 1: Level Up for player 2 is delivered. |
| AC-31 | Social off for user 3 only: Friend Request from 3 to 1 is delivered to 1. |
| AC-32 | `TestClient`: suppressed event returns `200 {"status": "suppressed"}`. |
| AC-33 | Category off: missing `new_level` and an unknown requester both raise `InvalidEventError` with their codes, and the outcome is never `SUPPRESSED`. |
| AC-34 | Suppress, enable, resend same ID: `DUPLICATE`, zero deliveries. |
| AC-35 | Suppress, enable: still zero deliveries. New ID: exactly one delivery, for the new event. |
| AC-36 | Game off, Social off then on: Game still off. |
| AC-37 | Parametrised: unknown player, unsupported category, `enabled` as `1` or `"false"`, missing field, extra field, not an object. Each gives its code and the store is unchanged. |
| AC-38 | `TestClient` on one app: `PUT /preferences` turns Game off, then `POST /events` Level Up returns suppressed with no delivery. |
| (FR-32 safety) | A store whose `get` raises: the error reaches the caller and the ID is released. Not an AC, it guards the widened `try`. |

## 7. Risks and open questions
- R5: changing the `NotificationService` constructor touches more than three files and a `core` interface, so that task runs in plan mode first, as CLAUDE.md requires.
- R6: a preference change is visible to the next event because both services share one store object. A store that caches would break FR-33. Noted for any future store.

## 8. Complexity tracking
None.

## 9. Extension notes
Per-type preferences would extend the map key from category to (category, type), with the default rule still in `is_enabled`. A persistent store is another `PreferenceStore`. A read route for the demo (004) is one call to `store.get` through `is_enabled` for each category.
