from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import logging
from typing import TYPE_CHECKING, Literal, TypeAlias
from urllib.parse import urlparse

from api.client import SpotifyClient
from api.types import SpotifyPlaylist

if TYPE_CHECKING:
    from ui import UserInterface

PLAYLIST_PAGE_LIMIT = 50
ADD_ITEMS_LIMIT = 100
PLAYLIST_ITEMS_LIMIT = 100

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AddTracksResult:
    """Результат добавления треков в плейлист."""

    found_count: int
    added_count: int
    skipped_count: int


class PlaylistSelectionSignal(Enum):
    """Служебные сигналы выбора целевого плейлиста."""

    RETRY = "retry"


PlaylistSelectionRetry: TypeAlias = Literal[PlaylistSelectionSignal.RETRY]


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

        for chunk in self._split_track_uris_chunks(new_track_uris):
            logger.info(
                "Playlist track batch add started: playlist_id=%s batch_size=%s",
                playlist_id,
                len(chunk),
            )
            self.spotify.playlist_add_items(playlist_id, chunk)

        result = AddTracksResult(
            found_count=len(track_uris),
            added_count=len(new_track_uris),
            skipped_count=len(track_uris) - len(new_track_uris),
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
            "Playlist edit permission checked: playlist_id=%s playlist_name=%s "
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

    def select(self) -> SpotifyPlaylist | None:
        """Запросить и вернуть плейлист или None при отказе."""
        while True:
            playlist_name_or_url = self.ui.ask_playlist_name_or_url()
            playlist_id = self.playlist_manager.extract_playlist_id(
                playlist_name_or_url,
            )

            if playlist_id:
                logger.info("Target playlist input received: input_type=id")
                result = self._handle_playlist_id(playlist_id)
            else:
                logger.info("Target playlist input received: input_type=name")
                result = self._handle_playlist_name(playlist_name_or_url)

            if result == PlaylistSelectionSignal.RETRY:
                continue

            return result

    def _handle_playlist_id(
        self,
        playlist_id: str,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать выбор плейлиста по id."""
        playlist = self.playlist_manager.find_by_id(playlist_id)
        if playlist is None:
            logger.info("Target playlist not found by id: playlist_id=%s", playlist_id)
            self.ui.show_playlist_not_found()
            return self._handle_not_found_by_url()

        if not self.playlist_manager.can_add_tracks(playlist):
            logger.info(
                "Target playlist is not editable: playlist_id=%s playlist_name=%s",
                playlist["id"],
                playlist["name"],
            )
            self.ui.show_no_permission()
            return PlaylistSelectionSignal.RETRY

        logger.info(
            "Target playlist selected by id: playlist_id=%s playlist_name=%s",
            playlist["id"],
            playlist["name"],
        )
        return playlist

    def _handle_playlist_name(
        self,
        name: str,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать выбор плейлиста по имени."""
        matching_playlists = self.playlist_manager.find_by_name(name)
        logger.info(
            "Target playlist name search completed: matches_count=%s",
            len(matching_playlists),
        )
        if not matching_playlists:
            self.ui.show_playlist_not_found()
            return self._handle_not_found_by_name(name)

        editable_playlists = [
            playlist
            for playlist in matching_playlists
            if self.playlist_manager.can_add_tracks(playlist)
        ]
        logger.info(
            "Editable target playlists filtered: matches_count=%s "
            "editable_count=%s",
            len(matching_playlists),
            len(editable_playlists),
        )
        if not editable_playlists:
            logger.info("No editable target playlists found by name")
            self.ui.show_no_permission()
            return PlaylistSelectionSignal.RETRY

        if len(editable_playlists) == 1:
            playlist = editable_playlists[0]
            logger.info(
                "Target playlist selected by name: playlist_id=%s "
                "playlist_name=%s",
                playlist["id"],
                playlist["name"],
            )
            return editable_playlists[0]

        logger.info(
            "Multiple editable target playlists found: editable_count=%s",
            len(editable_playlists),
        )
        selected_playlist = self.ui.choose_playlist(editable_playlists)
        logger.info(
            "Target playlist selected from multiple matches: playlist_id=%s "
            "playlist_name=%s",
            selected_playlist["id"],
            selected_playlist["name"],
        )
        return selected_playlist

    def _handle_not_found_by_name(
        self,
        name: str,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать отсутствие плейлиста при поиске по имени."""
        if self.ui.ask_enter_another_playlist():
            logger.info("Target playlist selection retry requested: source=name")
            return PlaylistSelectionSignal.RETRY

        if self.ui.ask_create_playlist(name):
            logger.info("Target playlist creation requested: source=name")
            playlist = self.playlist_manager.create(name)
            logger.info(
                "Target playlist created: playlist_id=%s playlist_name=%s",
                playlist["id"],
                playlist["name"],
            )
            return playlist

        logger.info("Target playlist selection cancelled: source=name")
        return None

    def _handle_not_found_by_url(
        self,
    ) -> SpotifyPlaylist | PlaylistSelectionRetry | None:
        """Обработать отсутствие плейлиста при поиске по URL/URI."""
        if self.ui.ask_enter_another_playlist():
            logger.info("Target playlist selection retry requested: source=id")
            return PlaylistSelectionSignal.RETRY

        if self.ui.ask_create_playlist():
            logger.info("Target playlist creation requested: source=id")
            new_playlist_name = self.ui.ask_new_playlist_name()
            playlist = self.playlist_manager.create(new_playlist_name)
            logger.info(
                "Target playlist created: playlist_id=%s playlist_name=%s",
                playlist["id"],
                playlist["name"],
            )
            return playlist

        logger.info("Target playlist selection cancelled: source=id")
        return None
