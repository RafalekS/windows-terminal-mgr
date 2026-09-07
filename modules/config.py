"""Application configuration - loaded from / saved to config/settings.json.

``APP_CONFIG`` is a module attribute that is mutated and (in the Settings tab)
reassigned at runtime. Always reference it as ``config.APP_CONFIG``.
"""

import json
from pathlib import Path

# Directory of the project (parent of this package).
SCRIPT_DIR = Path(__file__).resolve().parent.parent

_DEFAULT_CONFIG = {
    "window": {"width": 1400, "height": 900, "min_width": 1200, "min_height": 700},
    "profiles_panel": {"min_width": 250, "max_width": 300},
    "defaults": {"font_size": 12, "history_size": 9001},
    "backup": {"enabled": True, "max_count": 10},
    "theme": "light",
    "wt_path_override": "",
}


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _config_path() -> Path:
    return SCRIPT_DIR / "config" / "settings.json"


def load_app_config() -> dict:
    path = _config_path()
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            return _deep_merge(_DEFAULT_CONFIG, loaded)
        except (OSError, ValueError) as e:
            print(f"Config load error: {e}")
    return _DEFAULT_CONFIG.copy()


def save_app_config(cfg: dict) -> bool:
    path = _config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except OSError as e:
        print(f"Config save error: {e}")
        return False


APP_CONFIG = load_app_config()
