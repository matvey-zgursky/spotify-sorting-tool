import spotipy

from search import find_start_page_by_added_year


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

        start_page = find_start_page_by_added_year(
            self._get_saved_tracks_page,
            year,
            total,
            self.page_limit,
        )

        if start_page is None:
            return []

        return self._collect_track_uris_starting_from_page(
            first_page,
            start_page,
            year,
        )
