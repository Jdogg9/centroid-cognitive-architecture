"""Code encoder — extract structure, signatures, and documentation from
Python source files. Uses only ast + pathlib — no imports of target modules.
"""

from __future__ import annotations

import ast
import time
from pathlib import Path

from nodes.sensory_node import PerceivedText


class CodeEncoder:
    """Extract semantic structure from Python source files."""

    def encode_file(self, path: str | Path) -> PerceivedText | None:
        """Read a .py file and extract its structure as PerceivedText.

        Returns None if the file doesn't exist or isn't a .py file.
        """
        p = Path(path)
        if not p.exists() or p.suffix != ".py":
            return None

        try:
            source = p.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

        tree = ast.parse(source)
        source_id = self._source_id_for_file(p)
        source_lines = source.splitlines()

        signatures: list[str] = []
        docstrings: list[str] = []
        comments: list[str] = []

        for node in ast.walk(tree):
            # Module docstring
            if isinstance(node, ast.Module):
                ds = ast.get_docstring(node)
                if ds:
                    docstrings.append(f"module:{ds[:200]}")

            # Functions
            elif isinstance(node, (ast.AsyncFunctionDef, ast.FunctionDef)):
                line = source_lines[node.lineno - 1].strip()
                if line:
                    signatures.append(line[:200])
                ds = ast.get_docstring(node)
                if ds:
                    docstrings.append(f"{node.name}:{ds[:100]}")

            # Classes
            elif isinstance(node, ast.ClassDef):
                line = source_lines[node.lineno - 1].strip()
                if line:
                    signatures.append(line[:200])
                ds = ast.get_docstring(node)
                if ds:
                    docstrings.append(f"{node.name}:{ds[:100]}")

        # Extract comments (lines starting with #)
        for line in source.split("\n"):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                comment = stripped.lstrip("#").strip()
                if len(comment) > 5:
                    comments.append(comment[:80])

        content_parts: list[str] = [source_id]
        if signatures:
            content_parts.append(" | ".join(signatures[:20]))
        if docstrings:
            content_parts.append(" | ".join(docstrings[:10]))
        if comments:
            content_parts.append(" | ".join(comments[:10]))

        content = " ".join(content_parts)

        return PerceivedText(
            source_kind="code",
            content=content,
            source_id=source_id,
            timestamp=time.time(),
        )

    def encode_directory(
        self, root: str | Path, max_files: int = 50
    ) -> list[PerceivedText]:
        """Recursively walk root, encode all .py files up to max_files.

        Skips __pycache__, .git, and tests/ directories.
        """
        skip_dirs = {"__pycache__", ".git", "tests", "test", ".pytest_cache"}
        root_path = Path(root)
        results: list[PerceivedText] = []

        for p in sorted(root_path.rglob("*.py")):
            if any(skip in p.parts for skip in skip_dirs):
                continue
            perceived = self.encode_file(p)
            if perceived is not None:
                # Rebase source_id to be relative to root
                perceived.source_id = str(p.relative_to(root_path))
                results.append(perceived)
            if len(results) >= max_files:
                break

        return results

    @staticmethod
    def _source_id_for_file(path: Path) -> str:
        """Return a stable relative source identifier when possible."""
        if not path.is_absolute():
            return str(path)

        cwd = Path.cwd().resolve()
        resolved = path.resolve()
        try:
            return str(resolved.relative_to(cwd))
        except ValueError:
            return path.name
