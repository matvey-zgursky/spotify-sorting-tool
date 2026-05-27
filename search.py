from collections.abc import Callable


PageGetter = Callable[[int], dict]


def _get_last_item_year(page: dict) -> int:
    return int(page["items"][-1]["added_at"][:4])


def _find_first_page_not_newer_than_year(
    get_page: PageGetter,
    year: int,
    total: int,
    page_limit: int,
) -> int | None:
    left_page = 0
    right_page = (total - 1) // page_limit
    result = None

    while left_page <= right_page:
        middle_page = (left_page + right_page) // 2
        page = get_page(middle_page)
        last_year = _get_last_item_year(page)

        if last_year > year:
            left_page = middle_page + 1
        else:
            result = middle_page
            right_page = middle_page - 1

    return result


def find_start_page_by_added_year(
    get_page: PageGetter,
    year: int,
    total: int,
    page_limit: int,
) -> int | None:
    if total <= page_limit:
        return 0

    return _find_first_page_not_newer_than_year(get_page, year, total, page_limit)
