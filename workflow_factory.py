import logging
from typing import Protocol

from actions import UserAction
from api.types import SpotifyUser
from liked_tracks import LikedTracks
from playlist import PlaylistManager, PlaylistTrackAdder, TargetPlaylistSelector
from api.client import SpotifyClient
from transfer import TransferLikedTracksWorkflow
from ui import UserInterface

logger = logging.getLogger(__name__)


class Workflow(Protocol):
    """Сценарий приложения."""

    def run(self) -> None:
        """Запустить сценарий."""


class WorkflowFactory:
    """Создает сценарии приложения по выбранному действию."""

    def __init__(
        self,
        spotify: SpotifyClient,
        user: SpotifyUser,
        ui: UserInterface,
    ) -> None:
        self.spotify = spotify
        self.user = user
        self.ui = ui

    def create(self, action: UserAction) -> Workflow:
        """Создать сценарий для выбранного действия."""
        action_value = action.value
        logger.debug("Workflow creation requested: action=%s", action_value)

        if action == UserAction.TRANSFER_LIKED_TRACKS:
            playlist_manager = PlaylistManager(self.spotify, self.user["id"])
            playlist_selector = TargetPlaylistSelector(
                playlist_manager,
                self.ui,
            )
            liked_tracks = LikedTracks(self.spotify)
            track_adder = PlaylistTrackAdder(self.spotify)
            workflow = TransferLikedTracksWorkflow(
                self.ui,
                playlist_selector,
                liked_tracks,
                track_adder,
            )
            logger.debug(
                "Workflow created: action=%s workflow=%s",
                action_value,
                workflow.__class__.__name__,
            )
            return workflow

        logger.error("Unsupported workflow action requested: action=%s", action_value)
        raise ValueError(f"Unsupported user action: {action_value}")
