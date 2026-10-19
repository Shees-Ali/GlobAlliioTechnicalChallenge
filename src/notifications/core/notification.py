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
