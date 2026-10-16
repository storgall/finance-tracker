from datetime import date, timedelta

import pytest

from finance_tracker.periods import GRANULARITIES, period_key

DAY = date(2026, 9, 3)


def test_granularities_are_listed_from_longest_to_shortest() -> None:
    assert GRANULARITIES == ("year", "quarter", "month", "week", "day")


def test_year() -> None:
    assert period_key(DAY, "year") == "2026"


def test_day_is_the_iso_date() -> None:
    assert period_key(DAY, "day") == "2026-09-03"


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 1, 1), "2026-01"),
        (date(2026, 9, 30), "2026-09"),
        (date(2026, 10, 1), "2026-10"),
        (date(2026, 12, 31), "2026-12"),
    ],
)
def test_month_has_two_digits(day: date, expected: str) -> None:
    assert period_key(day, "month") == expected


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 1, 1), "2026-Q1"),
        (date(2026, 3, 31), "2026-Q1"),
        (date(2026, 4, 1), "2026-Q2"),
        (date(2026, 6, 30), "2026-Q2"),
        (date(2026, 7, 1), "2026-Q3"),
        (date(2026, 9, 30), "2026-Q3"),
        (date(2026, 10, 1), "2026-Q4"),
        (date(2026, 12, 31), "2026-Q4"),
    ],
)
def test_quarter_boundaries(day: date, expected: str) -> None:
    assert period_key(day, "quarter") == expected


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 9, 3), "2026-W36"),
        (date(2026, 1, 1), "2026-W01"),  # Thursday: week 1 of 2026
        (date(2026, 1, 4), "2026-W01"),  # Sunday: still week 1
        (date(2026, 1, 5), "2026-W02"),  # Monday starts the next week
        (date(2026, 2, 2), "2026-W06"),  # a single-digit week is padded with a zero
    ],
)
def test_week_is_iso_and_has_two_digits(day: date, expected: str) -> None:
    assert period_key(day, "week") == expected


@pytest.mark.parametrize(
    ("day", "expected"),
    [
        (date(2026, 12, 31), "2026-W53"),  # 2026 has 53 ISO weeks
        (date(2027, 1, 1), "2026-W53"),  # January 1st that still belongs to the old ISO year
        (date(2024, 12, 30), "2025-W01"),  # December that already belongs to the next ISO year
        (date(2021, 1, 3), "2020-W53"),  # a Sunday that belongs to the previous ISO year
    ],
)
def test_week_uses_the_iso_year_around_new_year(day: date, expected: str) -> None:
    assert period_key(day, "week") == expected


@pytest.mark.parametrize("granularity", GRANULARITIES)
def test_days_of_the_same_period_share_a_label(granularity: str) -> None:
    same_period = {
        "year": (date(2026, 1, 1), date(2026, 12, 31)),
        "quarter": (date(2026, 7, 1), date(2026, 9, 30)),
        "month": (date(2026, 9, 1), date(2026, 9, 30)),
        "week": (date(2026, 9, 7), date(2026, 9, 13)),  # Monday to Sunday
        "day": (date(2026, 9, 3), date(2026, 9, 3)),
    }
    first, last = same_period[granularity]

    assert period_key(first, granularity) == period_key(last, granularity)


@pytest.mark.parametrize("granularity", GRANULARITIES)
def test_the_next_period_gets_a_different_label(granularity: str) -> None:
    last_day_of = {
        "year": (date(2026, 12, 31), date(2027, 1, 1)),
        "quarter": (date(2026, 9, 30), date(2026, 10, 1)),
        "month": (date(2026, 9, 30), date(2026, 10, 1)),
        "week": (date(2026, 9, 13), date(2026, 9, 14)),  # Sunday, then Monday
        "day": (date(2026, 9, 3), date(2026, 9, 4)),
    }
    before, after = last_day_of[granularity]

    assert period_key(before, granularity) != period_key(after, granularity)


@pytest.mark.parametrize("granularity", GRANULARITIES)
def test_labels_sort_chronologically_as_strings(granularity: str) -> None:
    days = [date(2024, 11, 1) + timedelta(days=n) for n in range(0, 800)]

    labels = [period_key(day, granularity) for day in days]

    assert labels == sorted(labels)


@pytest.mark.parametrize("granularity", ["decade", "Year", "", "months"])
def test_unknown_granularity_raises_value_error_naming_it(granularity: str) -> None:
    with pytest.raises(ValueError) as exc_info:
        period_key(DAY, granularity)

    message = str(exc_info.value)
    assert granularity in message
    assert "granularity" in message.lower()
