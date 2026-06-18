from typing import Protocol

import spotipy

from actions import UserAction
from liked_tracks import LikedTracks
from playlist import PlaylistManager, PlaylistTrackAdder, TargetPlaylistSelector
from transfer import TransferLikedTracksWorkflow
from user_interface import UserInterface


class Workflow(Protocol):
    """Сценарий приложения."""

    def run(self) -> None:
        """Запустить сценарий."""


class WorkflowFactory:
    """Создает сценарии приложения по выбранному действию."""

    def __init__(
        self,
        spotify: spotipy.Spotify,
        user: dict,
        ui: UserInterface,
    ) -> None:
        self.spotify = spotify
        self.user = user
        self.ui = ui

    def create(self, action: UserAction) -> Workflow:
        """Создать сценарий для выбранного действия."""
        if action == UserAction.TRANSFER_LIKED_TRACKS:
            playlist_manager = PlaylistManager(self.spotify, self.user["id"])
            playlist_selector = TargetPlaylistSelector(
                playlist_manager,
                self.ui,
            )
            liked_tracks = LikedTracks(self.spotify)
            track_adder = PlaylistTrackAdder(self.spotify)
            return TransferLikedTracksWorkflow(
                self.ui,
                playlist_selector,
                liked_tracks,
                track_adder,
            )

        raise ValueError(f"Unsupported user action: {action.value}")
