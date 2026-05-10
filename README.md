# OpenDeck-Converter

Install `.streamDeckPlugin` packages into OpenDeck on Windows with a single double-click.

---

## Quick start — Windows "Open With" (recommended)

1. Go to the [**Releases**](../../releases/latest) page and download `OpenDeckInstaller.exe`.
2. Save it somewhere permanent, e.g. `C:\Program Files\OpenDeckInstaller\OpenDeckInstaller.exe`.
3. Right-click any `.streamDeckPlugin` file → **Open With** → **Choose another app**.
4. Browse to `OpenDeckInstaller.exe` and tick **Always use this app to open .streamDeckPlugin files**.
5. Done — from now on, double-clicking a `.streamDeckPlugin` file installs it automatically into  
   `%APPDATA%\opendeck\plugins`.

A success (or error) dialog will appear after each install.

---

## Command-line usage (Python script)

```bash
python install_streamdeck_plugin.py "C:\path\to\plugin.streamDeckPlugin"
```

### Options

| Option | Description | Default |
|---|---|---|
| `--destination PATH` | Override install directory | `%APPDATA%\opendeck\plugins` |
| `--overwrite` | Replace existing plugin folder if it already exists | off |

---

## How it works

- `.streamDeckPlugin` files are standard ZIP archives.
- The installer safely extracts the archive into a temporary folder.
- It locates plugin directories (folders containing `manifest.json`, preferably named `*.sdPlugin`).
- Each discovered plugin folder is copied into the OpenDeck plugins directory.
- When run as the compiled exe, existing plugin folders are always replaced so the install is truly one-click.

---

## Building the exe yourself

Requires Python 3.9+ and [PyInstaller](https://pyinstaller.org):

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name OpenDeckInstaller install_streamdeck_plugin.py
```

The exe is written to `dist\OpenDeckInstaller.exe`.
