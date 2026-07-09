class SpotifyAppError(Exception):
    """Ошибка Spotify, которую можно показать пользователю."""


class SpotifySettingsError(SpotifyAppError):
    """Не заполнены или некорректны обязательные настройки Spotify OAuth."""

    def __init__(self, invalid_vars: list[str]) -> None:
        super().__init__(
            "Missing or invalid Spotify settings in .env: "
            + ", ".join(invalid_vars)
        )
