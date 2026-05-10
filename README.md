# OpenDeck-Converter

Install `.streamDeckPlugin` packages into OpenDeck on Windows.

## Usage

```bash
python install_streamdeck_plugin.py "C:\path\to\plugin.streamDeckPlugin"
```

### Options

- `--destination PATH`  
  Override install directory.  
  Default: `%APPDATA%\opendeck\plugins`
- `--overwrite`  
  Replace existing plugin folders with the same name.

## Notes

- `.streamDeckPlugin` files are ZIP archives.
- The script safely extracts the package and installs discovered plugin folders (typically `*.sdPlugin`) into the OpenDeck plugins directory.
