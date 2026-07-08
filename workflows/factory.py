import logging
from collections.abc import Callable
from typing import Protocol

from workflows.actions import UserAction
from api.client import SpotifyClient
from api.types import SpotifyUser
from liked_tracks.reader import SpotifyLikedTracksReader
from liked_tracks.operations import LikedTracksDeleter, LikedTracksFinder
from liked_tracks.remover import SpotifyLikedTracksRemover
from playlist_manager import SpotifyPlaylistManager
from playlist_selection import TargetPlaylistSelector
from playlist_track_adder import PlaylistTrackAdder
from ui import UserInterface
from workflows.delete_liked_tracks import DeleteLikedTracksWorkflow
from workflows.transfer_liked_tracks import TransferLikedTracksWorkflow

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

        workflow_creators: dict[UserAction, Callable[[], Workflow]] = {
            UserAction.TRANSFER_LIKED_TRACKS: self._create_transfer_workflow,
            UserAction.DELETE_LIKED_TRACKS: self._create_delete_workflow,
        }

        try:
            workflow = workflow_creators[action]()
        except KeyError:
            logger.error(
                "Unsupported workflow action requested: action=%s",
                action_value,
            )
            raise ValueError(f"Unsupported user action: {action_value}") from None

        logger.debug(
            "Workflow created: action=%s workflow=%s",
            action_value,
            workflow.__class__.__name__,
        )
        return workflow

    def _create_transfer_workflow(self) -> TransferLikedTracksWorkflow:
        """Создать сценарий переноса любимых треков."""
        playlist_manager = SpotifyPlaylistManager(self.spotify, self.user["id"])

        return TransferLikedTracksWorkflow(
            self.ui,
            TargetPlaylistSelector(playlist_manager, self.ui),
            LikedTracksFinder(self.ui, SpotifyLikedTracksReader(self.spotify)),
            PlaylistTrackAdder(self.spotify),
            LikedTracksDeleter(self.ui, SpotifyLikedTracksRemover(self.spotify)),
        )

    def _create_delete_workflow(self) -> DeleteLikedTracksWorkflow:
        """Создать сценарий удаления любимых треков."""
        return DeleteLikedTracksWorkflow(
            self.ui,
            LikedTracksFinder(self.ui, SpotifyLikedTracksReader(self.spotify)),
            LikedTracksDeleter(self.ui, SpotifyLikedTracksRemover(self.spotify)),
        )
