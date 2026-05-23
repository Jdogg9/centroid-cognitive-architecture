from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_wheel_install_exposes_public_cli_resources(tmp_path: Path) -> None:
    dist_dir = tmp_path / "dist"
    venv_dir = tmp_path / "venv"
    run_dir = tmp_path / "run"
    run_dir.mkdir()

    _run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(dist_dir)])
    wheel = next(dist_dir.glob("*.whl"))

    _run([sys.executable, "-m", "venv", str(venv_dir)])
    python_bin = _venv_bin(venv_dir, "python")
    _run([str(python_bin), "-m", "pip", "install", "--no-index", str(wheel)])

    _run(
        [str(_venv_bin(venv_dir, "centroid-holly")), "--scenario", "project-companion"], cwd=run_dir
    )
    _run(
        [
            str(python_bin),
            "-c",
            (
                "from core.models import get_provider_config; "
                "c=get_provider_config('mock'); "
                "assert c.provider_id == 'mock'"
            ),
        ],
        cwd=run_dir,
    )
    _run(
        [
            str(_venv_bin(venv_dir, "centroid-agent")),
            "--config",
            "templates/minimal_agent.json",
            "--scenario",
            "project-companion",
            "--provider",
            "mock",
        ],
        cwd=run_dir,
    )
    _run(
        [
            str(_venv_bin(venv_dir, "centroid-holly")),
            "--scenario",
            "project-companion",
            "--provider",
            "mock",
        ],
        cwd=run_dir,
    )
    _run([str(_venv_bin(venv_dir, "centroid-eval"))], cwd=run_dir)
    _run([str(_venv_bin(venv_dir, "centroid-demo")), "--mode", "full"], cwd=run_dir)
    _run([str(_venv_bin(venv_dir, "centroid-provider-demo"))], cwd=run_dir)
    _run([str(_venv_bin(venv_dir, "centroid-provider-comparison"))], cwd=run_dir)
    _run(
        [
            str(python_bin),
            "-c",
            "from examples.run_config_comparison import main; raise SystemExit(main())",
        ],
        cwd=run_dir,
    )


def _run(command: list[str], *, cwd: Path = REPO_ROOT) -> None:
    subprocess.run(command, cwd=cwd, check=True)


def _venv_bin(venv_dir: Path, executable: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{executable}.exe"
    return venv_dir / "bin" / executable
