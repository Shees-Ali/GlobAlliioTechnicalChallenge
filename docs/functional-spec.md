# Initial Functional Specification: Gaming Notifications

Status: Draft for discussion

## 1. Purpose

The notification module receives events originating from the game platform, determines the appropriate notification and recipient, checks user preferences, and triggers in-app delivery.

## 2. System boundary and assumptions

### Upstream event production and transport

**Proposed assumption:** Game and social backend components are responsible for confirming that an action occurred and emitting the corresponding event.

For example, the game backend determines that a player has reached level 15 before emitting a Level Up event. The notification module does not calculate player progression, award items, complete achievements, or manage social relationships.

In a deployed platform, events could reach the notification module through an event bus, message broker such as RabbitMQ, or another integration mechanism. The challenge does not prescribe a transport.

**Exercise scope:** Upstream transport infrastructure and its receiving adapters are not implemented. Simulated game and social components submit events to the notification module’s event-handling entry point.

The module’s responsibility begins when an event is submitted to that entry point. Receiving the submitted event and passing it into notification processing remain part of the implementation.

### Downstream notification delivery

The game client is assumed to have an existing mechanism for receiving and displaying in-app notifications.

**Proposed environment assumption:** That existing mechanism may use WebSocket connections.

For this exercise, delivery is represented by a simulated external dependency. The module invokes it with the notification and intended recipient. WebSocket connection management and client rendering are outside the initial scope.

### Demonstrated flow

Simulated game/social component  
→ notification module receives event  
→ determines recipient and category  
→ checks recipient preferences  
→ creates notification  
→ invokes simulated in-app delivery

No message broker or active game client is required to run the demonstration.

## 3. Required events

| Category | Event | Trigger | Recipient | Content includes |
|---|---|---|---|---|
| Game Events | Level Up | Player reaches a new level | That player | New level |
| Game Events | Item Acquired | Player obtains a rare or valuable item | That player | Item name |
| Game Events | Challenge Completed | Player completes a challenging quest or achievement | That player | Quest or achievement name |
| Social Events | Friend Request | Player sends another player a request | Request recipient | Requester’s display name |
| Social Events | Friend Accepted | Player accepts a friend request | Original requester | Accepting player’s display name |
| Social Events | New Follower | Player follows another player | Followed player | Follower’s display name |

PvP notifications are optional and excluded from the initial scope.

**Proposed interpretations and assumptions:**

- Friend Accepted notifies the original requester.
- Upstream game logic determines which items and challenges qualify for notification.
- Event details needed to construct meaningful content are available to the module. Their representation will be defined in the technical specification.

## 4. Notification content and channel

Only in-app notifications are required.

Messages must clearly describe the event and contain relevant details. For example:

- “Congratulations! You’ve reached level 15!”
- “You’ve acquired the legendary Sword of Azeroth!”
- “Player ‘Alex’ has sent you a friend request.”

Exact wording is flexible; recipient accuracy and informative content are required.

Invoking delivery does not establish that the player received, displayed, or read the notification.

## 5. User preferences

Each user can independently enable or disable Game Events and Social Events.

The module checks the intended recipient’s preference for the event’s category:

- Enabled: create the notification and invoke delivery.
- Disabled: suppress the notification without invoking delivery.

**Proposed defaults:**

- Both categories are enabled when no preference is recorded.
- Preferences are evaluated when the event is processed.
- Changing one category or user’s preferences does not affect others.
- Re-enabling a category does not replay previously suppressed notifications.

## 6. Real-time behavior

Processing begins when an event is submitted to the module, without intentional batching or scheduled delay.

The exercise specifies no numerical latency target. Broker behavior, offline delivery, retries, ordering, and duplicate-event handling are deferred to technical decisions.

## 7. Acceptance scenarios

1. Simulated game and social producers submit events through the module’s entry point and trigger the complete notification flow.
2. All six required event types produce the correct recipient and meaningful content.
3. A friend request from user 3 to user 1 notifies user 1 about user 3.
4. When user 1 accepts user 3’s request, user 3 is notified about user 1.
5. Disabling a category prevents its notifications from reaching the delivery dependency.
6. Other categories and users remain unaffected.
7. Missing preferences follow the documented defaults.
8. Preference changes affect subsequent processing without replaying suppressed events.
9. The demonstration runs without RabbitMQ, WebSocket infrastructure, or a game client.

## 8. Technical decisions deferred

Event contracts, validation, component interfaces, preference storage, error behavior, and the demonstration interface will be defined in the technical specification.
