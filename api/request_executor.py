from collections.abc import Callable
import logging
from time import sleep
from typing import Any, TypeVar

import requests
from spotipy.exceptions import SpotifyException

from api.errors import (
    SpotifyAppError,
    SpotifyAuthorizationError,
    SpotifyNetworkError,
    SpotifyPermissionError,
    SpotifyRateLimitError,
    SpotifyResourceNotFoundError,
    SpotifyServerError,
)

MAX_RETRIES = 3
DEFAULT_RETRY_AFTER_SECONDS = 1

T = TypeVar("T")

logger = logging.getLogger(__name__)


def call_spotify(
    operation: Callable[..., T],
    *args: Any,
    **kwargs: Any,
) -> T:
    """Выполнить Spotify API-вызов с повторами и понятными ошибками."""
    operation_name = _get_operation_name(operation)

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = operation(*args, **kwargs)
            logger.debug(
                "Spotify API request succeeded: operation=%s",
                operation_name,
            )
            return result
        except SpotifyException as error:
            if _should_retry_spotify_error(error, attempt):
                sleep(_get_retry_delay(error, attempt))
            else:
                logger.error(
                    "Spotify API request failed: operation=%s status=%s",
                    operation_name,
                    getattr(error, "http_status", None),
                )
                raise _map_spotify_error(error) from error
        except requests.exceptions.RequestException as error:
            if attempt < MAX_RETRIES:
                sleep(_get_backoff_delay(attempt))
            else:
                logger.error(
                    "Spotify API network request failed: operation=%s error=%s",
                    operation_name,
                    error.__class__.__name__,
                )
                raise SpotifyNetworkError() from error

    raise SpotifyServerError()


def _get_operation_name(operation: Callable[..., Any]) -> str:
    """Вернуть безопасное имя операции без аргументов вызова."""
    return getattr(operation, "__name__", operation.__class__.__name__)


def _should_retry_spotify_error(error: SpotifyException, attempt: int) -> bool:
    """Проверить, стоит ли повторить запрос после ошибки Spotify."""
    status = getattr(error, "http_status", None)
    return attempt < MAX_RETRIES and (status == 429 or _is_server_error(status))


def _map_spotify_error(error: SpotifyException) -> SpotifyAppError:
    """Преобразовать ошибку spotipy в ошибку приложения."""
    status = getattr(error, "http_status", None)

    if status == 401:
        return SpotifyAuthorizationError()
    if status == 403:
        return SpotifyPermissionError()
    if status == 404:
        return SpotifyResourceNotFoundError()
    if status == 429:
        return SpotifyRateLimitError()
    if _is_server_error(status):
        return SpotifyServerError()

    return SpotifyAppError(f"Spotify request failed: {error}")


def _get_retry_delay(error: SpotifyException, attempt: int) -> float:
    """Вернуть задержку перед повтором с учетом Retry-After."""
    retry_after = _get_retry_after(error)
    if retry_after is not None:
        return retry_after

    return _get_backoff_delay(attempt)


def _get_retry_after(error: SpotifyException) -> float | None:
    """Прочитать Retry-After из ошибки Spotify, если он доступен."""
    headers = getattr(error, "headers", None) or {}
    retry_after = headers.get("Retry-After") or headers.get("retry-after")
    if retry_after is None:
        return None

    try:
        return max(float(retry_after), 0)
    except (TypeError, ValueError):
        return None


def _get_backoff_delay(attempt: int) -> float:
    """Вернуть короткую возрастающую задержку перед повтором."""
    return DEFAULT_RETRY_AFTER_SECONDS * attempt


def _is_server_error(status: int | None) -> bool:
    """Проверить, является ли HTTP-статус ошибкой сервера Spotify."""
    return status is not None and 500 <= status < 600
