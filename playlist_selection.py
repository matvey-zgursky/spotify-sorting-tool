from __future__ import annotations

from enum import Enum
import logging
from typing import TYPE_CHECKING, Literal, TypeAlias

from api.types import SpotifyPlaylist
from playlist import PlaylistManager
from playlist_id_parser import parse_playlist_id

if TYPE_CHECKING:
    from ui import UserInterface

logger = logging.getLogger(__name__)


class PlaylistSelectionSignal(Enum):
    """Служебные сигналы выбора целевого плейлиста."""

    RETRY = "retry"


PlaylistSelectionRetry: TypeAlias = Literal[PlaylistSelectionSignal.RETRY]


class TargetPlaylistSelector:
    """Выбирает целевой плейлист для переноса любимых треков."""

    def __init__(
        self,
        playlist_manager: PlaylistManager,
        ui: UserInterface,
    ) -> None:
        self.playlist_manager = playlist_manager
        self.ui = ui

    def select(self) -> SpotifyPlaylist | None:
        """Запросить и вернуть плейлист или None при отказе."""
        while True:
            playlist_name_or_url = self.ui.ask_playlist_name_or_url()
            playlist_id = parse_playlist_id(playlist_name_or_url)

            if playlist_id:
                logger.info("Target playlist input received: input_type=id")
                result = self._handle_playlist_id(playlist_id)
            else:
                logger.info("Target playlist input received: input_type=name")
                result = self._handle_playlist_name(playlist_name_or_url)

            if result == PlaylistSelectionSignal.RETRY:
                continue

            return result

    def _handle_playlist_id(
        self,
        playlist_id: str,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать выбор плейлиста по id."""
        playlist = self.playlist_manager.find_by_id(playlist_id)
        if playlist is None:
            logger.info("Target playlist not found by id: playlist_id=%s", playlist_id)
            self.ui.show_playlist_not_found()
            return self._handle_not_found_by_url()

        if not self.playlist_manager.can_add_tracks(playlist):
            logger.info(
                "Target playlist is not editable: playlist_id=%s playlist_name=%r",
                playlist["id"],
                playlist["name"],
            )
            self.ui.show_no_permission()
            return PlaylistSelectionSignal.RETRY

        logger.info(
            "Target playlist selected by id: playlist_id=%s playlist_name=%r",
            playlist["id"],
            playlist["name"],
        )
        return playlist

    def _handle_playlist_name(
        self,
        name: str,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать выбор плейлиста по имени."""
        matching_playlists = self.playlist_manager.find_by_name(name)
        logger.info(
            "Target playlist name search completed: matches_count=%s",
            len(matching_playlists),
        )
        if not matching_playlists:
            self.ui.show_playlist_not_found()
            return self._handle_not_found_by_name(name)

        editable_playlists = [
            playlist
            for playlist in matching_playlists
            if self.playlist_manager.can_add_tracks(playlist)
        ]
        logger.info(
            "Editable target playlists filtered: matches_count=%s "
            "editable_count=%s",
            len(matching_playlists),
            len(editable_playlists),
        )
        if not editable_playlists:
            logger.info("No editable target playlists found by name")
            self.ui.show_no_permission()
            return PlaylistSelectionSignal.RETRY

        if len(editable_playlists) == 1:
            playlist = editable_playlists[0]
            logger.info(
                "Target playlist selected by name: playlist_id=%s "
                "playlist_name=%r",
                playlist["id"],
                playlist["name"],
            )
            return editable_playlists[0]

        logger.info(
            "Multiple editable target playlists found: editable_count=%s",
            len(editable_playlists),
        )
        selected_playlist = self.ui.choose_playlist(editable_playlists)
        logger.info(
            "Target playlist selected from multiple matches: playlist_id=%s "
            "playlist_name=%r",
            selected_playlist["id"],
            selected_playlist["name"],
        )
        return selected_playlist

    def _handle_not_found_by_name(
        self,
        name: str,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать отсутствие плейлиста при поиске по имени."""
        if self.ui.ask_enter_another_playlist():
            logger.info("Target playlist selection retry requested: source=name")
            return PlaylistSelectionSignal.RETRY

        if self.ui.ask_create_playlist(name):
            logger.info("Target playlist creation requested: source=name")
            playlist = self.playlist_manager.create(name)
            logger.info(
                "Target playlist created: playlist_id=%s playlist_name=%r",
                playlist["id"],
                playlist["name"],
            )
            return playlist

        logger.info("Target playlist selection cancelled: source=name")
        return None

    def _handle_not_found_by_url(
        self,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать отсутствие плейлиста при поиске по URL/URI."""
        if self.ui.ask_enter_another_playlist():
            logger.info("Target playlist selection retry requested: source=id")
            return PlaylistSelectionSignal.RETRY

        if self.ui.ask_create_playlist():
            logger.info("Target playlist creation requested: source=id")
            new_playlist_name = self.ui.ask_new_playlist_name()
            playlist = self.playlist_manager.create(new_playlist_name)
            logger.info(
                "Target playlist created: playlist_id=%s playlist_name=%r",
                playlist["id"],
                playlist["name"],
            )
            return playlist

        logger.info("Target playlist selection cancelled: source=id")
        return None
