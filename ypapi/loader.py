"""Load YAML or JSON documents."""

import json
from pathlib import Path
from typing import Any

import yaml


class LoadError(Exception):
    pass


def load_document(path: str | Path) -> Any:
    path = Path(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LoadError(f"cannot read {path}: {exc.strerror}") from exc
    try:
        if path.suffix.lower() == ".json":
            return json.loads(text)
        return yaml.safe_load(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise LoadError(f"{path}: not valid {'JSON' if path.suffix.lower() == '.json' else 'YAML'}: {exc}") from exc
