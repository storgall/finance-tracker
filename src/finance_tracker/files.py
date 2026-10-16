from pathlib import Path


def expand_paths(paths: list[Path], expand_subfolders: bool = False) -> list[Path]:
    """Turn the paths given on the command line into the list of statement files to read.

    Each path is either a file, which is kept as it is, or a folder, which is replaced by
    the XML files it contains.

    Args:
        paths: files and folders, in the order the user typed them.
        expand_subfolders: when ``True``, the subfolders of a folder are searched too, at any
            depth. By default only the files directly in the folder are used.

    Returns:
        The files to read. The order of ``paths`` is kept. Inside a folder the entries are
        sorted by name (Moneta file names contain the date, so this is roughly chronological);
        the content of a subfolder comes at the place of that subfolder in the sorted entries.

    Raises:
        FileNotFoundError: if a path does not exist (the message names it).
        ValueError: if a folder from ``paths`` contains no XML file, not even in its
            subfolders when ``expand_subfolders`` is set (the message names the folder).
            Importing nothing is almost certainly a mistake.

    Requirements:
        * a file path is returned unchanged, whatever its extension
        * from a folder only files with the extension ``.xml`` are taken, regardless of
          letter case (``.XML`` too); other files are silently skipped
        * a subfolder without XML files is ignored; it never causes an error by itself
        * files and folders can be mixed; an empty ``paths`` list gives an empty list
    """

    result: list[Path] = []
    for path in paths:
        if path.is_file():
            result.append(path)

        elif path.is_dir():
            result += _xml_files_in(path, expand_subfolders)

        elif not path.exists():
            raise FileNotFoundError(f"Path not found: {path}")

    return result


def _xml_files_in(folder: Path, expand_subfolders: bool, subfolder: bool = False) -> list[Path]:
    """Collect the XML files of ``folder`` (and of its subfolders if ``expand_subfolders``).

    Args:
        folder: the folder to read.
        expand_subfolders: also descend into subfolders.
        subfolder: ``True`` when ``folder`` was reached by descending from the folder the user
            gave. Such a folder may be empty; only the folder the user gave must not be.

    Raises:
        ValueError: if nothing was found and ``folder`` is not a subfolder.
    """
    result: list[Path] = []
    for file in sorted(folder.iterdir()):
        if file.is_file() and file.suffix.lower() == ".xml":
            result.append(file)
        if expand_subfolders and file.is_dir():
            result += _xml_files_in(file, expand_subfolders, subfolder=True)

    if result or subfolder:
        return result

    raise ValueError(f"No xml file at '{folder}'")
