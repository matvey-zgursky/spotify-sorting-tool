import logging
import os

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from api.client import SpotifyClient
from errors import SpotifySettingsError

logger = logging.getLogger(__name__)


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
        """Проверить корректность env настроек Spotify OAuth."""
        logger.info("Spotify settings validation started")
        invalid_vars = [
            name
            for name in (
                "SPOTIPY_CLIENT_ID",
                "SPOTIPY_CLIENT_SECRET",
                "SPOTIPY_REDIRECT_URI",
            )
            if not (os.getenv(name) or "").strip()
        ]
        if invalid_vars:
            logger.error(
                "Spotify settings validation failed: invalid_vars=%s",
                ", ".join(invalid_vars),
            )
            raise SpotifySettingsError(invalid_vars)

        logger.info("Spotify settings validation completed")

    def create_client(self) -> SpotifyClient:
        """Создать авторизованный клиент Spotify API."""
        logger.info("Spotify client creation started")
        self.validate_settings()
        auth_manager = SpotifyOAuth(
            scope=self.SCOPES,
            cache_path=self.TOKEN_CACHE_PATH,
            open_browser=False,
        )
        spotify_client = SpotifyClient(spotipy.Spotify(auth_manager=auth_manager))
        logger.info("Spotify client created")
        return spotify_client
