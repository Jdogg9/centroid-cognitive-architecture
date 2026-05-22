from __future__ import annotations

from importlib import resources
from pathlib import Path

RESOURCE_ROOTS = {
    "configs": "configs",
    "evaluation": "evaluation",
    "schemas": "schemas",
    "templates": "templates",
}


def read_text_resource_or_file(path: Path | str) -> str:
    candidate = Path(path)
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")

    package, resource_name = _resource_package_and_name(candidate)
    return resources.files(package).joinpath(resource_name).read_text(encoding="utf-8")


def _resource_package_and_name(path: Path) -> tuple[str, str]:
    parts = path.parts
    if len(parts) < 2 or parts[0] not in RESOURCE_ROOTS:
        raise FileNotFoundError(f"resource or file not found: {path}")

    package = ".".join(parts[:-1])
    resource_name = parts[-1]
    return package, resource_name
