from pathlib import Path
from typing import Any, Generator

import dask.array as da
import numpy as np
from ome_zarr.format import CurrentFormat, Format, format_from_version
from ome_zarr.io import parse_url
from ome_zarr.reader import Node, Reader
from tifffile import FILETYPE, TiffWriter
from tqdm.auto import tqdm

from .model import Layer, Project


def convert_raw_to_tmap(
    raw_url: str | Path,
    tmap_file: str | Path,
    time: int | None = None,
    channel: int | str | None = None,
    depth: int | None = None,
    layer_img_dir: str | Path | None = None,
    ome_zarr_format: str | Format | None = None,
    progress: bool = False,
) -> None:
    """Convert OME-Zarr image to TMAP file."""
    # validate arguments
    raw_url = str(raw_url)
    tmap_file = Path(tmap_file)
    if layer_img_dir is None:
        layer_img_dir = tmap_file.parent / f".{tmap_file.name}" / "layers"
    elif not Path(layer_img_dir).is_absolute():
        layer_img_dir = tmap_file.parent / Path(layer_img_dir)
    else:
        layer_img_dir = Path(layer_img_dir)
    # open raw image
    if isinstance(ome_zarr_format, str):
        ome_zarr_format = format_from_version(ome_zarr_format)
    zarr_location = parse_url(raw_url, fmt=ome_zarr_format or CurrentFormat())
    if zarr_location is None:
        raise ValueError(f"Invalid raw URL: {raw_url}")
    reader = Reader(zarr_location)
    nodes = list(reader())
    img_node = nodes[0]
    # load channel names
    channel_names: list[str] | None = img_node.metadata.get("name")
    if isinstance(channel, str):
        if channel_names is None:
            raise ValueError("Missing channel names")
        channel = channel_names.index(channel)
    # create project with layers
    project = Project(filename=tmap_file.name)
    for layer_axis_name_indices, layer_data in _generate_image_layers(
        img_node, t=time, c=channel, z=depth, progress=progress
    ):
        # write layer image
        layer_img_dir.mkdir(parents=True, exist_ok=True)
        layer_img_file_name = Path(zarr_location.basename()).stem
        for axis_name, i in layer_axis_name_indices.items():
            layer_img_file_name += f"_{axis_name.lower()}{i:02d}"
        layer_img_file_name += ".tif"
        layer_img_file = layer_img_dir / layer_img_file_name
        with TiffWriter(layer_img_file) as f:
            f.write(layer_data[0], subifds=len(layer_data) - 1)
            for x in layer_data[1:]:
                f.write(x, subfiletype=FILETYPE.REDUCEDIMAGE)
        # create layer
        layer_name_components = [
            f"{axis_name.upper()}{index:02d}"
            for axis_name, index in layer_axis_name_indices.items()
            if not (axis_name == "c" and channel_names is not None)
        ]
        if "c" in layer_axis_name_indices and channel_names is not None:
            channel_name = channel_names[layer_axis_name_indices["c"]]
            layer_name_components.append(channel_name)
        if len(layer_name_components) > 0:
            layer_name = " ".join(layer_name_components)
        else:
            layer_name = zarr_location.basename()
        layer = Layer(
            name=layer_name,
            tileSource=str(layer_img_file.relative_to(tmap_file.parent)) + ".dzi",
        )
        project.layers.append(layer)
    # write project
    with tmap_file.open("w", encoding="utf-8") as f:
        f.write(project.model_dump_json(indent=2, by_alias=True))


def _generate_image_layers(
    img_node: Node,
    t: int | None = None,
    c: int | None = None,
    z: int | None = None,
    progress: bool = False,
) -> Generator[tuple[dict[str, int], list[da.Array]], None, None]:
    """Generate image layers from an image node."""
    # find axes
    axes_meta = img_node.metadata.get("axes")
    if axes_meta is None:
        raise ValueError("Missing axes metadata")
    if not 2 <= len(axes_meta) <= 5:
        raise ValueError(f"Expected 2-5 axes, got {len(axes_meta)}")
    if any(da.asarray(img).ndim != len(axes_meta) for img in img_node.data):
        raise ValueError("Number of image axes does not match axes metadata")
    t_axis = _find_axis(axes_meta, "t", axis_type="time")
    c_axis = _find_axis(axes_meta, "c", axis_type="channel")
    z_axis = _find_axis(axes_meta, "z", axis_type="space")
    y_axis = _find_axis(axes_meta, "y", axis_type="space")
    x_axis = _find_axis(axes_meta, "x", axis_type="space")
    if x_axis is None or y_axis is None:
        raise ValueError("Missing x and/or y axes")
    if sum(axis is not None for axis in (t_axis, c_axis, z_axis)) + 2 != len(axes_meta):
        raise ValueError("Missing and/or unexpected axes")
    # transpose data to standard order and filter time, channel, and depth
    axis_order = [a for a in (t_axis, c_axis, z_axis, y_axis, x_axis) if a is not None]
    data = [da.transpose(img, axes=axis_order) for img in img_node.data]
    current_axis = 0
    if t_axis is not None:
        if t is not None:
            data = [da.take(img, t, axis=current_axis) for img in data]
            t_axis = None
        else:
            t_axis = current_axis
            current_axis += 1
    if c_axis is not None:
        if c is not None:
            data = [da.take(img, c, axis=current_axis) for img in data]
            c_axis = None
        else:
            c_axis = current_axis
            current_axis += 1
    if z_axis is not None:
        if z is not None:
            data = [da.take(img, z, axis=current_axis) for img in data]
            z_axis = None
        else:
            z_axis = current_axis
            current_axis += 1
    y_axis = current_axis
    current_axis += 1
    x_axis = current_axis
    current_axis += 1
    # generate layers
    layer_axis_name_sizes = {
        axis_name: _get_axis_size(data, axis, axis_name)
        for axis, axis_name in [(t_axis, "t"), (c_axis, "c"), (z_axis, "z")]
        if axis is not None
    }
    layer_indices = np.ndindex(*layer_axis_name_sizes.values())
    if progress:
        layer_indices = tqdm(
            layer_indices,
            total=np.prod(list(layer_axis_name_sizes.values())),
            unit="layer",
        )
    for layer_index in layer_indices:
        layer_axis_name_indices = dict(zip(layer_axis_name_sizes.keys(), layer_index))
        layer_data = [img[layer_index] for img in data]
        yield layer_axis_name_indices, layer_data


def _find_axis(
    axes_meta: list[dict[str, Any]], axis_name: str, axis_type: str | None = None
) -> int | None:
    """Find the index of an axis in axes metadata."""
    filtered_axes = [
        axis
        for axis, axis_meta in enumerate(axes_meta)
        if axis_meta["name"] == axis_name and axis_meta.get("type") in (axis_type, None)
    ]
    if len(filtered_axes) > 1:
        raise ValueError(f"Expected 0 or 1 {axis_name} axes, got {len(filtered_axes)}")
    if len(filtered_axes) == 1:
        return filtered_axes[0]
    return None


def _get_axis_size(data: list[da.Array], axis: int, axis_name: str) -> int:
    """Get the size of an axis across all resolutions."""
    axis_size = data[0].shape[axis]
    if any(img.shape[axis] != axis_size for img in data):
        raise ValueError(f"Inconsistent {axis_name} axis sizes across resolutions")
    return axis_size
