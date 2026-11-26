from copy import deepcopy
from pathlib import Path
import json
from internal.logger import configure_logging, get_logger

logger = get_logger(__name__)

SETTING_PATH = Path.cwd() / "settings.json"

DEFAULT_SETTINGS: dict = {
    "app": {
        "download_folder": "Music",
        "max_log_lines": 1000,
    },
    "yt_downloader": {
        "cookie_file": "cookies.txt",
    },
    "slm": {
        "base_url": "http://localhost:11434",
        "model": "phi4-mini",
        "keep_alive": "5m",
        "timeout": 60,
    },
    "searxng": {
        "enabled": True,
        "base_url": "http://localhost:8080",
        "timeout": 10,
        "max_results": 5,
        "categories": "general",
    },
}


def _is_valid_value(key: str, value, default_value) -> bool:
    if isinstance(default_value, bool):
        return isinstance(value, bool)
    if isinstance(default_value, int):
        if not isinstance(value, int) or isinstance(value, bool):
            return False
        if key in ("max_log_lines", "timeout", "max_results") and value <= 0:
            return False
        return True
    if isinstance(default_value, str):
        return isinstance(value, str) and bool(value.strip())
    return isinstance(value, type(default_value))


def _sanitize_settings(user_data: dict, defaults: dict) -> tuple[dict, bool]:
    """
    Keeps only valid keys defined in defaults with valid types/values.
    Drops unknown/nonsense keys or invalid values and flags whether cleanup occurred.
    """
    cleaned: dict = {}
    changed = False

    for key in user_data:
        if key not in defaults:
            changed = True

    for key, default_val in defaults.items():
        if key not in user_data:
            cleaned[key] = deepcopy(default_val)
            changed = True
            continue

        user_val = user_data[key]
        if isinstance(default_val, dict):
            if isinstance(user_val, dict):
                sub_cleaned, sub_changed = _sanitize_settings(user_val, default_val)
                cleaned[key] = sub_cleaned
                if sub_changed:
                    changed = True
            else:
                cleaned[key] = deepcopy(default_val)
                changed = True
        else:
            if _is_valid_value(key, user_val, default_val):
                cleaned[key] = user_val
            else:
                cleaned[key] = deepcopy(default_val)
                changed = True

    return cleaned, changed


def create_default_settings(path: Path = SETTING_PATH) -> dict:
    defaults = deepcopy(DEFAULT_SETTINGS)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(defaults, f, indent=4)
    configure_logging(defaults["app"]["max_log_lines"])
    logger.info(f"Created default settings file at {path}.")
    return defaults


def get_settings() -> dict:
    try:
        if not SETTING_PATH.exists():
            logger.warning(f"Settings file not found at {SETTING_PATH}. Recreating default settings.json.")
            return create_default_settings(SETTING_PATH)

        with open(SETTING_PATH, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        if not isinstance(loaded, dict):
            logger.warning("settings.json root is not a JSON object. Recreating default settings.json.")
            return create_default_settings(SETTING_PATH)

        cleaned, changed = _sanitize_settings(loaded, DEFAULT_SETTINGS)
        if changed:
            with open(SETTING_PATH, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=4)
            logger.info(f"Sanitized settings.json (dropped invalid/unknown entries) at {SETTING_PATH}.")

        configure_logging(cleaned["app"]["max_log_lines"])
        return cleaned
    except Exception as e:
        logger.error(f"Error loading settings from {SETTING_PATH}. Error: {e}")
        raise
