from errors import SpotifyAppError


class SpotifyAuthorizationError(SpotifyAppError):
    """Авторизация Spotify истекла или недействительна."""

    def __init__(self) -> None:
        super().__init__(
            "Spotify authorization expired or is invalid. "
            "Delete .spotify_token_cache and run the app again."
        )


class SpotifyPermissionError(SpotifyAppError):
    """Spotify запретил выполнение действия."""

    def __init__(self) -> None:
        super().__init__(
            "Spotify denied access. Check that your account has permission "
            "for this action."
        )


class SpotifyResourceNotFoundError(SpotifyAppError):
    """Запрошенный ресурс Spotify не найден."""

    def __init__(self) -> None:
        super().__init__(
            "Spotify resource was not found. It may have been deleted "
            "or become unavailable."
        )


class SpotifyRateLimitError(SpotifyAppError):
    """Spotify ограничил частоту запросов."""

    def __init__(self) -> None:
        super().__init__(
            "Spotify rate limit exceeded. Please wait and try again later."
        )


class SpotifyServerError(SpotifyAppError):
    """Spotify временно недоступен."""

    def __init__(self) -> None:
        super().__init__(
            "Spotify API is temporarily unavailable. Please try again later."
        )


class SpotifyNetworkError(SpotifyAppError):
    """Не удалось связаться со Spotify."""

    def __init__(self) -> None:
        super().__init__(
            "Could not reach Spotify. Check your internet connection " "and try again."
        )
