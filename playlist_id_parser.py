from urllib.parse import urlparse


def parse_playlist_id(value: str) -> str | None:
    """Вернуть id плейлиста из Spotify URL/URI или None."""
    return _parse_playlist_id_from_uri(value) or _parse_playlist_id_from_url(value)


def _parse_playlist_id_from_uri(value: str) -> str | None:
    """Вернуть id плейлиста из Spotify URI или None."""
    if value.startswith("spotify:playlist:"):
        return value.removeprefix("spotify:playlist:").strip() or None

    return None


def _parse_playlist_id_from_url(value: str) -> str | None:
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
