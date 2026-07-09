from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from .spotify_remover import (
    LikedTrackRemoveError,
    SpotifyLikedTracksRemover,
)

if TYPE_CHECKING:
    from ..ui import UserInterface

logger = logging.getLogger(__name__)


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
