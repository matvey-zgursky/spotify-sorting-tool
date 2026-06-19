from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from api.client import SpotifyClient

if TYPE_CHECKING:
    from ui import UserInterface

PLAYLIST_PAGE_LIMIT = 50
ADD_ITEMS_LIMIT = 100
PLAYLIST_ITEMS_LIMIT = 100


@dataclass(frozen=True)
class AddTracksResult:
    """Результат добавления треков в плейлист."""

    found_count: int
    added_count: int
    skipped_count: int


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
        new_track_uris = self._exclude_existing_track_uris(
            playlist_id,
            track_uris,
        )

        for chunk in self._split_track_uris_chunks(new_track_uris):
            self.spotify.playlist_add_items(playlist_id, chunk)

        return AddTracksResult(
            found_count=len(track_uris),
            added_count=len(new_track_uris),
            skipped_count=len(track_uris) - len(new_track_uris),
        )

    def _exclude_existing_track_uris(
        self,
        playlist_id: str,
        track_uris: list[str],
    ) -> list[str]:
        """Вернуть URI треков, которых еще нет в плейлисте."""
        known_track_uris = self._get_playlist_track_uris(playlist_id)
        new_track_uris = []

        for track_uri in track_uris:
            if track_uri not in known_track_uris:
                new_track_uris.append(track_uri)
                known_track_uris.add(track_uri)

        return new_track_uris

    def _get_playlist_track_uris(self, playlist_id: str) -> set[str]:
        """Вернуть URI всех треков плейлиста."""
        track_uris = set()
        offset = 0

        while True:
            page = self.spotify.playlist_items(
                playlist_id,
                limit=self.read_limit,
                offset=offset,
            )

            items = page.get("items", [])

            for item in items:
                track = item.get("item") or {}
                track_uri = track.get("uri")
                if track_uri:
                    track_uris.add(track_uri)

            if not page.get("next"):
                break

            offset += self.read_limit

        return track_uris

    def _split_track_uris_chunks(
        self,
        track_uris: list[str],
    ) -> list[list[str]]:
        """Разбить URI на пачки допустимого размера для Spotify API."""
        return [
            track_uris[index : index + self.add_limit]
            for index in range(0, len(track_uris), self.add_limit)
        ]


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
        ui: UserInterface,
    ) -> None:
        self.playlist_manager = playlist_manager
        self.ui = ui

    def select(self) -> dict | None:
        """Запросить и вернуть плейлист или None при отказе."""
        while True:
            playlist_name_or_url = self.ui.ask_playlist_name_or_url()
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
            self.ui.show_playlist_not_found()
            return self._handle_not_found_by_url()

        if not self.playlist_manager.can_add_tracks(playlist):
            self.ui.show_no_permission()
            return True

        return playlist

    def _handle_playlist_name(self, name: str) -> dict | bool | None:
        """Обработать выбор плейлиста по имени."""
        matching_playlists = self.playlist_manager.find_by_name(name)
        if not matching_playlists:
            self.ui.show_playlist_not_found()
            return self._handle_not_found_by_name(name)

        editable_playlists = [
            playlist
            for playlist in matching_playlists
            if self.playlist_manager.can_add_tracks(playlist)
        ]
        if not editable_playlists:
            self.ui.show_no_permission()
            return True

        if len(editable_playlists) == 1:
            return editable_playlists[0]

        return self.ui.choose_playlist(editable_playlists)

    def _handle_not_found_by_name(self, name: str) -> dict | bool | None:
        """Обработать отсутствие плейлиста при поиске по имени."""
        if self.ui.ask_enter_another_playlist():
            return True

        if self.ui.ask_create_playlist(name):
            return self.playlist_manager.create(name)

        return None

    def _handle_not_found_by_url(self) -> dict | bool | None:
        """Обработать отсутствие плейлиста при поиске по URL/URI."""
        if self.ui.ask_enter_another_playlist():
            return True

        if self.ui.ask_create_playlist():
            new_playlist_name = self.ui.ask_new_playlist_name()
            return self.playlist_manager.create(new_playlist_name)

        return None
