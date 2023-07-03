# raw2tmap

Convert OME-Zarr files to TMAP format

## Installation

Use the package manager [pip](https://pip.pypa.io) to install raw2tmap:

    pip install raw2tmap

## Usage

To convert an OME-Zarr file to TMAP format:

    ❯ raw2tmap --help
    Usage: raw2tmap [OPTIONS] RAW_URL TMAP_FILE

      Convert OME-Zarr files to TMAP format.

    Options:
      -t, --time INTEGER RANGE      Time index.  [x>=0]
      -c, --channel INTEGER / TEXT  Channel index or name.
      -z, --depth INTEGER RANGE     Depth (z) index.  [x>=0]
      --layers DIRECTORY            Path to layer images, relative to TMAP_FILE.
                                    Defaults to '.{TMAP_FILE}/layers'.
      --compression                 Compression algorithm.  [default: none]
      --tilesize INTEGER RANGE      Tile size in pixels.  [default: 256; x>0]
      --format [0.1|0.2|0.3|0.4]    OME-Zarr format version.  [default: 0.4]
      -q, --quiet                   Quiet mode (suppress progress bar).
      --version                     Show the version and exit.
      --help                        Show this message and exit.

Example:

    raw2tmap -t 0 -z 0 https://uk1s3.embassy.ebi.ac.uk/idr/zarr/v0.4/idr0052A/5514375.zarr 5514375.tmap

OME-Zarr files can for example be created using [bioformats2raw](https://github.com/glencoesoftware/bioformats2raw).

## Support

If you find a bug, please [raise an issue](https://github.com/TissUUmaps/raw2tmap/issues/new).

## Contributing

Pull requests are welcome.

For major changes, please open an issue first to discuss what you would like to change.

## Authors

[SciLifeLab BioImage Informatics Facility (BIIF)](https://biifsweden.github.io)

## License

[MIT](LICENSE)
