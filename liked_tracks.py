import spotipy

SAVED_TRACKS_PAGE_LIMIT = 50


class LikedTracks:
    """Работает с любимыми треками текущего пользователя Spotify."""

    def __init__(
        self,
        spotify: spotipy.Spotify,
        page_limit: int = SAVED_TRACKS_PAGE_LIMIT,
    ) -> None:
        self.spotify = spotify
        self.page_limit = page_limit

    def _get_saved_tracks_page(self, page_index: int) -> dict:
        """Вернуть страницу любимых треков по ее номеру."""
        return self.spotify.current_user_saved_tracks(
            limit=self.page_limit,
            offset=page_index * self.page_limit,
        )

    def _get_last_item_year(self, page: dict) -> int:
        """Вернуть год добавления последнего трека на странице."""
        return int(page["items"][-1]["added_at"][:4])

    def _find_first_page_not_newer_than_year(
        self,
        year: int,
        total: int,
    ) -> int | None:
        """Найти первую страницу, где последний трек добавлен не позже указанного года."""
        left_page = 0
        right_page = (total - 1) // self.page_limit
        result = None

        while left_page <= right_page:
            middle_page = (left_page + right_page) // 2
            page = self._get_saved_tracks_page(middle_page)
            last_year = self._get_last_item_year(page)

            if last_year > year:
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
            return 0

        return self._find_first_page_not_newer_than_year(year, total)

    def _collect_track_uris_starting_from_page(
        self,
        first_page: dict,
        start_page: int,
        year: int,
    ) -> list[str]:
        """Собрать URI любимых треков за год, начиная с указанной страницы."""
        track_uris = []
        page_index = start_page

        while True:
            if page_index == 0:
                page = first_page
            else:
                page = self._get_saved_tracks_page(page_index)

            for item in page.get("items", []):
                added_at = item["added_at"]
                added_year = int(added_at[:4])

                if added_year == year:
                    track_uris.append(item["track"]["uri"])
                elif added_year < year:
                    return track_uris

            if not page.get("next"):
                break

            page_index += 1

        return track_uris

    def get_uris_by_added_year(
        self,
        year: int,
    ) -> list[str]:
        """Вернуть URI любимых треков, добавленных в указанном году."""
        first_page = self._get_saved_tracks_page(0)
        total = first_page["total"]

        if total == 0:
            return []

        start_page = self._find_start_page_by_added_year(
            year,
            total,
        )

        if start_page is None:
            return []

        return self._collect_track_uris_starting_from_page(
            first_page,
            start_page,
            year,
        )
