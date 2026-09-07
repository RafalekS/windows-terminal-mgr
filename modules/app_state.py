"""Shared application state: the Windows Terminal settings.json data, derived
lists, save/backup logic, and entry-identity (UID) helpers.

Importing this module has side effects (matching the original single-file
behaviour): it locates the Windows Terminal ``LocalState`` directory, ``chdir``s
into it, takes a timestamped backup of ``settings.json`` and loads it into
``data_schemes``. If the directory cannot be found it prints an error and calls
``sys.exit(1)``.

Mutable state (``data_schemes``, ``profiles_list`` ...) is exposed as *module
attributes*. Read them as ``app_state.data_schemes`` so runtime reassignments and
in-place mutations are visible everywhere.
"""

import argparse
import datetime
import glob
import os
import sys
import uuid as _uuid
from shutil import copyfile

import commentjson
import matplotlib.font_manager

from modules.config import APP_CONFIG

# ── Command line ─────────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(description="Windows Terminal Settings Manager")
_parser.add_argument("--debug", action="store_true", help="Enable debug output")
_args, _ = _parser.parse_known_args()

DEBUG = _args.debug


def debug_print(*args, **kwargs):
    """Print only when the ``--debug`` flag is set."""
    if DEBUG:
        print(*args, **kwargs)


# ── UID tracking for newTabMenu entries ──────────────────────────────────────
# Internal key stamped onto menu entries so the Folders tab can track identity
# across tree reloads. Stripped again before writing to disk.
_UID_KEY = "_wt_uid"


def stamp_uids(entries):
    """Stamp unique IDs on all newTabMenu entries (recursively into folders)."""
    for entry in entries:
        if isinstance(entry, dict):
            if _UID_KEY not in entry:
                entry[_UID_KEY] = str(_uuid.uuid4())
            if entry.get("type") == "folder" and "entries" in entry:
                stamp_uids(entry["entries"])


def strip_uids(obj):
    """Return a deep copy of *obj* with every ``_wt_uid`` key removed."""
    if isinstance(obj, dict):
        return {k: strip_uids(v) for k, v in obj.items() if k != _UID_KEY}
    if isinstance(obj, list):
        return [strip_uids(item) for item in obj]
    return obj


# ── Locate the Windows Terminal settings directory ───────────────────────────
def _discover_settings_path() -> str:
    home_path = os.getenv("HOMEPATH")
    if not home_path:
        user_profile = os.getenv("USERPROFILE", "")
        if user_profile and ":" in user_profile:
            # USERPROFILE is a full path like C:\Users\name - strip the drive.
            home_path = user_profile[2:]
        else:
            home_path = user_profile

    override = APP_CONFIG.get("wt_path_override", "").strip()
    if override and os.path.isdir(override):
        return override

    for base in (f"C:{home_path}\\LocalAppData", f"C:{home_path}\\AppData\\Local"):
        candidate = f"{base}\\Packages\\Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState"
        if os.path.isdir(candidate):
            return candidate

    print("Error: Could not find Windows Terminal settings directory.")
    print(f"Searched with HOMEPATH='{home_path}'")
    print("Expected: %HOMEPATH%\\LocalAppData\\Packages\\"
          "Microsoft.WindowsTerminal_8wekyb3d8bbwe\\LocalState")
    sys.exit(1)


settingsPath = _discover_settings_path()
os.chdir(settingsPath)


def _backup_settings() -> None:
    """Copy settings.json to a timestamped ``.bak_YYYYMMDD_HHMMSS`` file."""
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    copyfile(f"{settingsPath}\\settings.json",
             f"{settingsPath}\\settings.json.bak_{stamp}")


# Backup once at startup (matches original behaviour).
_backup_settings()

try:
    with open("settings.json", "r", encoding="utf-8") as _f:
        data_schemes = commentjson.loads(_f.read())
except (OSError, ValueError) as e:
    print(f"Error loading settings.json: {e}")
    sys.exit(1)

# Stamp UIDs on existing menu entries at load time.
stamp_uids(data_schemes.get("newTabMenu", []))


# ── Save ─────────────────────────────────────────────────────────────────────
def dumpJson() -> bool:
    """Write ``data_schemes`` back to settings.json (with backup + pruning)."""
    try:
        backup_cfg = APP_CONFIG.get("backup", {})
        if backup_cfg.get("enabled", True):
            _backup_settings()
            max_count = backup_cfg.get("max_count", 10)
            bak_files = sorted(glob.glob(f"{settingsPath}\\settings.json.bak_*"))
            while len(bak_files) > max_count:
                try:
                    os.remove(bak_files.pop(0))
                except OSError:
                    break

        clean_data = strip_uids(data_schemes)
        with open("settings.json", "w", encoding="utf-8") as f:
            commentjson.dump(clean_data, f, indent=2, ensure_ascii=False)
        return True
    except (OSError, ValueError) as e:
        print(f"Error saving settings.json: {e}")
        return False


# ── Derived lists ────────────────────────────────────────────────────────────
default_guid = data_schemes.get("defaultProfile", "")


def findDefault() -> str:
    """Name of the default profile (looked up from ``defaultProfile`` GUID)."""
    for item in data_schemes.get("profiles", {}).get("list", []):
        if item.get("guid") == default_guid:
            return item.get("name", "Unknown")
    return "Unknown"


default_profile = findDefault()

data_list = [item["name"] for item in data_schemes.get("schemes", [])]
profiles_list = [item["name"] for item in data_schemes.get("profiles", {}).get("list", [])]

_fonts = matplotlib.font_manager.fontManager.ttflist
font_list = list(dict.fromkeys(sorted((f.name for f in _fonts), key=str.lower)))
