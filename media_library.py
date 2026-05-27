from search import find_start_page_by_added_year


ADDED_YEAR = 2025
SAVED_TRACKS_PAGE_LIMIT = 50


def _get_saved_tracks_page(spotify, page_index: int) -> dict:
    return spotify.current_user_saved_tracks(
        limit=SAVED_TRACKS_PAGE_LIMIT,
        offset=page_index * SAVED_TRACKS_PAGE_LIMIT,
    )


def _collect_track_uris_starting_from_page(
    spotify,
    first_page: dict,
    start_page: int,
    year: int,
) -> list[str]:
    track_uris = []
    page_index = start_page

    while True:
        if page_index == 0:
            page = first_page
        else:
            page = _get_saved_tracks_page(spotify, page_index)

        for item in page.get("items", []):
            added_at = item["added_at"]
            added_year = int(added_at[:4])

            if added_year == year:
                track_uris.append(item["track"]["uri"])
            elif added_year < year:
                return track_uris

        if not page.get("next"):
            break

        page_index += 1

    return track_uris


def get_liked_track_uris_by_added_year(
    spotify,
    year: int = ADDED_YEAR,
) -> list[str]:
    """Return liked track URIs filtered by the year they were added."""
    first_page = _get_saved_tracks_page(spotify, 0)
    total = first_page["total"]

    if total == 0:
        return []

    start_page = find_start_page_by_added_year(
        lambda page_index: _get_saved_tracks_page(spotify, page_index),
        year,
        total,
        SAVED_TRACKS_PAGE_LIMIT,
    )

    if start_page is None:
        return []

    return _collect_track_uris_starting_from_page(spotify, first_page, start_page, year)
