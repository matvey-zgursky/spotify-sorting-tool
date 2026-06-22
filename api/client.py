import spotipy

from api.request_executor import call_spotify


class SpotifyClient:
    """Spotify-клиент с централизованной обработкой ошибок API."""

    def __init__(self, spotify: spotipy.Spotify) -> None:
        self.spotify = spotify

    def current_user(self) -> dict:
        """Вернуть текущего пользователя Spotify."""
        return call_spotify(self.spotify.current_user)

    def current_user_saved_tracks(self, limit: int, offset: int) -> dict:
        """Вернуть страницу любимых треков текущего пользователя."""
        return call_spotify(
            self.spotify.current_user_saved_tracks,
            limit=limit,
            offset=offset,
        )

    def playlist_add_items(self, playlist_id: str, items: list[str]) -> dict:
        """Добавить треки в плейлист."""
        return call_spotify(
            self.spotify.playlist_add_items,
            playlist_id=playlist_id,
            items=items,
        )

    def playlist_items(self, playlist_id: str, limit: int, offset: int) -> dict:
        """Вернуть страницу треков плейлиста."""
        return call_spotify(
            self.spotify.playlist_items,
            playlist_id=playlist_id,
            limit=limit,
            offset=offset,
        )

    def current_user_playlists(self, limit: int, offset: int) -> dict:
        """Вернуть страницу плейлистов текущего пользователя."""
        return call_spotify(
            self.spotify.current_user_playlists,
            limit=limit,
            offset=offset,
        )

    def current_user_playlist_create(self, name: str, public: bool) -> dict:
        """Создать плейлист для текущего пользователя."""
        return call_spotify(
            self.spotify.current_user_playlist_create,
            name=name,
            public=public,
        )
