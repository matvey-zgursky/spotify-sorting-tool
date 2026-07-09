import spotipy

from .parsers import (
    parse_playlist,
    parse_playlist_items_page,
    parse_playlists_page,
    parse_saved_tracks_page,
    parse_user,
)
from .request_executor import call_spotify
from .types import (
    SpotifyPlaylist,
    SpotifyPlaylistItemsPage,
    SpotifyPlaylistsPage,
    SpotifySavedTracksPage,
    SpotifyUser,
)


class SpotifyClient:
    """Spotify-клиент с централизованной обработкой ошибок API."""

    def __init__(self, spotify: spotipy.Spotify) -> None:
        self.spotify = spotify

    def current_user(self) -> SpotifyUser:
        """Вернуть текущего пользователя Spotify."""
        raw_user = call_spotify(self.spotify.current_user)
        return parse_user(raw_user)

    def current_user_saved_tracks(
        self,
        limit: int,
        offset: int,
    ) -> SpotifySavedTracksPage:
        """Вернуть страницу любимых треков текущего пользователя."""
        raw_page = call_spotify(
            self.spotify.current_user_saved_tracks,
            limit=limit,
            offset=offset,
        )
        return parse_saved_tracks_page(raw_page)

    def playlist_add_items(
        self,
        playlist_id: str,
        items: list[str],
    ) -> None:
        """Добавить треки в плейлист."""
        call_spotify(
            self.spotify.playlist_add_items,
            playlist_id=playlist_id,
            items=items,
        )

    def current_user_saved_tracks_delete(self, tracks: list[str]) -> None:
        """Удалить треки из любимых треков текущего пользователя."""
        call_spotify(
            self.spotify.current_user_saved_tracks_delete,
            tracks=tracks,
        )

    def playlist_items(
        self,
        playlist_id: str,
        limit: int,
        offset: int,
    ) -> SpotifyPlaylistItemsPage:
        """Вернуть страницу треков плейлиста."""
        raw_page = call_spotify(
            self.spotify.playlist_items,
            playlist_id=playlist_id,
            limit=limit,
            offset=offset,
        )
        return parse_playlist_items_page(raw_page)

    def current_user_playlists(
        self,
        limit: int,
        offset: int,
    ) -> SpotifyPlaylistsPage:
        """Вернуть страницу плейлистов текущего пользователя."""
        raw_page = call_spotify(
            self.spotify.current_user_playlists,
            limit=limit,
            offset=offset,
        )
        return parse_playlists_page(raw_page)

    def current_user_playlist_create(
        self,
        name: str,
        public: bool,
    ) -> SpotifyPlaylist:
        """Создать плейлист для текущего пользователя."""
        raw_playlist = call_spotify(
            self.spotify.current_user_playlist_create,
            name=name,
            public=public,
        )
        return parse_playlist(raw_playlist)
