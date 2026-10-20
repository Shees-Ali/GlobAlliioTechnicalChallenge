from dataclasses import dataclass
from enum import Enum


class Category(str, Enum):
    GAME = "game"
    SOCIAL = "social"


@dataclass(frozen=True)
class Notification:
    recipient_id: int
    category: Category
    event_type: str
    message: str
    event_id: str  # the event that produced it, so a receiver can drop a repeat (FR-64)
