import json
import os
from internal.log_time import logTime
import pathlib

def _load_json_object(file_path: str) -> dict:
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception as e:
            logTime(f"Error loading JSON from {file_path}. Error: {e}", level="ERR")
            raise
    return {}

def clean_up_metadata_recursively(data):
    """
    Recursively traverses the metadata dictionary and removes any keys with None values.
    """
    if isinstance(data, dict):
        return {k: clean_up_metadata_recursively(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [clean_up_metadata_recursively(item) for item in data if item is not None]
    else:
        return data

def append_metadata(file_path: str, music_id: str, metadata: dict, full_path: str) -> None:
    data = _load_json_object(file_path)
    data[music_id] = {
        "metadata": clean_up_metadata_recursively(metadata),
        "parent": str(pathlib.Path(full_path).parent),
        "filename": pathlib.Path(full_path).stem,
        "extension": pathlib.Path(full_path).suffix
    }
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logTime(f"Metadata for '{music_id}' appended to {file_path}", level="INF")
    except Exception as e:
        logTime(f"Error writing metadata to {file_path}. Error: {e}", level="ERR")
        raise