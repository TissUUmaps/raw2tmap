from pathlib import Path

import click

from raw2tmap import convert_raw_to_tmap


@click.command(name="raw2tmap", help="Convert OME-NGFF to TMAP.")
@click.argument(
    "raw_file",
    type=click.Path(exists=True, path_type=Path),
    help="Path to input OME-NGFF file.",
)
@click.argument(
    "tmap_file",
    type=click.Path(dir_okay=False, writable=True, path_type=Path),
    help="Path to output TMAP file.",
)
@click.version_option()
def main(raw_file: Path, tmap_file: Path) -> None:
    convert_raw_to_tmap(raw_file, tmap_file)


if __name__ == "__main__":
    main()
