from notifications.core.ports import UserRecord

SAMPLE_USERS = [
    UserRecord(1, "Alice", "token-1"),
    UserRecord(2, "Bob", "token-2"),
    UserRecord(3, "Carol", "token-3"),
    UserRecord(4, "Dave", "token-4"),
    UserRecord(5, "Eve", None),  # never connected: events for Eve are undeliverable
    UserRecord(6, "Frank", "token-6"),  # connected, but the channel is down (see UNREACHABLE_TOKENS)
]

# Tokens the simulated channel cannot reach, so the 503 path can be shown by hand.
UNREACHABLE_TOKENS = {"token-6"}
