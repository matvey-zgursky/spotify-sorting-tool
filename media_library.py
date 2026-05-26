from search import find_start_page_by_added_year


ADDED_YEAR = 2025
PAGE_LIMIT = 50


def _get_saved_tracks_page(spotify, page_index: int) -> dict:
    return spotify.current_user_saved_tracks(
        limit=PAGE_LIMIT,
        offset=page_index * PAGE_LIMIT,
    )


def _get_page_for_collection(spotify, first_page: dict, page_index: int) -> dict:
    if page_index == 0:
        return first_page

    return _get_saved_tracks_page(spotify, page_index)


def _collect_track_uris_from_page(
    spotify,
    first_page: dict,
    start_page: int,
    year: int,
) -> list[str]:
    track_uris = []
    page_index = start_page

    while True:
        saved_tracks = _get_page_for_collection(spotify, first_page, page_index)

        for item in saved_tracks.get("items", []):
            added_at = item["added_at"]
            added_year = int(added_at[:4])

            if added_year == year:
                track_uris.append(item["track"]["uri"])
            elif added_year < year:
                return track_uris

        if not saved_tracks.get("next"):
            break

        page_index += 1

    return track_uris


def get_liked_track_uris_by_added_year(
    spotify,
    year: int = ADDED_YEAR,
) -> list[str]:
    """Return liked track URIs filtered by the year they were added."""
    first_page = _get_saved_tracks_page(spotify, 0)
    total = first_page.get("total", 0)

    if total == 0 or not first_page.get("items"):
        return []

    start_page = find_start_page_by_added_year(
        lambda page_index: _get_saved_tracks_page(spotify, page_index),
        year,
        total,
        PAGE_LIMIT,
    )

    if start_page is None:
        return []

    return _collect_track_uris_from_page(spotify, first_page, start_page, year)
