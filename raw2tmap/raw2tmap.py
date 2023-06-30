from os import PathLike
from pathlib import Path
from typing import BinaryIO


def convert_raw_to_tmap(
    raw_file: str | PathLike | BinaryIO,
    tmap_file: str | PathLike | BinaryIO,
) -> None:
    if isinstance(raw_file, (str, PathLike)):
        with Path(raw_file).open("rb") as raw_file:
            return convert_raw_to_tmap(raw_file, tmap_file)
    assert isinstance(raw_file, BinaryIO)
    if isinstance(tmap_file, (str, PathLike)):
        with Path(tmap_file).open("wb") as tmap_file:
            return convert_raw_to_tmap(raw_file, tmap_file)
    assert isinstance(tmap_file, BinaryIO)
    raise NotImplementedError()  # TODO
