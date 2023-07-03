# raw2tmap

Convert OME-NGFF to TMAP

## Installation

Use the package manager [pip](https://pip.pypa.io) to install raw2tmap:

    pip install raw2tmap

## Usage

    ❯ raw2tmap --help
    Usage: raw2tmap [OPTIONS] RAW_URL TMAP_FILE

      Convert OME-NGFF to TMAP.

    Options:
    -t INTEGER RANGE         Time index.  [x>=0]
    -c INTEGER / TEXT        Channel index or name.
    -z INTEGER RANGE         Depth (z) index.  [x>=0]
    --layers DIRECTORY       Path to layer images, relative to TMAP_FILE.
                             Defaults to '.{TMAP_FILE}/layers'.
    --fmt [0.1|0.2|0.3|0.4]  OME-Zarr format version.  [default: 0.4]
    --quiet / --no-quiet     Suppress progress bar.  [default: no-quiet]
    --version                Show the version and exit.
    --help                   Show this message and exit.

## Support

If you find a bug, please [raise an issue](https://github.com/TissUUmaps/raw2tmap/issues/new).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## Authors

[SciLifeLab BioImage Informatics Facility (BIIF)](https://biifsweden.github.io)

## License

[MIT](LICENSE)
