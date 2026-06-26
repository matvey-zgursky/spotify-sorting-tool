from typing import TypedDict


class SpotifyUser(TypedDict):
    """Минимальные данные текущего пользователя Spotify."""

    id: str
    display_name: str | None


class SpotifyPlaylist(TypedDict):
    """Минимальные данные плейлиста, используемые приложением."""

    id: str
    name: str
    owner_id: str | None
    spotify_url: str | None


class SpotifyTrack(TypedDict):
    """Минимальные данные трека Spotify."""

    uri: str


class SpotifySavedTrackItem(TypedDict):
    """Элемент страницы любимых треков."""

    added_at: str
    track: SpotifyTrack


class SpotifySavedTracksPage(TypedDict):
    """Страница любимых треков пользователя."""

    items: list[SpotifySavedTrackItem]
    total: int
    next: str | None


class SpotifyPlaylistItem(TypedDict):
    """Элемент страницы треков плейлиста."""

    item: SpotifyTrack | None


class SpotifyPlaylistItemsPage(TypedDict):
    """Страница треков плейлиста."""

    items: list[SpotifyPlaylistItem]
    next: str | None


class SpotifyPlaylistsPage(TypedDict):
    """Страница плейлистов пользователя."""

    items: list[SpotifyPlaylist]
    next: str | None


class SpotifySnapshotResponse(TypedDict):
    """Ответ Spotify на изменение содержимого плейлиста."""

    snapshot_id: str
