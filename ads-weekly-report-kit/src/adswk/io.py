from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd

from . import AdsWkError


@dataclass(frozen=True)
class CSVReadProfile:
    encoding: str
    delimiter: str
    row_count: int
    original_columns: list[str]
    canonical_columns: list[str]


_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def canonicalize_column_name(name: object) -> str:
    s = "" if name is None else str(name)
    s = s.strip().lower()
    s = _NON_ALNUM_RE.sub("_", s)
    s = s.strip("_")
    s = re.sub(r"_+", "_", s)
    return s


def _dedupe_columns(columns: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    out: list[str] = []
    for col in columns:
        base = col or "col"
        if base not in seen:
            seen[base] = 1
            out.append(base)
            continue
        seen[base] += 1
        out.append(f"{base}_{seen[base]}")
    return out


def _sniff_delimiter(sample: str) -> str | None:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";"])
        if dialect.delimiter in {",", ";"}:
            return dialect.delimiter
    except Exception:
        return None
    return None


def detect_delimiter(path: Path) -> Literal[",", ";"]:
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        sample = f.read(4096)
    sniffed = _sniff_delimiter(sample)
    if sniffed in {",", ";"}:
        return sniffed  # type: ignore[return-value]

    header_line = sample.splitlines()[0] if sample.splitlines() else ""
    comma_count = header_line.count(",")
    semi_count = header_line.count(";")
    return ";" if semi_count > comma_count else ","


def read_csv_flexible(path: Path, verbose: bool = False) -> tuple[pd.DataFrame, CSVReadProfile]:
    if not path.exists():
        raise AdsWkError(f"Input file not found: {path}")
    if path.suffix.lower() != ".csv":
        raise AdsWkError("v0.1 only supports CSV input (Meta export as CSV).")

    detected = detect_delimiter(path)
    delimiters: list[str] = [detected, ";" if detected == "," else ","]
    last_error: Exception | None = None
    for delimiter in delimiters:
        for encoding in ("utf-8-sig", "utf-8"):
            try:
                df = pd.read_csv(
                    path,
                    sep=delimiter,
                    encoding=encoding,
                    dtype=str,
                    engine="python",
                )
                if df.shape[1] <= 1 and delimiter != delimiters[-1]:
                    continue

                original_columns = [str(c) for c in df.columns.tolist()]
                canonical_columns = _dedupe_columns([canonicalize_column_name(c) for c in original_columns])
                df.columns = canonical_columns
                return df, CSVReadProfile(
                    encoding=encoding,
                    delimiter=delimiter,
                    row_count=int(len(df)),
                    original_columns=original_columns,
                    canonical_columns=canonical_columns,
                )
            except UnicodeDecodeError as e:
                last_error = e
                continue
    raise AdsWkError(f"Failed to read CSV as UTF-8/UTF-8-SIG. Error: {last_error}")
