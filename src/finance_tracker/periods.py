from datetime import date

GRANULARITIES = ("year", "quarter", "month", "week", "day")
"""The periods the overview can be split into, from the longest to the shortest."""


def period_key(day: date, granularity: str) -> str:
    """Return the label of the period that ``day`` belongs to.

    Args:
        day: the date of a transaction.
        granularity: one of ``GRANULARITIES``.

    Returns:
        A label that also sorts chronologically as a plain string:

        * ``"year"``:    ``2026``
        * ``"quarter"``: ``2026-Q3``
        * ``"month"``:   ``2026-09`` (the month is always two digits)
        * ``"week"``:    ``2026-W36`` (ISO week, always two digits)
        * ``"day"``:     ``2026-09-03`` (ISO date)

    Raises:
        ValueError: if ``granularity`` is not one of ``GRANULARITIES`` (the message names it).

    Requirements:
        * quarters are 1-3 = Q1, 4-6 = Q2, 7-9 = Q3, 10-12 = Q4
        * weeks follow ISO 8601: a week starts on Monday and belongs to the year that holds
          its Thursday. So the last days of December can be in week 1 of the next year and
          the first days of January in week 52 or 53 of the previous year; the year in the
          label is the ISO year, not the calendar year of ``day``
    """

    match granularity:
        case "year":
            return str(day.year)
        case "quarter":
            return f"{day.year}-Q{(day.month + 2) // 3}"
        case "month":
            return f"{day.year}-{day.month:02d}"
        case "week":
            iso = day.isocalendar()
            return f"{iso.year}-W{iso.week:02d}"
        case "day":
            return day.isoformat()

    raise ValueError(f"Granularity {granularity!r} not supported, allowed values: {GRANULARITIES}")
