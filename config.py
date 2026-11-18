"""Where the Mod Manager looks for things / Dove il Mod Manager cerca le cose.

Every path can be changed with an environment variable or with a JSON file at
`$XDG_CONFIG_HOME/fs25-mod-manager/config.json` (default `~/.config/fs25-mod-manager/config.json`).
Environment variables win over the file. Keys in the file are the same names as the variables.

| Variable              | What it is                                                         | Default |
|-----------------------|--------------------------------------------------------------------|---------|
| FS25_PROFILE_DIR      | game profile folder `.../My Games/FarmingSimulator2025`            | first existing Steam/Proton path (see `profile_candidates`) |
| FS25_GAME_MODS_DIR    | folder the game reads mods from                                    | `$FS25_PROFILE_DIR/mods` |
| FS25_LIBRARY_DIR      | your mod library: holds `mods/` (archive), `BACKUP_MODS/`, `mods-bck/` | `$XDG_DATA_HOME/fs25-mod-manager/library` |
| FS25_LAUNCHER         | optional script that starts the game (may define mod sets, see README) | not set: no launch button |
| FS25_BACKUP_DIR       | optional backup drive or folder for `backup_mods.py`               | not set: backup disabled |
| FS25_KINGMODS_DB      | optional local SQLite database for the search tab                  | `$FS25_LIBRARY_DIR/scraper/kingmods_fs25.db` |
| FS25_NICKNAME         | player name written in a new savegame                              | `Player` |
| FS25_FARM_NAME        | farm name written in a new savegame                                | `My Farm` |
"""

import json
import os
from pathlib import Path

STEAM_APP_ID = "2300320"  # Farming Simulator 25 on Steam
_PROFILE_TAIL = Path("drive_c/users/steamuser/Documents/My Games/FarmingSimulator2025")


def _home():
    return Path(os.path.expanduser("~"))


def _xdg(var, fallback):
    val = os.environ.get(var)
    return Path(val) if val else _home() / fallback


def _file_config():
    path = _xdg("XDG_CONFIG_HOME", ".config") / "fs25-mod-manager" / "config.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


_FILE = _file_config()


def get(name, default=None):
    """Environment variable, then config file, then default. '~' is expanded."""
    val = os.environ.get(name)
    if val is None:
        val = _FILE.get(name)
    if val in (None, ""):
        return default
    return os.path.expanduser(str(val))


def profile_candidates():
    """Usual places of the FS25 profile under Steam + Proton (native Steam, Flatpak Steam, Steam Deck)."""
    steam_roots = [
        _home() / ".local/share/Steam",
        _home() / ".steam/steam",
        _home() / ".var/app/com.valvesoftware.Steam/.local/share/Steam",
    ]
    return [root / "steamapps/compatdata" / STEAM_APP_ID / "pfx" / _PROFILE_TAIL for root in steam_roots]


def profile_dir():
    val = get("FS25_PROFILE_DIR")
    if val:
        return Path(val)
    cands = profile_candidates()
    for c in cands:
        if c.is_dir():
            return c
    return cands[0]


def game_mods_dir():
    val = get("FS25_GAME_MODS_DIR")
    return Path(val) if val else profile_dir() / "mods"


def library_dir():
    val = get("FS25_LIBRARY_DIR")
    return Path(val) if val else _xdg("XDG_DATA_HOME", ".local/share") / "fs25-mod-manager" / "library"


def launcher():
    val = get("FS25_LAUNCHER")
    return Path(val) if val else None


def backup_dir():
    val = get("FS25_BACKUP_DIR")
    return Path(val) if val else None


def kingmods_db():
    val = get("FS25_KINGMODS_DB")
    return Path(val) if val else library_dir() / "scraper" / "kingmods_fs25.db"


def nickname():
    return get("FS25_NICKNAME", "Player")


def farm_name():
    return get("FS25_FARM_NAME", "My Farm")


if __name__ == "__main__":
    for k, v in (("FS25_PROFILE_DIR", profile_dir()), ("FS25_GAME_MODS_DIR", game_mods_dir()),
                 ("FS25_LIBRARY_DIR", library_dir()), ("FS25_LAUNCHER", launcher()),
                 ("FS25_BACKUP_DIR", backup_dir()), ("FS25_KINGMODS_DB", kingmods_db()),
                 ("FS25_NICKNAME", nickname()), ("FS25_FARM_NAME", farm_name())):
        print(f"{k:20} {v}")
