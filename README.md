# raw2tmap

[![pypi](https://img.shields.io/pypi/v/raw2tmap?label=pypi)](https://pypi.org/project/raw2tmap/)
[![python](https://img.shields.io/pypi/pyversions/raw2tmap?label=python)](https://www.python.org)
[![test](https://img.shields.io/github/actions/workflow/status/TissUUmaps/raw2tmap/test.yml?label=test)](https://github.com/TissUUmaps/raw2tmap/actions/workflows/test.yml)
[![build](https://img.shields.io/github/actions/workflow/status/TissUUmaps/raw2tmap/build-and-publish.yml?label=build)](https://github.com/TissUUmaps/raw2tmap/actions/workflows/build-and-publish.yml)
[![coverage](https://img.shields.io/codecov/c/gh/TissUUmaps/raw2tmap?label=coverage)](https://app.codecov.io/gh/TissUUmaps/raw2tmap)
[![issues](https://img.shields.io/github/issues/TissUUmaps/raw2tmap?label=issues)](https://github.com/TissUUmaps/raw2tmap/issues)
[![pull requests](https://img.shields.io/github/issues-pr/TissUUmaps/raw2tmap?label=pull%20requests)](https://github.com/TissUUmaps/raw2tmap/pulls)
[![license](https://img.shields.io/github/license/TissUUmaps/raw2tmap?label=license)](https://github.com/TissUUmaps/raw2tmap/blob/main/LICENSE)

Convert OME-Zarr files to TMAP format

## Requirements

[Python](https://www.python.org) 3.9 or later

## Installation

Use the package manager [pip](https://pip.pypa.io) to install raw2tmap:

    pip install raw2tmap

To enable the `--dzi` option, install with the `dzi` extra (requires libvips):

    pip install "raw2tmap[dzi]"

## Usage

To convert an OME-Zarr file to TMAP format:

    ❯ raw2tmap --help
    Usage: raw2tmap [OPTIONS] RAW_FILE_OR_URL TMAP_FILE

      Convert OME-Zarr files to TMAP format.

    Options:
      -t, --time INTEGER RANGE    Time index.  [x>=0]
      -c, --channel INTEGER/TEXT  Channel index or name.
      -z, --depth INTEGER RANGE   Depth (z) index.  [x>=0]
      --layers DIRECTORY          Path to layer images, relative to TMAP_FILE.
                                  Defaults to '.{TMAP_FILE}/layers'.
      --compression ALGORITHM     Compression algorithm.  [default: none]
      --tilesize INTEGER RANGE    Tile size in pixels.  [default: 256; x>0]
      --format [0.1|0.2|0.3|0.4]  OME-Zarr format version.  [default: 0.4]
      --dzi                       Write DZI file (requires pyvips).
      -q, --quiet                 Quiet mode (hide progress bar).
      --version                   Show the version and exit.
      --help                      Show this message and exit.

Example:

    raw2tmap -t 0 -z 10 https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0052A/5514375.zarr 5514375.tmap

OME-Zarr files can for example be created using [bioformats2raw](https://github.com/glencoesoftware/bioformats2raw).

## Support

If you find a bug, please [raise an issue](https://github.com/TissUUmaps/raw2tmap/issues/new).

## Contributing

Pull requests are welcome.

For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Changelog

[Changelog](https://github.com/TissUUmaps/raw2tmap/blob/main/CHANGELOG.md)

## Authors

[SciLifeLab BioImage Informatics Facility (BIIF)](https://biifsweden.github.io)

## License

[MIT](https://github.com/TissUUmaps/raw2tmap/blob/main/LICENSE)
