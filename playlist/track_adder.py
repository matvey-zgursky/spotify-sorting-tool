from collections.abc import Iterator
from dataclasses import dataclass
import logging

from api.client import SpotifyClient
from errors import SpotifyAppError

ADD_ITEMS_LIMIT = 100
PLAYLIST_ITEMS_LIMIT = 100

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddTracksResult:
    """Результат добавления треков в плейлист."""

    found_count: int
    added_count: int
    skipped_count: int
    added_track_uris: list[str]


class PlaylistTrackAddError(SpotifyAppError):
    """Ошибка добавления треков с частичным результатом операции."""

    def __init__(self, result: AddTracksResult, cause: Exception) -> None:
        self.result = result
        super().__init__(str(cause))


class PlaylistTrackAdder:
    """Добавляет треки в плейлист."""

    def __init__(
        self,
        spotify: SpotifyClient,
        add_limit: int = ADD_ITEMS_LIMIT,
        read_limit: int = PLAYLIST_ITEMS_LIMIT,
    ) -> None:
        self.spotify = spotify
        self.add_limit = add_limit
        self.read_limit = read_limit

    def add_tracks(
        self,
        playlist_id: str,
        track_uris: list[str],
    ) -> AddTracksResult:
        """Добавить в плейлист отсутствующие в нем треки."""
        logger.info(
            "Playlist track add started: playlist_id=%s tracks_count=%s",
            playlist_id,
            len(track_uris),
        )
        new_track_uris = self._exclude_existing_track_uris(
            playlist_id,
            track_uris,
        )

        added_track_uris: list[str] = []
        for chunk in self._iter_track_uri_chunks(new_track_uris):
            logger.info(
                "Playlist track batch add started: playlist_id=%s batch_size=%s",
                playlist_id,
                len(chunk),
            )
            try:
                self.spotify.playlist_add_items(playlist_id, chunk)
                added_track_uris.extend(chunk)
            except Exception as error:
                result = AddTracksResult(
                    found_count=len(track_uris),
                    added_count=len(added_track_uris),
                    skipped_count=len(track_uris) - len(new_track_uris),
                    added_track_uris=added_track_uris.copy(),
                )
                logger.error(
                    "Playlist track batch add failed: playlist_id=%s "
                    "batch_size=%s added_count=%s skipped_count=%s error=%s",
                    playlist_id,
                    len(chunk),
                    result.added_count,
                    result.skipped_count,
                    error,
                )
                raise PlaylistTrackAddError(result, error) from error

        result = AddTracksResult(
            found_count=len(track_uris),
            added_count=len(added_track_uris),
            skipped_count=len(track_uris) - len(new_track_uris),
            added_track_uris=added_track_uris.copy(),
        )
        logger.info(
            "Playlist track add completed: playlist_id=%s found_count=%s "
            "added_count=%s skipped_count=%s",
            playlist_id,
            result.found_count,
            result.added_count,
            result.skipped_count,
        )
        return result

    def _exclude_existing_track_uris(
        self,
        playlist_id: str,
        track_uris: list[str],
    ) -> list[str]:
        """Вернуть URI треков, которых еще нет в плейлисте."""
        logger.info(
            "Playlist track deduplication started: playlist_id=%s "
            "tracks_count=%s",
            playlist_id,
            len(track_uris),
        )
        known_track_uris = self._get_playlist_track_uris(playlist_id)
        new_track_uris: list[str] = []

        for track_uri in track_uris:
            if track_uri not in known_track_uris:
                new_track_uris.append(track_uri)
                known_track_uris.add(track_uri)

        logger.info(
            "Playlist track deduplication completed: playlist_id=%s "
            "new_count=%s skipped_count=%s",
            playlist_id,
            len(new_track_uris),
            len(track_uris) - len(new_track_uris),
        )
        return new_track_uris

    def _get_playlist_track_uris(self, playlist_id: str) -> set[str]:
        """Вернуть URI всех треков плейлиста."""
        track_uris: set[str] = set()
        offset = 0

        while True:
            page = self.spotify.playlist_items(
                playlist_id,
                limit=self.read_limit,
                offset=offset,
            )

            items = page["items"]

            for item in items:
                track = item["item"]
                if track is not None:
                    track_uris.add(track["uri"])

            if not page["next"]:
                break

            offset += self.read_limit

        logger.info(
            "Existing playlist tracks loaded: playlist_id=%s existing_count=%s",
            playlist_id,
            len(track_uris),
        )
        return track_uris

    def _iter_track_uri_chunks(self, track_uris: list[str]) -> Iterator[list[str]]:
        """Вернуть чанки URI треков для добавления."""
        for index in range(0, len(track_uris), self.add_limit):
            yield track_uris[index : index + self.add_limit]
