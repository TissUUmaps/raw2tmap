from os import PathLike
from pathlib import Path


def convert_raw_to_tmap(raw_file: str | PathLike, tmap_file: str | PathLike) -> None:
    raw_file = Path(raw_file)
    tmap_file = Path(tmap_file)
    raise NotImplementedError()  # TODO
