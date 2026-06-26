from collections.abc import Mapping
import logging
from typing import Any

from api.errors import SpotifyResponseError
from api.types import (
    SpotifyPlaylist,
    SpotifyPlaylistItem,
    SpotifyPlaylistItemsPage,
    SpotifyPlaylistsPage,
    SpotifySavedTrackItem,
    SpotifySavedTracksPage,
    SpotifySnapshotResponse,
    SpotifyTrack,
    SpotifyUser,
)

logger = logging.getLogger(__name__)


def parse_user(raw: Any) -> SpotifyUser:
    """Проверить и нормализовать ответ текущего пользователя Spotify."""
    user = _require_mapping(raw, "user")
    return {
        "id": _require_str(user, "id", "user"),
        "display_name": _optional_str(user, "display_name", "user"),
    }


def parse_playlist(raw: Any) -> SpotifyPlaylist:
    """Проверить и нормализовать плейлист Spotify."""
    playlist = _require_mapping(raw, "playlist")
    return {
        "id": _require_str(playlist, "id", "playlist"),
        "name": _require_str(playlist, "name", "playlist"),
        "owner_id": _parse_owner_id(playlist.get("owner")),
        "spotify_url": _parse_spotify_url(playlist.get("external_urls")),
    }


def parse_saved_tracks_page(raw: Any) -> SpotifySavedTracksPage:
    """Проверить и нормализовать страницу любимых треков."""
    page = _require_mapping(raw, "saved tracks page")
    return {
        "items": [
            _parse_saved_track_item(item)
            for item in _require_list(page, "items", "saved tracks page")
        ],
        "total": _require_int(page, "total", "saved tracks page"),
        "next": _optional_next(page),
    }


def parse_playlist_items_page(raw: Any) -> SpotifyPlaylistItemsPage:
    """Проверить и нормализовать страницу треков плейлиста."""
    page = _require_mapping(raw, "playlist items page")
    return {
        "items": [
            _parse_playlist_item(item)
            for item in _require_list(page, "items", "playlist items page")
        ],
        "next": _optional_next(page),
    }


def parse_playlists_page(raw: Any) -> SpotifyPlaylistsPage:
    """Проверить и нормализовать страницу плейлистов пользователя."""
    page = _require_mapping(raw, "playlists page")
    return {
        "items": _parse_playlists_page_items(
            _require_list(page, "items", "playlists page"),
        ),
        "next": _optional_next(page),
    }


def parse_snapshot_response(raw: Any) -> SpotifySnapshotResponse:
    """Проверить ответ Spotify на изменение содержимого плейлиста."""
    response = _require_mapping(raw, "snapshot response")
    return {
        "snapshot_id": _require_str(response, "snapshot_id", "snapshot response"),
    }


def _parse_saved_track_item(raw: Any) -> SpotifySavedTrackItem:
    """Проверить и нормализовать элемент любимых треков."""
    item = _require_mapping(raw, "saved track item")
    return {
        "added_at": _require_str(item, "added_at", "saved track item"),
        "track": _parse_track(item.get("track"), "saved track item"),
    }


def _parse_track(raw: Any, context: str) -> SpotifyTrack:
    """Проверить и нормализовать трек с обязательным URI."""
    track = _require_mapping(raw, f"{context} track")
    return {
        "uri": _require_str(track, "uri", f"{context} track"),
    }


def _parse_playlist_item(raw: Any) -> SpotifyPlaylistItem:
    """Нормализовать элемент плейлиста, мягко пропуская невалидный трек."""
    if not isinstance(raw, Mapping):
        logger.debug("Playlist item skipped: item is not a mapping")
        return {"item": None}

    track = raw.get("item")
    if track is None:
        logger.debug("Playlist item skipped: track is missing")
        return {"item": None}

    if not isinstance(track, Mapping):
        logger.debug("Playlist item skipped: track is not a mapping")
        return {"item": None}

    track_uri = track.get("uri")
    if not isinstance(track_uri, str) or not track_uri:
        logger.debug("Playlist item skipped: track URI is missing")
        return {"item": None}

    return {"item": {"uri": track_uri}}


def _parse_playlists_page_items(raw_items: list[Any]) -> list[SpotifyPlaylist]:
    """Нормализовать список плейлистов, пропуская невалидные элементы."""
    playlists = []

    for index, item in enumerate(raw_items):
        try:
            playlists.append(parse_playlist(item))
        except SpotifyResponseError as error:
            logger.warning(
                "Invalid playlist skipped in playlists page: index=%s error=%s",
                index,
                error,
            )
            continue

    return playlists


def _parse_owner_id(raw: Any) -> str | None:
    """Вернуть id владельца плейлиста, если он доступен."""
    if not isinstance(raw, Mapping):
        return None

    owner_id = raw.get("id")
    if isinstance(owner_id, str) and owner_id:
        return owner_id

    return None


def _parse_spotify_url(raw: Any) -> str | None:
    """Вернуть Spotify URL ресурса, если он доступен."""
    if not isinstance(raw, Mapping):
        return None

    spotify_url = raw.get("spotify")
    if isinstance(spotify_url, str):
        return spotify_url

    return None


def _require_mapping(raw: Any, context: str) -> Mapping[str, Any]:
    """Проверить, что значение является словареподобным ответом."""
    if not isinstance(raw, Mapping):
        raise SpotifyResponseError(f"invalid {context}")

    return raw


def _require_str(raw: Mapping[str, Any], key: str, context: str) -> str:
    """Вернуть обязательную непустую строку из ответа."""
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise SpotifyResponseError(f"missing {key} in {context}")

    return value


def _require_int(raw: Mapping[str, Any], key: str, context: str) -> int:
    """Вернуть обязательное целое число из ответа."""
    value = raw.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise SpotifyResponseError(f"missing {key} in {context}")

    return value


def _optional_str(raw: Mapping[str, Any], key: str, context: str) -> str | None:
    """Вернуть опциональную строку или None."""
    value = raw.get(key)
    if value is None:
        return None

    if not isinstance(value, str):
        raise SpotifyResponseError(f"invalid {key} in {context}")

    return value


def _optional_next(raw: Mapping[str, Any]) -> str | None:
    """Нормализовать ссылку на следующую страницу."""
    next_url = raw.get("next")
    if isinstance(next_url, str):
        return next_url

    return None


def _require_list(raw: Mapping[str, Any], key: str, context: str) -> list[Any]:
    """Вернуть обязательный список из ответа."""
    value = raw.get(key)
    if isinstance(value, list):
        return value

    raise SpotifyResponseError(f"missing {key} in {context}")
