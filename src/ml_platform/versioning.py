"""Versioning helpers for platform metadata."""

from __future__ import annotations

from importlib import metadata as importlib_metadata
from pathlib import Path
import subprocess
from typing import Any

from ml_platform.common.config_utils import cfg_value as _cfg_value

__all__ = ["get_platform_version", "get_code_version", "get_schema_version"]

_SCHEMA_VERSION_PATHS = (
    "schema_version",
    "schema.version",
    "data.schema_version",
    "data.schema.version",
    "task.schema_version",
    "task.schema.version",
)


def get_platform_version() -> str:
    for dist_name in ("ml-platform", "ml_platform"):
        try:
            return importlib_metadata.version(dist_name)
        except importlib_metadata.PackageNotFoundError:
            continue
    version = _read_pyproject_version()
    return version or "unknown"


def get_code_version(repo_root: str | Path | None = None) -> str:
    root = _resolve_repo_root(repo_root)
    if root is None:
        return "unknown"
    revision = _git_rev_parse(root)
    return revision or "unknown"


def get_schema_version(cfg: Any, default: str = "unknown") -> str:
    for path in _SCHEMA_VERSION_PATHS:
        value = _cfg_value(cfg, path)
        if value is not None:
            return str(value)
    return default


def _resolve_repo_root(repo_root: str | Path | None) -> Path | None:
    if repo_root is not None:
        base = Path(repo_root)
        return _find_repo_root(base)
    for base in (Path.cwd(), Path(__file__).resolve()):
        root = _find_repo_root(base)
        if root is not None:
            return root
    return None


def _find_repo_root(start: Path) -> Path | None:
    current = start if start.is_dir() else start.parent
    for parent in (current, *current.parents):
        if (parent / ".git").exists():
            return parent
    for parent in (current, *current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    return None


def _git_rev_parse(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    sha = result.stdout.strip()
    return sha or None


def _read_pyproject_version() -> str | None:
    root = _find_repo_root(Path(__file__).resolve())
    if root is None:
        return None
    path = root / "pyproject.toml"
    if not path.exists():
        return None
    text = None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    try:
        import tomllib  # type: ignore

        data = tomllib.loads(text)
        version = data.get("project", {}).get("version")
        if version:
            return str(version)
    except (AttributeError, ModuleNotFoundError, TypeError, ValueError):
        pass
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("version"):
            _, _, value = stripped.partition("=")
            value = value.strip().strip('"').strip("'")
            if value:
                return value
    return None
