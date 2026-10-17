# Plan: Feature 001 Event intake and dispatch

Implements: [spec.md](spec.md)
Status: Reviewed by owner (decisions in section 5; two marked as assumptions)

## 1. Summary
Build a framework-free core with one entry point, `handle_event(payload)`. It validates the raw event, looks up the players in a user directory, builds a `Notification` and calls the delivery dependency once, all synchronously. Each of the six event types is one declarative definition in a registry, so adding an event type means adding one definition. The user directory and the delivery dependency are the two seams, each a small interface with a simulated in-memory implementation. FastAPI is the project framework and sits in a thin `api` adapter that exposes the core over HTTP (`POST /events`). Because the core never imports FastAPI, a WebSocket or broker intake later is another adapter calling the same `handle_event`. This feature also sets up the project baseline (language, layout, test command).

## 2. Technical context
- Language and framework: Python 3.12 with FastAPI (owner decision: the module is FastAPI-based so that WebSocket or other intake mechanisms can be added later). The core stays framework-free and FastAPI lives only in the `api` adapter.
- New dependencies: runtime `fastapi` and `uvicorn` (the app and the server to run it); dev `pytest` and `httpx` (test runner, and the client FastAPI's `TestClient` needs). Needs owner approval (CLAUDE.md asks before adding any dependency).
- Storage: none. The user directory is an in-memory simulated dependency.
- Testing approach: unit tests against the core with a fake delivery and an in-memory directory, no server (P2). A few API tests through `TestClient` for the HTTP adapter only.
- Constraints from the brief and base spec: in-app only, delivery is simulated, no broker or WebSocket, must run from a fresh clone with a documented command.

## 3. Constitution check
- [x] P1 Spec first: every task cites FR and AC IDs from the reviewed spec.
- [x] P2 Core has no framework dependencies: `core` does not import FastAPI, Starlette or Pydantic. FastAPI is confined to `api/`. An architecture test enforces it (see risk R1).
- [x] P3 Abstractions at seams likely to change: only two interfaces. `UserDirectory` (becomes a real user service) and `NotificationDelivery` (becomes WebSocket delivery). Nothing else is abstracted.
- [x] P4 Open for extension, closed for modification: a new event type is a new entry in the registry. The service, validation and delivery code do not change.
- [x] P5 Simplest thing that meets the brief: synchronous, no queue, no persistence, no notification IDs or timestamps (not in the spec).
- [x] P6 One command to run, one to test: `uvicorn notifications.api.app:app` to run, `pytest` to test, after `pip install -e ".[dev]"`. Recorded under Commands in AGENTS.md when the first task is done.
- [x] P7 Tests prove the spec: section 6 maps all 17 ACs to tests.
- [x] P8 Honest scope: the README limitations list gets "synchronous, in-memory, no retries or dedup" (written at packaging).
- [x] P9 Process is logged: decisions in section 5 go to `docs/ai-process/README.md` after the owner decides.
- [x] P10 One feature at a time: nothing is built for 002 to 004 beyond the two interfaces this feature itself needs.

## 4. Approach

### Files
```
pyproject.toml                       project metadata, pytest config
src/notifications/
  __init__.py
  core/
    errors.py          InvalidEventError with a reason code
    notification.py    Category enum, Notification (frozen dataclass)
    ports.py           UserDirectory and NotificationDelivery interfaces, UserRecord
    formatting.py      readable_name("SwordOfAzeroth") -> "Sword Of Azeroth"
    validation.py      FieldSpec kinds and the payload validator
    events.py          EventDefinition and the registry of six definitions
    service.py         NotificationService.handle_event(payload)
  simulated/
    in_memory_directory.py   dict-backed UserDirectory for tests and the demo
  api/
    app.py             FastAPI app factory and POST /events route (thin adapter)
tests/
  core/                one test module per core module
  api/                 TestClient tests for the route
  test_architecture.py core imports no web framework
```
`simulated/` holds stand-ins for external systems. The simulated delivery implementation is feature 003, so tests here use a recording fake. `api/` only translates HTTP to `handle_event` and `InvalidEventError` to a response. It holds no rules.

### HTTP adapter (proposed)
- `POST /events` takes a JSON object and passes it to `handle_event` unchanged. The body is read as a plain dict, not a Pydantic model, so the module's own validation (FR-15) produces the errors and not FastAPI's.
- Accepted event: `200` with `{"status": "processed"}`. Delivery has been invoked by then (FR-2, AC-8).
- Invalid event: `422` with `{"code": "...", "message": "..."}` from `InvalidEventError`. A body that is not a JSON object is also rejected as invalid.
- The app is built by a factory that takes the service, so tests and the demo inject their own directory and delivery.

### Event contract (raw payload, proposed)
The entry point takes a plain mapping, as a broker message would arrive. `type` selects the definition.

| type | fields | recipient | actor (name looked up) |
|---|---|---|---|
| `level_up` | `player_id`, `new_level` | `player_id` | none |
| `item_acquired` | `player_id`, `item_name` | `player_id` | none |
| `challenge_completed` | `player_id`, `challenge_name` | `player_id` | none |
| `friend_request` | `requester_id`, `recipient_id` | `recipient_id` | `requester_id` |
| `friend_accepted` | `accepter_id`, `requester_id` | `requester_id` | `accepter_id` |
| `new_follower` | `follower_id`, `followed_id` | `followed_id` | `follower_id` |

IDs must be positive integers (not booleans). `new_level` must be a positive integer. Names must be non-blank strings. Extra fields are rejected (see Validation).

### Validation (decided: declarative field specs in core)
Each `EventDefinition` lists `FieldSpec`s (name, kind, optional max length). One validator in `core` checks every payload against its definition, with no third-party library:
- the payload is a mapping and `type` is a known string (else `UNSUPPORTED_EVENT_TYPE`);
- every declared field is present (else `MISSING_FIELD`);
- each value has the strict kind: `PlayerId` is an int above 0 and not a bool, `PositiveInt` likewise, `NonEmptyText` is a non-blank string within the length limit, with no coercion of `"15"` to `15` (else `MALFORMED_FIELD`);
- no field outside the definition is present (else `MALFORMED_FIELD`).
The validator lives in `core/validation.py`. Adding an event type adds no validation code.

### Intake neutrality
The core knows nothing about how events arrive.
- `handle_event` takes a plain mapping and either returns or raises `InvalidEventError`. There are no request objects, status codes or framing in `core`.
- `InvalidEventError` carries a reason code and message, never an HTTP status. The `api` adapter maps it to `422`. A WebSocket adapter would map it to an error frame, and a RabbitMQ consumer to a reject or dead-letter, each in its own adapter.
- Every adapter does the same three things: decode the transport into a mapping, call `handle_event`, translate the result or error back. Adding one needs no change in `core`.

### Interfaces
- `UserDirectory.get(player_id) -> UserRecord | None`. `UserRecord` holds `player_id`, `display_name`, `delivery_token`.
- `NotificationDelivery.deliver(notification, token)`. The contract beyond this signature is feature 003.
- `NotificationService(directory, delivery)` is built with both and exposes `handle_event(payload)`.

### Data flow
```
handle_event(payload)
  -> definition = registry[payload["type"]]          else UNSUPPORTED_EVENT_TYPE
  -> check the payload against the definition's FieldSpecs   else MISSING_FIELD / MALFORMED_FIELD
  -> reject if actor id == recipient id              else SELF_TARGETED
  -> recipient = directory.get(recipient id)         else UNKNOWN_PLAYER
  -> actor = directory.get(actor id) if the type has one   else UNKNOWN_PLAYER
  -> message = definition.build_message(fields, actor name)
  -> notification = Notification(recipient id, category, type, message)
  -> delivery.deliver(notification, recipient.delivery_token)
```
Any failure raises `InvalidEventError(code, message)` before step 1 of delivery, so a rejected event never reaches delivery (FR-15). The error is what the submitting component gets back: raised in-process, and a `422` body over HTTP.

### How it connects
It is the baseline, so nothing exists beneath it. Features 002 to 004 add to it: 002 inserts a preference check before the notification is created, 003 replaces the recording fake with the simulated delivery, 004 adds the demo page and simulated producers on top of the `api` adapter.

## 5. Options and decisions

| Decision | Options considered | Recommendation and why | Tradeoff accepted | Owner decision |
|---|---|---|---|---|
| Language and framework | Python, TypeScript on Node, Java | Python 3.12 with FastAPI: least boilerplate, fast to read in an interview, pytest is simple. | Weaker static typing than Java or TypeScript, mitigated with type hints. | Python with FastAPI (owner). Reason: WebSocket or other intake mechanisms can be added later. |
| FastAPI in this feature | (a) core only, API in feature 004, (b) core plus a thin `POST /events` adapter now | (b). Proves the core-versus-framework seam from the start, makes "reject and tell the sender" (FR-15) real over HTTP, and 004 then only adds the demo on top. | Slightly more in 001: one route, about 10 lines, and two API tests. | (b) (assumed from the owner's "right now it's going to be FastAPI", to be confirmed) |
| Entry point input | (a) raw mapping validated by the module, (b) typed event objects built by producers | (a). The spec requires rejecting unsupported types and missing fields, which only makes sense for raw input, and it mimics a broker message. | Producers are not guided by types. A typed builder can be added in the demo. | Recommendation accepted (owner asked for tasks without objecting) |
| Where event rules live | (a) one registry of declarative definitions, (b) an if/else or match in the service, (c) one class per event type | (a). Meets P4 with the least code: category, fields, recipient, actor and message in one place. | Message templates are code, not translatable text. Fine for this scope. | Recommendation accepted (owner asked for tasks without objecting) |
| Rejection style | (a) raise `InvalidEventError` with a reason code, (b) return a result object | (a). Simple for in-process callers, and the code maps cleanly to an HTTP 4xx later. | Callers must catch. | Recommendation accepted (owner asked for tasks without objecting) |
| Sync or async | (a) synchronous, (b) async/queue | (a). AC-8 requires delivery to be invoked before the entry point returns, and no broker is in scope. | No back-pressure or retries. Stated in the README. | Recommendation accepted (owner asked for tasks without objecting) |
| In-memory directory in this feature | (a) include it now, (b) tests use ad-hoc fakes only | (a). Feature 004 needs it anyway and tests share one helper. It is a tiny dict wrapper. | Slight early work for 004. | Recommendation accepted (owner asked for tasks without objecting) |
| Name formatting | (a) regex splitting before capitals, only when the name has no spaces, (b) lookup table | (a). Matches FR-17 and Q14, about three lines. | Odd names such as acronyms ("XPBoost") split imperfectly. | Recommendation accepted (owner asked for tasks without objecting) |
| Event field naming | Names in the contract table above, or alternatives | Table above: the role is in the name, so a request and an acceptance cannot be confused. | None significant. | Recommendation accepted (owner asked for tasks without objecting) |
| Payload validation | (a) declarative `FieldSpec` in core, (b) Pydantic models in core, (c) Pydantic in `api/` only | (a). Own reason codes map onto AC-13, the core stays library-free and every future intake shares the same checks. | About 40 lines of validation code to maintain. | (a) (owner) |
| Unknown extra fields | (a) reject, (b) ignore | (a). Stricter, and fits the owner's concern about forged or malicious senders. | A producer that adds a field later is rejected until the definition is updated. | Reject (assumed, to be confirmed) |

## 6. Testing strategy
All AC tests are unit tests on the core using a recording fake delivery and an in-memory directory. The API tests below add HTTP coverage of AC-8 and AC-13 only if the owner accepts the adapter in 001.

| AC | Test |
|---|---|
| AC-1 to AC-6 | One test per event type. Assert one delivery call, the recipient, the category and that the message contains the detail. |
| AC-7 | Parametrised over all six types: message is non-empty. |
| AC-8 | The fake delivery has already recorded the call when `handle_event` returns. |
| AC-9 | Item and challenge events with arbitrary names are all delivered. |
| AC-10 | Two events in a row produce two calls, each with only its own data. |
| AC-11, AC-12 | Fake directory records lookups. Assert the actor's name appears in the message, and that game events look up only the recipient. |
| AC-13 | Parametrised: unsupported type, each missing field, malformed values. Assert the error code and zero delivery calls. |
| AC-14 | Self-targeted friend request, friend accepted and follow are rejected. |
| AC-15 | Unknown recipient and unknown actor are rejected, for game and social events. |
| AC-16 | `SwordOfAzeroth` becomes "Sword Of Azeroth". A name with spaces is unchanged. |
| AC-17 | The fake delivery receives the recipient's token. |
| AC-8, AC-13 (HTTP) | `TestClient`: a valid `POST /events` returns 200 and the fake delivery has been called. An invalid body returns 422 with the reason code and no delivery call. |

## 7. Risks and open questions
- R1: CLAUDE.md says "the architecture test (AC-15) passes", but no spec defines an architecture test, and AC-15 in this feature is the unknown-player case. The ID collides. My proposal: this feature gets a plain `test_architecture.py` (modules under `core` import no web framework: fastapi, starlette, pydantic, uvicorn) without an AC number, because it serves P2, and CLAUDE.md is corrected to say "the architecture test" once you agree. I did not edit CLAUDE.md. Your call.
- R2: the event field names are my proposal. If the real producers (the brief's `gameEngine.playerLeveledUp(1, 15)` style calls) are meant to map one to one onto method names, the demo feature will adapt them. No effect on the core.
- R3: a missing `delivery_token` (Q15) is passed through as `None`. Feature 003 defines what delivery does with it.
- Open questions for the owner: the pending decisions in section 5, and R1.

## 8. Complexity tracking
None.

## 9. Extension notes
A new event type is a new registry entry plus tests. A new intake (WebSocket, RabbitMQ) is a new adapter beside `api/` that calls `handle_event`. A new channel would be a second `NotificationDelivery`, which is a question for a later feature.
