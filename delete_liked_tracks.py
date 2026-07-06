import logging

from liked_tracks_operations import LikedTracksDeleter, LikedTracksFinder
from ui import UserInterface

logger = logging.getLogger(__name__)


class DeleteLikedTracksWorkflow:
    """Выполняет сценарий удаления любимых треков."""

    def __init__(
        self,
        ui: UserInterface,
        liked_tracks_finder: LikedTracksFinder,
        liked_tracks_deleter: LikedTracksDeleter,
    ) -> None:
        self.ui = ui
        self.liked_tracks_finder = liked_tracks_finder
        self.liked_tracks_deleter = liked_tracks_deleter

    def run(self) -> None:
        """Удалить любимые треки за выбранный год."""
        logger.info("Delete liked tracks workflow started")
        year = self.ui.ask_added_year()
        logger.info("Added year selected: year=%s", year)

        track_uris = self.liked_tracks_finder.find_uris_by_added_year(year)
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

        self.liked_tracks_deleter.delete(track_uris)

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
