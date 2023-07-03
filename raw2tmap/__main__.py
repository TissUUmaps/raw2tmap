from pathlib import Path
from typing import Any, Union

import click
import tifffile
from click.core import Context, Parameter
from ome_zarr.format import CurrentFormat, format_implementations

from raw2tmap import convert_raw_to_tmap


class IntRangeOrStringParamType(click.ParamType):
    """A parameter type that accepts either an integer or a string."""

    name = "integer/text"

    def __init__(self, *args, **kwargs) -> None:
        self._int_range = click.IntRange(*args, **kwargs)

    def convert(
        self, value: Any, param: Union[Parameter, None], ctx: Union[Context, None]
    ) -> Any:
        try:
            return self._int_range.convert(value, param, ctx)
        except click.BadParameter:
            return str(value)


@click.command(name="raw2tmap", help="Convert OME-Zarr files to TMAP format.")
@click.argument("raw_file_or_url", type=str)
@click.argument("tmap_file", type=click.Path(path_type=Path))
@click.option(
    "-t",
    "--time",
    "time",
    type=click.IntRange(min=0),
    help="Time index.",
)
@click.option(
    "-c",
    "--channel",
    "channel",
    type=IntRangeOrStringParamType(min=0),
    help="Channel index or name.",
)
@click.option(
    "-z",
    "--depth",
    "depth",
    type=click.IntRange(min=0),
    help="Depth (z) index.",
)
@click.option(
    "--layers",
    "img_dir",
    type=click.Path(file_okay=False, path_type=Path),
    help=(
        "Path to layer images, relative to TMAP_FILE. "
        "Defaults to '.{TMAP_FILE}/layers'."
    ),
)
@click.option(
    "--compression",
    "compression",
    type=click.Choice(
        [c.name.lower() for c in tifffile.COMPRESSION], case_sensitive=False
    ),
    default="none",
    show_default=True,
    help="Compression algorithm.",
    metavar="ALGORITHM",
)
@click.option(
    "--tilesize",
    "tile_size_px",
    type=click.IntRange(min=0, min_open=True),
    default=256,
    show_default=True,
    help="Tile size in pixels.",
)
@click.option(
    "--format",
    "ome_zarr_format",
    type=click.Choice(
        sorted(fmt_impl.version for fmt_impl in format_implementations())
    ),
    default=CurrentFormat().version,
    show_default=True,
    help="OME-Zarr format version.",
)
@click.option(
    "--dzi",
    "write_dzi",
    is_flag=True,
    default=False,
    help="Write DZI file (requires pyvips).",
)
@click.option(
    "-q",
    "--quiet",
    "quiet",
    is_flag=True,
    default=False,
    help="Quiet mode (hide progress bar).",
)
@click.version_option()
def main(
    raw_file_or_url: str,
    tmap_file: Path,
    time: Union[int, None],
    channel: Union[int, str, None],
    depth: Union[int, None],
    img_dir: Union[Path, None],
    compression: Union[str, None],
    tile_size_px: int,
    ome_zarr_format: str,
    write_dzi: bool,
    quiet: bool,
) -> None:
    convert_raw_to_tmap(
        raw_file_or_url,
        tmap_file,
        time=time,
        channel=channel,
        depth=depth,
        img_dir=img_dir,
        compression=compression,
        tile_size_px=tile_size_px,
        ome_zarr_format=ome_zarr_format,
        write_dzi=write_dzi,
        progress=not quiet,
    )


if __name__ == "__main__":
    main()
