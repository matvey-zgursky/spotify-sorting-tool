from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .spotify_reader import SpotifyLikedTracksReader

if TYPE_CHECKING:
    from ..ui import UserInterface

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
