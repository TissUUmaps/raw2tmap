from pathlib import Path
from typing import Any, Generator, Union

import dask.array as da
import numpy as np
import tifffile
from ome_zarr.format import CurrentFormat, Format, format_from_version
from ome_zarr.io import parse_url
from ome_zarr.reader import Node, Reader
from skimage.util import img_as_ubyte
from tifffile import TiffWriter
from tissuumaps_schema.v01 import Project
from tissuumaps_schema.v01.project import Layer
from tqdm.auto import tqdm

try:
    import pyvips
except ImportError:
    pyvips = None

MICROMETERS_PER_UNIT: dict[str, float] = {
    "angstrom": 1e-4,
    "attometer": 1e-12,
    "centimeter": 1e4,
    "decimeter": 1e5,
    "exameter": 1e24,
    "femtometer": 1e-9,
    "foot": 304800,
    "gigameter": 1e15,
    "hectometer": 1e8,
    "inch": 25400,
    "kilometer": 1e9,
    "megameter": 1e12,
    "meter": 1e6,
    "micrometer": 1,
    "mile": 1609344000,
    "millimeter": 1e3,
    "nanometer": 1e-3,
    "parsec": 30.857 * 1e21,  # approximate!
    "petameter": 1e21,
    "picometer": 1e-6,
    "terameter": 1e18,
    "yard": 914400,
    "yoctometer": 1e-18,
    "yottameter": 1e30,
    "zeptometer": 1e-15,
    "zettameter": 1e27,
}


def convert_raw_to_tmap(
    raw_file_or_url: Union[str, Path],
    tmap_file: Union[str, Path],
    time: Union[int, None] = None,
    channel: Union[int, str, None] = None,
    depth: Union[int, None] = None,
    img_dir: Union[str, Path, None] = None,
    compression: Union[str, None] = None,
    tile_size_px: int = 256,
    ome_zarr_format: Union[str, Format, None] = None,
    write_dzi: bool = False,
    progress: bool = False,
) -> None:
    """Convert OME-Zarr files to TMAP format."""
    # validate arguments
    raw_file_or_url = str(raw_file_or_url)
    tmap_file = Path(tmap_file)
    if img_dir is None:
        img_dir = tmap_file.parent / f".{tmap_file.name}" / "layers"
    elif not Path(img_dir).is_absolute():
        img_dir = tmap_file.parent / Path(img_dir)
    else:
        img_dir = Path(img_dir)
    if write_dzi and not pyvips:
        raise ImportError("pyvips is required for DZI writing")
    # open raw image
    if isinstance(ome_zarr_format, str):
        ome_zarr_format = format_from_version(ome_zarr_format)
    zarr_location = parse_url(raw_file_or_url, fmt=ome_zarr_format or CurrentFormat())
    if zarr_location is None:
        raise ValueError(f"Invalid raw file/URL: {raw_file_or_url}")
    reader = Reader(zarr_location)
    nodes = list(reader())
    img_node = nodes[0]
    # load xy scales and channel names
    xy_scales_um = _get_xy_scales_um(img_node, check_tissuumaps=True)
    channel_names: Union[list[str], None] = img_node.metadata.get("name")
    if isinstance(channel, str):
        if channel_names is None:
            raise ValueError("Missing channel names")
        channel = channel_names.index(channel)
    # create project with layers
    project = Project(filename=tmap_file.name, mpp=xy_scales_um[0][0])
    for layer_axis_name_indices, layer_data in _generate_image_layers(
        img_node, t=time, c=channel, z=depth, progress=progress
    ):
        # write layer TIFF
        img_dir.mkdir(parents=True, exist_ok=True)
        img_file_name = Path(zarr_location.basename()).stem
        for axis_name, index in layer_axis_name_indices.items():
            img_file_name += f"_{axis_name.lower()}{index:02d}"
        img_file_name += ".tif"
        img_file = img_dir / img_file_name
        with TiffWriter(img_file, bigtiff=True) as f:
            for i, (img, xy_scale_um) in enumerate(zip(layer_data, xy_scales_um)):
                f.write(
                    img_as_ubyte(img),
                    tile=(tile_size_px, tile_size_px),
                    compression=compression,
                    resolution=(1.0 / xy_scale_um[0], 1.0 / xy_scale_um[1]),
                    resolutionunit=tifffile.RESUNIT.MICROMETER,
                    subfiletype=tifffile.FILETYPE.REDUCEDIMAGE if i > 0 else None,
                    software=False,
                    subifds=len(layer_data) - 1 if i == 0 else None,
                )
        # convert to DZI
        if write_dzi:
            pyvips.Image.new_from_file(str(img_file)).dzsave(
                str(img_file),
                suffix=".jpg",
                overlap=0,
                tile_size=tile_size_px,
                depth="onepixel",
                background=0,
            )
            img_file.unlink()
        # create layer
        layer_name_components = [
            f"{axis_name.upper()}{index:02d}"
            for axis_name, index in layer_axis_name_indices.items()
            if not (axis_name == "c" and channel_names is not None)
        ]
        if "c" in layer_axis_name_indices and channel_names is not None:
            channel_index = layer_axis_name_indices["c"]
            if not 0 <= channel_index < len(channel_names):
                raise ValueError(f"Missing channel name for index {channel_index}")
            layer_name_components.append(channel_names[channel_index])
        if len(layer_name_components) > 0:
            layer_name = " ".join(layer_name_components)
        else:
            layer_name = zarr_location.basename()
        layer = Layer(
            name=layer_name,
            tileSource=str(img_file.relative_to(tmap_file.parent)) + ".dzi",
        )
        project.layers.append(layer)
    # write project
    with tmap_file.open("w", encoding="utf-8") as f:
        f.write(project.model_dump_json(indent=2, by_alias=True))


def _get_xy_scales_um(
    img_node: Node, check_tissuumaps: bool = False
) -> list[tuple[float, float]]:
    """Get the XY scales in micrometers for each resolution."""
    ct_metadata = img_node.metadata.get("coordinateTransformations")
    if ct_metadata is None:
        raise ValueError("Missing coordinate transformations metadata")
    if len(ct_metadata) != len(img_node.data):
        raise ValueError("Expected one coordinate transformation per resolution")
    scale_cts = [ct for cts in ct_metadata for ct in cts if ct["type"] == "scale"]
    if len(scale_cts) != len(img_node.data):
        raise ValueError("Expected one scale coordinate transformation per resolution")
    axes_metadata = img_node.metadata.get("axes")
    if axes_metadata is None:
        raise ValueError("Missing axes metadata")
    x_axis = _find_axis(axes_metadata, "x", axis_type="space")
    y_axis = _find_axis(axes_metadata, "y", axis_type="space")
    if x_axis is None or y_axis is None:
        raise ValueError("Missing X and/or Y axes")
    x_unit = axes_metadata[x_axis].get("unit")
    y_unit = axes_metadata[y_axis].get("unit")
    if x_unit is None or y_unit is None:
        raise ValueError("Missing unit metadata for X and/or Y axes")
    xy_scales = [
        (scale_ct["scale"][x_axis], scale_ct["scale"][y_axis]) for scale_ct in scale_cts
    ]
    if check_tissuumaps and any(
        x_scale * MICROMETERS_PER_UNIT[x_unit] != y_scale * MICROMETERS_PER_UNIT[y_unit]
        for x_scale, y_scale in xy_scales
    ):
        raise ValueError("TissUUmaps requires equal XY scales")
    if check_tissuumaps and any(
        x_scale != xy_scales[res - 1][0] * 2 or y_scale != xy_scales[res - 1][1] * 2
        for res, (x_scale, y_scale) in enumerate(xy_scales[1:], start=1)
    ):
        raise ValueError("TissUUmaps requires 2x scale difference between resolutions")
    return [
        (x_scale * MICROMETERS_PER_UNIT[x_unit], y_scale * MICROMETERS_PER_UNIT[y_unit])
        for (x_scale, y_scale) in xy_scales
    ]


def _generate_image_layers(
    img_node: Node,
    t: Union[int, None] = None,
    c: Union[int, None] = None,
    z: Union[int, None] = None,
    progress: bool = False,
) -> Generator[tuple[dict[str, int], list[da.Array]], None, None]:
    """Generate image layers from an image node."""
    # find axes
    axes_metadata = img_node.metadata.get("axes")
    if axes_metadata is None:
        raise ValueError("Missing axes metadata")
    if not 2 <= len(axes_metadata) <= 5:
        raise ValueError(f"Expected 2-5 axes, got {len(axes_metadata)}")
    if any(da.asarray(img).ndim != len(axes_metadata) for img in img_node.data):
        raise ValueError("Number of image axes does not match axes metadata")
    t_axis = _find_axis(axes_metadata, "t", axis_type="time")
    c_axis = _find_axis(axes_metadata, "c", axis_type="channel")
    z_axis = _find_axis(axes_metadata, "z", axis_type="space")
    y_axis = _find_axis(axes_metadata, "y", axis_type="space")
    x_axis = _find_axis(axes_metadata, "x", axis_type="space")
    if x_axis is None or y_axis is None:
        raise ValueError("Missing X and/or Y axes")
    if sum(a is not None for a in (t_axis, c_axis, z_axis)) + 2 != len(axes_metadata):
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
    axes_metadata: list[dict[str, Any]],
    axis_name: str,
    axis_type: Union[str, None] = None,
) -> Union[int, None]:
    """Find the index of an axis in axes metadata."""
    filtered_axes = [
        axis
        for axis, axis_metadata in enumerate(axes_metadata)
        if axis_metadata["name"] == axis_name
        and (axis_type is None or axis_metadata.get("type") in (axis_type, None))
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
