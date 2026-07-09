import logging
from dataclasses import dataclass

from ..api.client import SpotifyClient
from ..api.types import SpotifySavedTracksPage

SAVED_TRACKS_PAGE_LIMIT = 50

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _SavedTracksPageScan:
    """Результат сканирования одной страницы любимых треков."""

    track_uris: list[str]
    stop_year: int | None = None

    @property
    def should_stop(self) -> bool:
        """Вернуть True, если дальнейшее сканирование страниц не нужно."""
        return self.stop_year is not None


class SpotifyLikedTracksReader:
    """Читает любимые треки текущего пользователя из Spotify."""

    def __init__(
        self,
        spotify: SpotifyClient,
        page_limit: int = SAVED_TRACKS_PAGE_LIMIT,
    ) -> None:
        self.spotify = spotify
        self.page_limit = page_limit

    def _get_saved_tracks_page(self, page_index: int) -> SpotifySavedTracksPage:
        """Вернуть страницу любимых треков по ее номеру."""
        return self.spotify.current_user_saved_tracks(
            limit=self.page_limit,
            offset=page_index * self.page_limit,
        )

    def _get_added_year(self, added_at: str) -> int:
        """Вернуть год из даты добавления трека."""
        return int(added_at[:4])

    def _get_oldest_track_year(self, page: SpotifySavedTracksPage) -> int:
        """Вернуть год добавления самого старого трека на странице."""
        return self._get_added_year(page["items"][-1]["added_at"])

    def _find_first_page_with_old_enough_tracks(
        self,
        year: int,
        total: int,
    ) -> int | None:
        """Найти первую страницу, где могут быть треки указанного года."""
        left_page = 0
        right_page = (total - 1) // self.page_limit
        result = None

        while left_page <= right_page:
            middle_page = (left_page + right_page) // 2
            page = self._get_saved_tracks_page(middle_page)
            oldest_track_year = self._get_oldest_track_year(page)
            logger.debug(
                "Liked tracks start page probe: year=%s page=%s "
                "oldest_track_year=%s",
                year,
                middle_page,
                oldest_track_year,
            )

            if oldest_track_year > year:
                left_page = middle_page + 1
            else:
                result = middle_page
                right_page = middle_page - 1

        return result

    def _find_start_page_by_added_year(
        self,
        year: int,
        total: int,
    ) -> int | None:
        """Вернуть первую страницу, с которой стоит искать треки за указанный год."""
        if total <= self.page_limit:
            logger.info(
                "Liked tracks start page selected: year=%s start_page=0",
                year,
            )
            return 0

        start_page = self._find_first_page_with_old_enough_tracks(year, total)
        logger.info(
            "Liked tracks start page selected: year=%s start_page=%s",
            year,
            start_page,
        )
        return start_page

    def _collect_track_uris_starting_from_page(
        self,
        first_page: SpotifySavedTracksPage,
        start_page: int,
        year: int,
    ) -> list[str]:
        """Собрать URI любимых треков за год, начиная с указанной страницы."""
        track_uris: list[str] = []
        page_index = start_page

        while True:
            if page_index == 0:
                page = first_page
            else:
                page = self._get_saved_tracks_page(page_index)

            page_scan = self._scan_track_uris_by_added_year(page, year)
            track_uris.extend(page_scan.track_uris)

            if page_scan.should_stop:
                logger.debug(
                    "Liked tracks page scan stopped: year=%s page=%s "
                    "matched_count=%s tracks_count=%s stop_year=%s",
                    year,
                    page_index,
                    len(page_scan.track_uris),
                    len(track_uris),
                    page_scan.stop_year,
                )
                return track_uris

            logger.debug(
                "Liked tracks page scanned: year=%s page=%s matched_count=%s "
                "tracks_count=%s",
                year,
                page_index,
                len(page_scan.track_uris),
                len(track_uris),
            )

            if not page["next"]:
                break

            page_index += 1

        return track_uris

    def _scan_track_uris_by_added_year(
        self,
        page: SpotifySavedTracksPage,
        year: int,
    ) -> _SavedTracksPageScan:
        """Собрать URI треков указанного года на одной странице."""
        track_uris: list[str] = []

        for item in page["items"]:
            added_year = self._get_added_year(item["added_at"])

            if added_year == year:
                track_uris.append(item["track"]["uri"])
            elif added_year < year:
                return _SavedTracksPageScan(track_uris, added_year)

        return _SavedTracksPageScan(track_uris)

    def get_uris_by_added_year(
        self,
        year: int,
    ) -> list[str]:
        """Вернуть URI любимых треков, добавленных в указанном году."""
        logger.info("Liked tracks search started: year=%s", year)
        first_page = self._get_saved_tracks_page(0)
        total = first_page["total"]
        logger.info("Liked tracks first page loaded: year=%s total=%s", year, total)

        if total == 0:
            logger.info("Liked tracks search stopped: library is empty year=%s", year)
            return []

        start_page = self._find_start_page_by_added_year(
            year,
            total,
        )

        if start_page is None:
            logger.info(
                "Liked tracks search stopped: no start page found year=%s",
                year,
            )
            return []

        track_uris = self._collect_track_uris_starting_from_page(
            first_page,
            start_page,
            year,
        )
        logger.info(
            "Liked tracks search completed: year=%s tracks_count=%s",
            year,
            len(track_uris),
        )
        return track_uris
