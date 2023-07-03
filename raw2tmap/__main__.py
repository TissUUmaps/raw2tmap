from pathlib import Path
from typing import Any

import click
from click.core import Context, Parameter
from ome_zarr.format import CurrentFormat, format_implementations

from raw2tmap import convert_raw_to_tmap


class IntRangeOrStringParamType(click.ParamType):
    """A parameter type that accepts either an integer or a string."""

    name = "integer / text"

    def __init__(self, *args, **kwargs) -> None:
        self._int_range = click.IntRange(*args, **kwargs)

    def convert(self, value: Any, param: Parameter | None, ctx: Context | None) -> Any:
        try:
            return self._int_range.convert(value, param, ctx)
        except click.BadParameter:
            return str(value)


@click.command(name="raw2tmap", help="Convert OME-NGFF to TMAP.")
@click.argument("raw_url", type=str)
@click.argument("tmap_file", type=click.Path(path_type=Path))
@click.option(
    "-t",
    "time",
    type=click.IntRange(min=0),
    help="Time index.",
)
@click.option(
    "-c",
    "channel",
    type=IntRangeOrStringParamType(min=0),
    help="Channel index or name.",
)
@click.option(
    "-z",
    "depth",
    type=click.IntRange(min=0),
    help="Depth index.",
)
@click.option(
    "--layers",
    "layer_img_dir",
    type=click.Path(file_okay=False, path_type=Path),
    help=(
        "Path to layer images, relative to TMAP_FILE. "
        "Defaults to '.{TMAP_FILE}/layers'."
    ),
)
@click.option(
    "--fmt",
    "ome_zarr_format",
    type=click.Choice(
        sorted(fmt_impl.version for fmt_impl in format_implementations())
    ),
    default=CurrentFormat().version,
    show_default=True,
    help="OME-Zarr format version.",
)
@click.option(
    "--quiet/--no-quiet",
    default=False,
    show_default=True,
    help="Suppress progress bar.",
)
@click.version_option()
def main(
    raw_url: str,
    tmap_file: Path,
    time: int | None,
    channel: int | str | None,
    depth: int | None,
    layer_img_dir: Path | None,
    ome_zarr_format: str,
    quiet: bool,
) -> None:
    convert_raw_to_tmap(
        raw_url,
        tmap_file,
        time=time,
        channel=channel,
        depth=depth,
        layer_img_dir=layer_img_dir,
        ome_zarr_format=ome_zarr_format,
        progress=not quiet,
    )


if __name__ == "__main__":
    main()
