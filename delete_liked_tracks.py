import logging

from liked_tracks import LikedTrackRemoveError, LikedTrackRemover, LikedTracks
from ui import UserInterface

logger = logging.getLogger(__name__)


class DeleteLikedTracksWorkflow:
    """Выполняет сценарий удаления любимых треков."""

    def __init__(
        self,
        ui: UserInterface,
        liked_tracks: LikedTracks,
        track_remover: LikedTrackRemover,
    ) -> None:
        self.ui = ui
        self.liked_tracks = liked_tracks
        self.track_remover = track_remover

    def run(self) -> None:
        """Удалить любимые треки за выбранный год."""
        logger.info("Delete liked tracks workflow started")
        year = self.ui.ask_added_year()
        logger.info("Added year selected: year=%s", year)

        track_uris = self._find_liked_tracks(year)
        if not track_uris:
            logger.info(
                "Delete liked tracks workflow stopped: no liked tracks found "
                "year=%s",
                year,
            )
            return

        if not self._confirm_delete(len(track_uris), year):
            logger.info(
                "Delete liked tracks workflow cancelled: year=%s tracks_count=%s",
                year,
                len(track_uris),
            )
            return

        self._delete_tracks(track_uris)

    def _find_liked_tracks(self, year: int) -> list[str]:
        """Найти URI любимых треков за год."""
        self.ui.show_liked_tracks_search_started(year)
        track_uris = self.liked_tracks.get_uris_by_added_year(year)
        logger.info(
            "Liked tracks found: year=%s tracks_count=%s",
            year,
            len(track_uris),
        )
        if not track_uris:
            self.ui.show_no_liked_tracks_found(year)

        return track_uris

    def _confirm_delete(self, tracks_count: int, year: int) -> bool:
        """Подтвердить удаление найденных треков."""
        self.ui.show_selected_tracks_count(tracks_count, year)
        if self.ui.ask_confirm_tracks_delete():
            logger.info(
                "Tracks delete confirmed: year=%s tracks_count=%s",
                year,
                tracks_count,
            )
            return True

        logger.info(
            "Tracks delete declined: year=%s tracks_count=%s",
            year,
            tracks_count,
        )
        self.ui.show_tracks_delete_cancelled()
        return False

    def _delete_tracks(self, track_uris: list[str]) -> None:
        """Удалить треки из любимых."""
        self.ui.show_tracks_delete_started()
        logger.info("Tracks delete started: tracks_count=%s", len(track_uris))
        try:
            result = self.track_remover.remove_tracks(track_uris)
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
