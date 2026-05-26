ADDED_YEAR = 2025
PAGE_LIMIT = 50


def _get_saved_tracks_page(spotify, page_index: int) -> dict:
    return spotify.current_user_saved_tracks(
        limit=PAGE_LIMIT,
        offset=page_index * PAGE_LIMIT,
    )


def _get_last_item_year(page: dict) -> int:
    return int(page["items"][-1]["added_at"][:4])


def _find_first_page_with_year_at_most(
    spotify,
    year: int,
    total: int,
) -> int | None:
    left_page = 0
    right_page = (total - 1) // PAGE_LIMIT
    result = None

    while left_page <= right_page:
        middle_page = (left_page + right_page) // 2
        page = _get_saved_tracks_page(spotify, middle_page)
        last_year = _get_last_item_year(page)

        if last_year > year:
            left_page = middle_page + 1
        else:
            result = middle_page
            right_page = middle_page - 1

    return result


def get_liked_track_uris_by_added_year(
    spotify,
    year: int = ADDED_YEAR,
) -> list[str]:
    """Return liked track URIs filtered by the year they were added."""
    track_uris = []
    first_page = _get_saved_tracks_page(spotify, 0)
    total = first_page.get("total", 0)

    if total == 0 or not first_page.get("items"):
        return track_uris

    if total <= PAGE_LIMIT:
        start_page = 0
    else:
        start_page = _find_first_page_with_year_at_most(spotify, year, total)

    if start_page is None:
        return track_uris

    page_index = start_page
    while True:
        if page_index == 0:
            saved_tracks = first_page
        else:
            saved_tracks = _get_saved_tracks_page(spotify, page_index)

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
