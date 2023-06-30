import sys
from pathlib import Path
from typing import BinaryIO

import click

from raw2tmap import convert_raw_to_tmap


@click.command(name="raw2tmap", help="Convert OME-NGFF to TMAP.")
@click.argument("raw_file", type=click.File(mode="rb"))
@click.option(
    "-o",
    "tmap_file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Path to output TMAP file.",
)
@click.version_option()
def main(raw_file: BinaryIO, tmap_file: Path | None) -> None:
    convert_raw_to_tmap(raw_file, tmap_file or sys.stdout)


if __name__ == "__main__":
    main()
