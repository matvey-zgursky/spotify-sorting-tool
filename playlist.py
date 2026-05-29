from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

import spotipy

if TYPE_CHECKING:
    from user_interface import UserInterface

PLAYLIST_PAGE_LIMIT = 50


class PlaylistManager:
    """Работает с плейлистами текущего пользователя Spotify."""

    def __init__(
        self,
        spotify: spotipy.Spotify,
        current_user_id: str,
        page_limit: int = PLAYLIST_PAGE_LIMIT,
    ) -> None:
        self.spotify = spotify
        self.current_user_id = current_user_id
        self.page_limit = page_limit

    def get_user_playlists(self) -> list[dict]:
        """Вернуть все плейлисты из медиатеки текущего пользователя."""
        playlists = []
        offset = 0

        while True:
            page = self.spotify.current_user_playlists(
                limit=self.page_limit,
                offset=offset,
            )
            playlists.extend(page.get("items", []))

            if not page.get("next"):
                break

            offset += self.page_limit

        return playlists

    def find_by_id(self, playlist_id: str) -> dict | None:
        """Найти плейлист в медиатеке пользователя по id."""
        for playlist in self.get_user_playlists():
            if playlist.get("id") == playlist_id:
                return playlist

        return None

    def find_by_name(self, name: str) -> list[dict]:
        """Найти плейлисты в медиатеке пользователя по точному названию."""
        return [
            playlist
            for playlist in self.get_user_playlists()
            if playlist.get("name") == name
        ]

    def can_add_tracks(self, playlist: dict) -> bool:
        """Проверить, может ли текущий пользователь добавлять треки."""
        owner = playlist.get("owner") or {}
        return owner.get("id") == self.current_user_id

    def create(self, name: str) -> dict:
        """Создать новый публичный плейлист."""
        return self.spotify.current_user_playlist_create(
            name=name,
            public=True,
        )

    def extract_playlist_id(self, value: str) -> str | None:
        """Вернуть id плейлиста из URL/URI Spotify или None."""
        return self._extract_playlist_id_from_uri(value) or (
            self._extract_playlist_id_from_url(value)
        )

    def _extract_playlist_id_from_uri(self, value: str) -> str | None:
        """Вернуть id плейлиста из Spotify URI или None."""
        if value.startswith("spotify:playlist:"):
            return value.removeprefix("spotify:playlist:").strip() or None

        return None

    def _extract_playlist_id_from_url(self, value: str) -> str | None:
        """Вернуть id плейлиста из URL Spotify или None."""
        parsed_url = urlparse(value)
        if not parsed_url.scheme or not parsed_url.netloc:
            return None

        path_parts = [part for part in parsed_url.path.split("/") if part]
        try:
            playlist_index = path_parts.index("playlist")
        except ValueError:
            return None

        playlist_id_index = playlist_index + 1
        if playlist_id_index >= len(path_parts):
            return None

        return path_parts[playlist_id_index] or None


class TargetPlaylistSelector:
    """Выбирает целевой плейлист для переноса любимых треков."""

    def __init__(
        self,
        playlist_manager: PlaylistManager,
        user_interface: UserInterface,
    ) -> None:
        self.playlist_manager = playlist_manager
        self.user_interface = user_interface

    def select(self) -> dict | None:
        """Запросить и вернуть плейлист или None при отказе."""
        while True:
            playlist_name_or_url = self.user_interface.ask_playlist_name_or_url()
            playlist_id = self.playlist_manager.extract_playlist_id(
                playlist_name_or_url,
            )

            if playlist_id:
                result = self._handle_playlist_id(playlist_id)
            else:
                result = self._handle_playlist_name(playlist_name_or_url)

            if result is True:
                continue

            return result

    def _handle_playlist_id(self, playlist_id: str) -> dict | bool | None:
        """Обработать выбор плейлиста по id."""
        playlist = self.playlist_manager.find_by_id(playlist_id)
        if playlist is None:
            self.user_interface.show_playlist_not_found()
            return self._handle_not_found_by_url()

        if not self.playlist_manager.can_add_tracks(playlist):
            self.user_interface.show_no_permission()
            return True

        return playlist

    def _handle_playlist_name(self, name: str) -> dict | bool | None:
        """Обработать выбор плейлиста по имени."""
        matching_playlists = self.playlist_manager.find_by_name(name)
        if not matching_playlists:
            self.user_interface.show_playlist_not_found()
            return self._handle_not_found_by_name(name)

        editable_playlists = [
            playlist
            for playlist in matching_playlists
            if self.playlist_manager.can_add_tracks(playlist)
        ]
        if not editable_playlists:
            self.user_interface.show_no_permission()
            return True

        if len(editable_playlists) == 1:
            return editable_playlists[0]

        return self.user_interface.choose_playlist(editable_playlists)

    def _handle_not_found_by_name(self, name: str) -> dict | bool | None:
        """Обработать отсутствие плейлиста при поиске по имени."""
        if self.user_interface.ask_enter_another_playlist():
            return True

        if self.user_interface.ask_create_playlist(name):
            return self.playlist_manager.create(name)

        return None

    def _handle_not_found_by_url(self) -> dict | bool | None:
        """Обработать отсутствие плейлиста при поиске по URL/URI."""
        if self.user_interface.ask_enter_another_playlist():
            return True

        if self.user_interface.ask_create_playlist():
            new_playlist_name = self.user_interface.ask_new_playlist_name()
            return self.playlist_manager.create(new_playlist_name)

        return None
