"""Transport-independent message types."""
from __future__ import annotations

from dataclasses import dataclass

Keyboard = tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class Incoming:
    chat_id: int
    user_id: int
    text: str | None  # None for non-text (photo, sticker...)
    first_name: str = ""
    username: str = ""
    chat_type: str = "private"


@dataclass(frozen=True)
class Outgoing:
    chat_id: int
    text: str
    keyboard: Keyboard | None = None  # reply keyboard; None = leave unchanged
    remove_keyboard: bool = False
