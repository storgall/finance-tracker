from pathlib import Path

import pytest

from finance_tracker.files import expand_paths


def touch(*paths: Path) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<statement/>", encoding="utf-8")


def test_no_paths_give_no_files() -> None:
    assert expand_paths([]) == []


def test_file_is_returned_unchanged(tmp_path: Path) -> None:
    file = tmp_path / "a.xml"
    touch(file)

    assert expand_paths([file]) == [file]


def test_file_with_other_extension_is_kept_when_given_explicitly(tmp_path: Path) -> None:
    file = tmp_path / "statement.txt"
    touch(file)

    assert expand_paths([file]) == [file]


def test_folder_is_replaced_by_its_xml_files_sorted_by_name(tmp_path: Path) -> None:
    touch(
        tmp_path / "STM_20261001.xml", tmp_path / "STM_20260901.xml", tmp_path / "STM_20260915.xml"
    )

    result = expand_paths([tmp_path])

    assert result == [
        tmp_path / "STM_20260901.xml",
        tmp_path / "STM_20260915.xml",
        tmp_path / "STM_20261001.xml",
    ]


def test_xml_extension_is_matched_regardless_of_letter_case(tmp_path: Path) -> None:
    touch(tmp_path / "a.XML", tmp_path / "b.xml", tmp_path / "c.Xml")

    assert [p.name for p in expand_paths([tmp_path])] == ["a.XML", "b.xml", "c.Xml"]


def test_other_files_in_a_folder_are_skipped(tmp_path: Path) -> None:
    touch(tmp_path / "a.xml", tmp_path / "notes.txt", tmp_path / "b.pdf", tmp_path / "noext")

    assert expand_paths([tmp_path]) == [tmp_path / "a.xml"]


def test_subfolders_are_not_searched(tmp_path: Path) -> None:
    touch(tmp_path / "a.xml", tmp_path / "older" / "b.xml")

    assert expand_paths([tmp_path]) == [tmp_path / "a.xml"]


def test_folder_named_like_an_xml_file_is_not_taken_as_a_file(tmp_path: Path) -> None:
    touch(tmp_path / "a.xml")
    (tmp_path / "trap.xml").mkdir()

    assert expand_paths([tmp_path]) == [tmp_path / "a.xml"]


def test_files_and_folders_can_be_mixed_and_keep_the_given_order(tmp_path: Path) -> None:
    folder = tmp_path / "folder"
    touch(folder / "b.xml", folder / "a.xml", tmp_path / "x.xml", tmp_path / "y.xml")

    result = expand_paths([tmp_path / "y.xml", folder, tmp_path / "x.xml"])

    assert result == [
        tmp_path / "y.xml",
        folder / "a.xml",
        folder / "b.xml",
        tmp_path / "x.xml",
    ]


def test_missing_path_raises_file_not_found_error_naming_it(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing.xml"):
        expand_paths([tmp_path / "missing.xml"])


def test_missing_path_among_valid_ones_still_raises(tmp_path: Path) -> None:
    touch(tmp_path / "a.xml")

    with pytest.raises(FileNotFoundError, match="missing"):
        expand_paths([tmp_path / "a.xml", tmp_path / "missing"])


def test_empty_folder_raises_value_error_naming_it(tmp_path: Path) -> None:
    folder = tmp_path / "empty_dir"
    folder.mkdir()

    with pytest.raises(ValueError, match="empty_dir"):
        expand_paths([folder])


def test_folder_without_xml_files_raises_value_error(tmp_path: Path) -> None:
    folder = tmp_path / "only_pdf"
    touch(folder / "a.pdf", folder / "b.txt")

    with pytest.raises(ValueError, match="only_pdf"):
        expand_paths([folder])


def test_subfolders_are_searched_in_place_when_expanding_subfolders(tmp_path: Path) -> None:
    touch(tmp_path / "a.xml", tmp_path / "b_sub" / "x.xml", tmp_path / "c.xml")

    result = expand_paths([tmp_path], expand_subfolders=True)

    assert result == [tmp_path / "a.xml", tmp_path / "b_sub" / "x.xml", tmp_path / "c.xml"]


def test_nested_subfolders_are_searched_at_any_depth(tmp_path: Path) -> None:
    touch(tmp_path / "one" / "two" / "deep.xml", tmp_path / "top.xml")

    result = expand_paths([tmp_path], expand_subfolders=True)

    assert result == [tmp_path / "one" / "two" / "deep.xml", tmp_path / "top.xml"]


def test_files_in_subfolders_are_filtered_the_same_way(tmp_path: Path) -> None:
    touch(tmp_path / "sub" / "a.XML", tmp_path / "sub" / "notes.txt")

    assert expand_paths([tmp_path], expand_subfolders=True) == [tmp_path / "sub" / "a.XML"]


def test_empty_subfolder_is_ignored_when_expanding_subfolders(tmp_path: Path) -> None:
    touch(tmp_path / "a.xml")
    (tmp_path / "empty").mkdir()

    assert expand_paths([tmp_path], expand_subfolders=True) == [tmp_path / "a.xml"]


def test_subfolder_without_xml_files_is_ignored_when_expanding_subfolders(
    tmp_path: Path,
) -> None:
    touch(tmp_path / "a.xml", tmp_path / "docs" / "readme.txt")

    assert expand_paths([tmp_path], expand_subfolders=True) == [tmp_path / "a.xml"]


def test_folder_with_xml_only_in_a_subfolder_is_fine_when_expanding_subfolders(
    tmp_path: Path,
) -> None:
    touch(tmp_path / "sub" / "a.xml")

    assert expand_paths([tmp_path], expand_subfolders=True) == [tmp_path / "sub" / "a.xml"]


def test_the_same_folder_without_expanding_subfolders_has_no_xml_and_fails(
    tmp_path: Path,
) -> None:
    touch(tmp_path / "sub" / "a.xml")

    with pytest.raises(ValueError, match=tmp_path.name):
        expand_paths([tmp_path])


def test_folder_without_xml_anywhere_still_fails_when_expanding_subfolders(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "nothing"
    touch(folder / "sub" / "notes.txt")

    with pytest.raises(ValueError, match="nothing"):
        expand_paths([folder], expand_subfolders=True)
