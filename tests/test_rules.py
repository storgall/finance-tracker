from pathlib import Path

import pytest

from finance_tracker.rules import load_rules

FIXTURE = Path(__file__).parent / "fixtures" / "rules.toml"
FIXTURE_WITH_IGNORE = Path(__file__).parent / "fixtures" / "rules_with_ignore.toml"


def write_toml(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "rules.toml"
    path.write_text(content, encoding="utf-8")
    return path


def test_loads_categories_and_keywords() -> None:
    rules = load_rules(FIXTURE).categories

    assert rules == {
        "Groceries": ["test market", "fake grocer"],
        "Rent": ["nájem"],
        "Streaming": ["fake streaming"],
    }


def test_keeps_file_order_as_priority() -> None:
    assert list(load_rules(FIXTURE).categories) == ["Groceries", "Rent", "Streaming"]


def test_empty_rules_table_returns_empty_dict(tmp_path: Path) -> None:
    assert load_rules(write_toml(tmp_path, "[rules]\n")).categories == {}


def test_missing_file_raises_file_not_found_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_rules(tmp_path / "does_not_exist.toml")


def test_invalid_toml_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, "[rules\nGroceries = ")

    with pytest.raises(ValueError, match="Failed to parse"):
        load_rules(path)


def test_missing_rules_table_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, '[other]\nGroceries = ["market"]\n')

    with pytest.raises(ValueError, match="rules"):
        load_rules(path)


def test_rules_that_is_not_a_table_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, "rules = 5\n")

    with pytest.raises(ValueError, match="rules"):
        load_rules(path)


@pytest.mark.parametrize(
    "line",
    [
        'Groceries = "market"',  # a string instead of a list
        "Groceries = [1, 2]",  # a list of numbers
        'Groceries = ["market", 3]',  # one bad item is enough
    ],
)
def test_keywords_that_are_not_a_list_of_strings_raise_value_error(
    tmp_path: Path, line: str
) -> None:
    path = write_toml(tmp_path, f"[rules]\n{line}\n")

    with pytest.raises(ValueError, match="Groceries"):
        load_rules(path)


def test_file_without_ignore_section_has_no_ignored_keywords() -> None:
    assert load_rules(FIXTURE).ignore == []


def test_loads_ignored_keywords() -> None:
    rule_set = load_rules(FIXTURE_WITH_IGNORE)

    assert rule_set.ignore == ["fake savings", "999999999/0600"]
    assert rule_set.categories == {"Groceries": ["test market"]}


def test_ignore_section_without_keywords_means_nothing_is_ignored(tmp_path: Path) -> None:
    path = write_toml(tmp_path, '[rules]\nGroceries = ["market"]\n\n[ignore]\n')

    assert load_rules(path).ignore == []


def test_ignore_section_alone_is_not_enough(tmp_path: Path) -> None:
    path = write_toml(tmp_path, '[ignore]\nkeywords = ["savings"]\n')

    with pytest.raises(ValueError, match="rules"):
        load_rules(path)


def test_ignore_that_is_not_a_table_raises_value_error(tmp_path: Path) -> None:
    path = write_toml(tmp_path, "ignore = 5\n\n[rules]\n")

    with pytest.raises(ValueError, match="ignore"):
        load_rules(path)


@pytest.mark.parametrize(
    "line",
    [
        'keywords = "savings"',  # a string instead of a list
        "keywords = [1, 2]",  # a list of numbers
        'keywords = ["savings", 3]',  # one bad item is enough
    ],
)
def test_ignored_keywords_that_are_not_a_list_of_strings_raise_value_error(
    tmp_path: Path, line: str
) -> None:
    path = write_toml(tmp_path, f"[rules]\n\n[ignore]\n{line}\n")

    with pytest.raises(ValueError, match="ignore"):
        load_rules(path)
