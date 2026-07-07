from __future__ import annotations

import logging

from api.client import SpotifyClient
from api.types import SpotifyPlaylist

PLAYLIST_PAGE_LIMIT = 50

logger = logging.getLogger(__name__)


class PlaylistManager:
    """Работает с плейлистами текущего пользователя Spotify."""

    def __init__(
        self,
        spotify: SpotifyClient,
        current_user_id: str,
        page_limit: int = PLAYLIST_PAGE_LIMIT,
    ) -> None:
        self.spotify = spotify
        self.current_user_id = current_user_id
        self.page_limit = page_limit

    def get_user_playlists(self) -> list[SpotifyPlaylist]:
        """Вернуть все плейлисты из медиатеки текущего пользователя."""
        playlists: list[SpotifyPlaylist] = []
        offset = 0

        while True:
            page = self.spotify.current_user_playlists(
                limit=self.page_limit,
                offset=offset,
            )
            items = page["items"]
            playlists.extend(items)
            logger.debug(
                "User playlists page loaded: offset=%s limit=%s items_count=%s",
                offset,
                self.page_limit,
                len(items),
            )

            if not page["next"]:
                break

            offset += self.page_limit

        logger.debug("User playlists loaded: playlists_count=%s", len(playlists))
        return playlists

    def find_by_id(self, playlist_id: str) -> SpotifyPlaylist | None:
        """Найти плейлист в медиатеке пользователя по id."""
        for playlist in self.get_user_playlists():
            if playlist["id"] == playlist_id:
                return playlist

        return None

    def find_by_name(self, name: str) -> list[SpotifyPlaylist]:
        """Найти плейлисты в медиатеке пользователя по точному названию."""
        return [
            playlist
            for playlist in self.get_user_playlists()
            if playlist["name"] == name
        ]

    def can_add_tracks(self, playlist: SpotifyPlaylist) -> bool:
        """Проверить, может ли текущий пользователь добавлять треки."""
        can_add = playlist["owner_id"] == self.current_user_id
        logger.debug(
            "Playlist edit permission checked: playlist_id=%s playlist_name=%r "
            "can_add=%s",
            playlist["id"],
            playlist["name"],
            can_add,
        )
        return can_add

    def create(self, name: str) -> SpotifyPlaylist:
        """Создать новый публичный плейлист."""
        return self.spotify.current_user_playlist_create(
            name=name,
            public=True,
        )
