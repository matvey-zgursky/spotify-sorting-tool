import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Authenticator:
    """Настраивает OAuth и создает клиент Spotify."""

    SCOPES = (
        "user-library-read "
        "user-library-modify "
        "playlist-read-private "
        "playlist-modify-private "
        "playlist-modify-public"
    )
    TOKEN_CACHE_PATH = ".spotify_token_cache"

    def validate_settings(self) -> None:
        """Проверить наличие обязательных настроек Spotify OAuth."""
        missing_vars = [
            name
            for name in (
                "SPOTIPY_CLIENT_ID",
                "SPOTIPY_CLIENT_SECRET",
                "SPOTIPY_REDIRECT_URI",
            )
            if not os.getenv(name)
        ]
        if missing_vars:
            raise RuntimeError(
                "Missing Spotify settings in .env: " + ", ".join(missing_vars)
            )

    def create_client(self) -> spotipy.Spotify:
        """Создать авторизованный клиент Spotify API."""
        self.validate_settings()
        auth_manager = SpotifyOAuth(
            scope=self.SCOPES,
            cache_path=self.TOKEN_CACHE_PATH,
            open_browser=False,
        )
        return spotipy.Spotify(auth_manager=auth_manager)
