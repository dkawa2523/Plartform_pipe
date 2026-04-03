"""Contract linting utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

__all__ = ["REQUIRED_ARTIFACTS", "lint_contract", "assert_contract"]

REQUIRED_ARTIFACTS = (
    "config_resolved.yaml",
    "out.json",
    "manifest.json",
)


def lint_contract(
    *,
    output_dir: str | Path,
    required_artifacts: Iterable[str] | None = None,
) -> list[str]:
    """Return missing contract artifacts for the given output dir."""
    output_path = Path(output_dir)
    required = tuple(required_artifacts) if required_artifacts is not None else REQUIRED_ARTIFACTS
    missing: list[str] = []
    if not output_path.exists():
        return list(required)
    for name in required:
        if not (output_path / name).exists():
            missing.append(name)
    return missing


def assert_contract(
    *,
    output_dir: str | Path,
    required_artifacts: Iterable[str] | None = None,
) -> None:
    """Raise if required contract artifacts are missing."""
    missing = lint_contract(output_dir=output_dir, required_artifacts=required_artifacts)
    if not missing:
        return
    output_path = Path(output_dir)
    lines = [
        "Contract artifacts missing:",
        f"output_dir={output_path}",
        *[f"- {name}" for name in missing],
    ]
    raise RuntimeError("\n".join(lines))
