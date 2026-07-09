import logging
from dataclasses import dataclass
from collections.abc import Iterator

from ..api.client import SpotifyClient
from ..errors import SpotifyAppError

SAVED_TRACKS_DELETE_LIMIT = 40

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RemoveTracksResult:
    """Результат удаления треков из любимых."""

    found_count: int
    removed_count: int


class LikedTrackRemoveError(SpotifyAppError):
    """Ошибка удаления любимых треков с частичным результатом операции."""

    def __init__(self, result: RemoveTracksResult, cause: Exception) -> None:
        self.result = result
        super().__init__(str(cause))


class SpotifyLikedTracksRemover:
    """Удаляет любимые треки через Spotify API."""

    def __init__(
        self,
        spotify: SpotifyClient,
        remove_limit: int = SAVED_TRACKS_DELETE_LIMIT,
    ) -> None:
        self.spotify = spotify
        self.remove_limit = remove_limit

    def remove(self, track_uris: list[str]) -> RemoveTracksResult:
        """Удалить треки из любимых."""
        logger.info(
            "Liked tracks remove started: tracks_count=%s",
            len(track_uris),
        )
        removed_count = 0

        for chunk in self._iter_track_uri_chunks(track_uris):
            logger.info(
                "Liked tracks remove batch started: batch_size=%s",
                len(chunk),
            )
            try:
                self.spotify.current_user_saved_tracks_delete(chunk)
                removed_count += len(chunk)
            except Exception as error:
                result = RemoveTracksResult(
                    found_count=len(track_uris),
                    removed_count=removed_count,
                )
                logger.error(
                    "Liked tracks remove batch failed: batch_size=%s "
                    "found_count=%s removed_count=%s error=%s",
                    len(chunk),
                    result.found_count,
                    result.removed_count,
                    error,
                )
                raise LikedTrackRemoveError(result, error) from error

        result = RemoveTracksResult(
            found_count=len(track_uris),
            removed_count=removed_count,
        )
        logger.info(
            "Liked tracks remove completed: found_count=%s removed_count=%s",
            result.found_count,
            result.removed_count,
        )
        return result

    def _iter_track_uri_chunks(self, track_uris: list[str]) -> Iterator[list[str]]:
        """Вернуть чанки URI треков для удаления."""
        for index in range(0, len(track_uris), self.remove_limit):
            yield track_uris[index : index + self.remove_limit]
