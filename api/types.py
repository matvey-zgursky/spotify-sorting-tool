from typing import NotRequired, TypedDict


class SpotifyUser(TypedDict):
    """Минимальные данные текущего пользователя Spotify."""

    id: str
    display_name: NotRequired[str | None]


class SpotifyPlaylistOwner(TypedDict):
    """Минимальные данные владельца плейлиста."""

    id: str


class SpotifyExternalUrls(TypedDict):
    """Внешние URL Spotify-ресурса."""

    spotify: NotRequired[str]


class SpotifyPlaylist(TypedDict):
    """Минимальные данные плейлиста, используемые приложением."""

    id: str
    name: str
    owner: NotRequired[SpotifyPlaylistOwner]
    external_urls: NotRequired[SpotifyExternalUrls]


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
    next: NotRequired[str | None]


class SpotifyPlaylistItem(TypedDict):
    """Элемент страницы треков плейлиста."""

    item: NotRequired[SpotifyTrack | None]


class SpotifyPlaylistItemsPage(TypedDict):
    """Страница треков плейлиста."""

    items: list[SpotifyPlaylistItem]
    next: NotRequired[str | None]


class SpotifyPlaylistsPage(TypedDict):
    """Страница плейлистов пользователя."""

    items: list[SpotifyPlaylist]
    next: NotRequired[str | None]


class SpotifySnapshotResponse(TypedDict):
    """Ответ Spotify на изменение содержимого плейлиста."""

    snapshot_id: str
