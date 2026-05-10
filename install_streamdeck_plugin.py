#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ctypes
import os
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path


def _is_frozen() -> bool:
    """Return True when running as a PyInstaller-compiled executable."""
    return getattr(sys, "frozen", False)


def _notify(title: str, message: str, *, is_error: bool = False) -> None:
    """Show a Windows message box when running as exe, otherwise print."""
    if _is_frozen() and sys.platform == "win32":
        MB_OK = 0x0
        MB_ICONERROR = 0x10
        MB_ICONINFORMATION = 0x40
        flags = MB_OK | (MB_ICONERROR if is_error else MB_ICONINFORMATION)
        ctypes.windll.user32.MessageBoxW(0, message, title, flags)
    else:
        dest = sys.stderr if is_error else sys.stdout
        print(f"[{'ERROR' if is_error else 'OK'}] {title}: {message}", file=dest)


def default_opendeck_plugins_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("APPDATA is not set. Use --destination to provide a target directory.")
    return Path(appdata) / "opendeck" / "plugins"


def safe_extract_zip(zip_path: Path, extract_dir: Path) -> None:
    with zipfile.ZipFile(zip_path, "r") as archive:
        for member in archive.infolist():
            member_path = extract_dir / member.filename
            resolved_member = member_path.resolve()
            resolved_extract_dir = extract_dir.resolve()
            try:
                resolved_member.relative_to(resolved_extract_dir)
            except ValueError:
                raise RuntimeError(
                    f"Unsafe archive entry detected: {member.filename} "
                    "(attempts to extract outside target directory; possible path traversal)."
                )
        archive.extractall(extract_dir)


def discover_plugin_dirs(extract_dir: Path) -> list[Path]:
    manifests = list(extract_dir.rglob("manifest.json"))
    sdplugin_candidates = {m.parent for m in manifests if m.parent.name.endswith(".sdPlugin")}
    sdplugin_dirs = sorted(sdplugin_candidates, key=lambda p: len(p.parts))
    if sdplugin_dirs:
        return sdplugin_dirs

    if not manifests:
        return []

    manifest_parents = sorted({m.parent for m in manifests}, key=lambda p: len(p.parts))
    selected: list[Path] = []
    for candidate in manifest_parents:
        is_nested = False
        for parent in selected:
            try:
                candidate.relative_to(parent)
                is_nested = True
                break
            except ValueError:
                continue
        if not is_nested:
            selected.append(candidate)
    return selected


def install_plugin_dir(source_dir: Path, destination_root: Path, overwrite: bool) -> Path:
    target_dir = destination_root / source_dir.name
    if target_dir.exists():
        if not overwrite:
            raise FileExistsError(
                f"Plugin folder already exists: {target_dir}. Re-run with --overwrite to replace it."
            )
        if target_dir.is_dir():
            shutil.rmtree(target_dir)
        else:
            target_dir.unlink()

    shutil.copytree(source_dir, target_dir)
    return target_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install a .streamDeckPlugin package into OpenDeck plugins folder."
    )
    parser.add_argument("package", type=Path, help="Path to .streamDeckPlugin file")
    parser.add_argument(
        "--destination",
        type=Path,
        default=None,
        help=r"Target plugin directory (default: %%APPDATA%%\opendeck\plugins)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite installed plugin folders with the same name",
    )
    return parser.parse_args()



def main() -> int:
    # When launched with no arguments (e.g., double-clicked), show a usage hint.
    if _is_frozen() and len(sys.argv) < 2:
        _notify(
            "OpenDeck Plugin Installer",
            "To install a plugin, right-click a .streamDeckPlugin file and choose\n"
            "'Open With' → OpenDeckInstaller.exe.\n\n"
            "You can also drag a .streamDeckPlugin file onto this exe.",
        )
        return 0

    args = parse_args()
    package_path: Path = args.package.expanduser().resolve()

    # When running as a compiled exe (i.e., via "Open With"), always overwrite
    # existing plugin folders so the install is truly one-click.
    if _is_frozen():
        args.overwrite = True

    if not package_path.exists() or not package_path.is_file():
        _notify(
            "OpenDeck Plugin Installer",
            f"Package file not found:\n{package_path}",
            is_error=True,
        )
        return 1

    if package_path.suffix.lower() != ".streamdeckplugin":
        _notify(
            "OpenDeck Plugin Installer",
            "Input file must use the .streamDeckPlugin extension.",
            is_error=True,
        )
        return 1

    destination_root = (
        args.destination.expanduser().resolve() if args.destination is not None else default_opendeck_plugins_dir()
    )
    destination_root.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="opendeck_plugin_") as temp_dir:
            extract_dir = Path(temp_dir)
            safe_extract_zip(package_path, extract_dir)
            plugin_dirs = discover_plugin_dirs(extract_dir)
            if not plugin_dirs:
                _notify(
                    "OpenDeck Plugin Installer",
                    "No valid plugin found in archive "
                    "(expected a manifest.json file, preferably in a directory ending with .sdPlugin).",
                    is_error=True,
                )
                return 1

            installed_paths: list[Path] = []
            for plugin_dir in plugin_dirs:
                installed_paths.append(
                    install_plugin_dir(plugin_dir, destination_root=destination_root, overwrite=args.overwrite)
                )

            names = "\n".join(f"- {p.name}" for p in installed_paths)
            _notify(
                "OpenDeck Plugin Installer",
                f"Plugin(s) installed successfully:\n{names}",
            )

    except zipfile.BadZipFile:
        _notify(
            "OpenDeck Plugin Installer",
            "Invalid .streamDeckPlugin file (not a valid ZIP archive).",
            is_error=True,
        )
        return 1
    except (RuntimeError, FileExistsError, OSError) as exc:
        _notify(
            "OpenDeck Plugin Installer",
            f"Installation failed:\n{exc}",
            is_error=True,
        )
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
