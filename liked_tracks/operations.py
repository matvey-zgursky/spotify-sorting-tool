from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from liked_tracks.reader import SpotifyLikedTracksReader
from liked_tracks.remover import LikedTrackRemoveError, SpotifyLikedTracksRemover

if TYPE_CHECKING:
    from ui import UserInterface

logger = logging.getLogger(__name__)


class LikedTracksFinder:
    """Ищет любимые треки."""

    def __init__(
        self,
        ui: UserInterface,
        spotify_reader: SpotifyLikedTracksReader,
    ) -> None:
        self.ui = ui
        self.spotify_reader = spotify_reader

    def find_uris_by_added_year(self, year: int) -> list[str]:
        """Найти URI любимых треков за год добавления."""
        self.ui.show_liked_tracks_search_started(year)
        track_uris = self.spotify_reader.get_uris_by_added_year(year)
        logger.info(
            "Liked tracks found: year=%s tracks_count=%s",
            year,
            len(track_uris),
        )
        if not track_uris:
            self.ui.show_no_liked_tracks_found(year)

        return track_uris


class LikedTracksDeleter:
    """Удаляет любимые треки."""

    def __init__(
        self,
        ui: UserInterface,
        spotify_remover: SpotifyLikedTracksRemover,
    ) -> None:
        self.ui = ui
        self.spotify_remover = spotify_remover

    def delete(self, track_uris: list[str]) -> None:
        """Удалить треки из любимых."""
        self.ui.show_tracks_delete_started()
        logger.info("Tracks delete started: tracks_count=%s", len(track_uris))
        try:
            result = self.spotify_remover.remove(track_uris)
        except LikedTrackRemoveError as error:
            self.ui.show_tracks_partially_deleted(error.result)
            logger.error(
                "Tracks delete failed after partial remove: found_count=%s "
                "removed_count=%s",
                error.result.found_count,
                error.result.removed_count,
            )
            raise

        self.ui.show_tracks_deleted(result)
        logger.info(
            "Tracks delete completed: found_count=%s removed_count=%s",
            result.found_count,
            result.removed_count,
        )
