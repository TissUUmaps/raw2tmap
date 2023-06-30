from os import PathLike
from pathlib import Path
from typing import BinaryIO, TextIO


def convert_raw_to_tmap(
    raw_file: str | PathLike | BinaryIO | TextIO,
    tmap_file: str | PathLike | BinaryIO | TextIO,
) -> None:
    if isinstance(raw_file, (str, PathLike)):
        with Path(raw_file).open("rb") as raw_file:
            return convert_raw_to_tmap(raw_file, tmap_file)
    if isinstance(tmap_file, (str, PathLike)):
        with Path(tmap_file).open("wb") as tmap_file:
            return convert_raw_to_tmap(raw_file, tmap_file)
    raise NotImplementedError()  # TODO
