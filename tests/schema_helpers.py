from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_schema(name: str) -> dict:
    path = REPO_ROOT / "schemas" / name
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def validate_schema(name: str, payload: dict) -> None:
    schema = load_schema(name)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(payload)

