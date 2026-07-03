import logging

from api.types import SpotifyPlaylist
from liked_tracks import LikedTrackRemoveError, LikedTrackRemover, LikedTracks
from playlist import (
    AddTracksResult,
    PlaylistTrackAddError,
    PlaylistTrackAdder,
    TargetPlaylistSelector,
)
from ui import UserInterface

logger = logging.getLogger(__name__)


class TransferLikedTracksWorkflow:
    """Выполняет сценарий переноса любимых треков в плейлист."""

    def __init__(
        self,
        ui: UserInterface,
        playlist_selector: TargetPlaylistSelector,
        liked_tracks: LikedTracks,
        track_adder: PlaylistTrackAdder,
        track_remover: LikedTrackRemover,
    ) -> None:
        self.ui = ui
        self.playlist_selector = playlist_selector
        self.liked_tracks = liked_tracks
        self.track_adder = track_adder
        self.track_remover = track_remover

    def run(self) -> None:
        """Перенести любимые треки за выбранный год в выбранный плейлист."""
        logger.info("Transfer liked tracks workflow started")
        year = self.ui.ask_added_year()
        logger.info("Added year selected: year=%s", year)
        target_playlist = self._select_target_playlist()
        if target_playlist is None:
            logger.info("Transfer liked tracks workflow stopped: no target playlist")
            return

        track_uris = self._find_liked_tracks(year)
        if not track_uris:
            logger.info(
                "Transfer liked tracks workflow stopped: no liked tracks found "
                "year=%s",
                year,
            )
            return

        if not self._confirm_transfer(len(track_uris), year):
            logger.info(
                "Transfer liked tracks workflow cancelled: year=%s tracks_count=%s",
                year,
                len(track_uris),
            )
            return

        result = self._transfer_tracks(target_playlist, track_uris)
        self._delete_transferred_tracks(result.added_track_uris)

    def _select_target_playlist(self) -> SpotifyPlaylist | None:
        """Выбрать целевой плейлист для переноса."""
        target_playlist = self.playlist_selector.select()
        if target_playlist is None:
            self.ui.show_no_target_playlist_selected()
            return None

        self.ui.show_selected_playlist(target_playlist)
        logger.info(
            "Target playlist selected: playlist_id=%s playlist_name=%r",
            target_playlist["id"],
            target_playlist["name"],
        )
        return target_playlist

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

    def _confirm_transfer(self, tracks_count: int, year: int) -> bool:
        """Подтвердить перенос найденных треков."""
        self.ui.show_selected_tracks_count(tracks_count, year)
        if self.ui.ask_confirm_tracks_transfer():
            logger.info(
                "Tracks transfer confirmed: year=%s tracks_count=%s",
                year,
                tracks_count,
            )
            return True

        logger.info(
            "Tracks transfer declined: year=%s tracks_count=%s",
            year,
            tracks_count,
        )
        self.ui.show_tracks_transfer_cancelled()
        return False

    def _transfer_tracks(
        self,
        playlist: SpotifyPlaylist,
        track_uris: list[str],
    ) -> AddTracksResult:
        """Перенести треки в плейлист."""
        self.ui.show_tracks_transfer_started()
        logger.info(
            "Tracks transfer started: playlist_id=%s playlist_name=%r "
            "tracks_count=%s",
            playlist["id"],
            playlist["name"],
            len(track_uris),
        )
        try:
            result = self.track_adder.add_tracks(playlist["id"], track_uris)
        except PlaylistTrackAddError as error:
            self.ui.show_tracks_partially_added(error.result, playlist)
            logger.error(
                "Tracks transfer failed after partial add: playlist_id=%s "
                "playlist_name=%r found_count=%s added_count=%s skipped_count=%s",
                playlist["id"],
                playlist["name"],
                error.result.found_count,
                error.result.added_count,
                error.result.skipped_count,
            )
            raise

        self.ui.show_tracks_added(result, playlist)
        logger.info(
            "Tracks transfer completed: playlist_id=%s playlist_name=%r "
            "found_count=%s added_count=%s skipped_count=%s",
            playlist["id"],
            playlist["name"],
            result.found_count,
            result.added_count,
            result.skipped_count,
        )
        return result

    def _delete_transferred_tracks(self, track_uris: list[str]) -> None:
        """Удалить успешно перенесенные треки из любимых."""
        if not track_uris:
            logger.info("Transferred tracks delete skipped: no tracks added")
            return

        if not self.ui.ask_delete_transferred_tracks():
            logger.info(
                "Transferred tracks delete declined: tracks_count=%s",
                len(track_uris),
            )
            self.ui.show_tracks_delete_cancelled()
            return

        self.ui.show_tracks_delete_started()
        logger.info(
            "Transferred tracks delete started: tracks_count=%s",
            len(track_uris),
        )
        try:
            result = self.track_remover.remove_tracks(track_uris)
        except LikedTrackRemoveError as error:
            self.ui.show_tracks_partially_deleted(error.result)
            logger.error(
                "Transferred tracks delete failed after partial remove: "
                "found_count=%s removed_count=%s",
                error.result.found_count,
                error.result.removed_count,
            )
            raise

        self.ui.show_tracks_deleted(result)
        logger.info(
            "Transferred tracks delete completed: found_count=%s removed_count=%s",
            result.found_count,
            result.removed_count,
        )
