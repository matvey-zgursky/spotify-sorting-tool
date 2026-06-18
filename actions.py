from enum import Enum


class UserAction(Enum):
    """Действия, которые может запустить приложение."""

    TRANSFER_LIKED_TRACKS = "transfer_liked_tracks"
