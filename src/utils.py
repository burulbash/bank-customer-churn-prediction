from __future__ import annotations

from pathlib import Path

from .config import ARTIFACT_DIRS


def ensure_artifact_dirs() -> None:
    for directory in ARTIFACT_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


def validate_columns(columns: list[str] | set[str], required: list[str]) -> None:
    missing = sorted(set(required) - set(columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def safe_write_csv(df, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
