from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd

from . import AdsWkError


@dataclass(frozen=True)
class NormalizeProfile:
    date_parse_failed_rows: int
    date_parse_total_rows: int
    warnings: list[str]


_MISSING_TOKENS = {"", " ", "nan", "na", "n/a", "none", "null", "--", "—"}
_MONEY_KEEP_RE = re.compile(r"[^0-9.\-]")


def _as_str_series(series: pd.Series) -> pd.Series:
    if series.dtype == "string":
        s = series
    else:
        s = series.astype("string")
    return s.fillna(pd.NA)


def _to_money(series: pd.Series) -> pd.Series:
    s = _as_str_series(series).str.strip()
    s = s.mask(s.str.lower().isin(_MISSING_TOKENS), other=pd.NA)
    neg = s.str.startswith("(") & s.str.endswith(")")
    s = s.str.replace(r"^\((.*)\)$", r"\1", regex=True)
    s = s.str.replace(",", "", regex=False)
    s = s.str.replace(_MONEY_KEEP_RE, "", regex=True)
    out = pd.to_numeric(s, errors="coerce")
    out = out.where(~neg, -out)
    return out


def _to_number(series: pd.Series) -> pd.Series:
    s = _as_str_series(series).str.strip()
    s = s.mask(s.str.lower().isin(_MISSING_TOKENS), other=pd.NA)
    s = s.str.replace(",", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def _to_date(series: pd.Series) -> tuple[pd.Series, int, int]:
    s = _as_str_series(series).str.strip()
    s = s.mask(s.str.lower().isin(_MISSING_TOKENS), other=pd.NA)
    dt = pd.to_datetime(s, errors="coerce")
    total = int(s.notna().sum())
    failed = int((s.notna() & dt.isna()).sum())
    if getattr(dt.dt, "tz", None) is not None:
        dt = dt.dt.tz_localize(None)
    return dt, failed, total


def normalize_dataframe(
    df: pd.DataFrame,
    template: dict[str, Any],
    mapping: dict[str, str],
    *,
    fill_numeric: float = 0.0,
    fill_text: str = "",
) -> tuple[pd.DataFrame, NormalizeProfile]:
    fields = template.get("fields")
    if not isinstance(fields, dict):
        raise AdsWkError("Template YAML must contain a 'fields' mapping.")

    out = df.copy()
    warnings: list[str] = []

    date_failed = 0
    date_total = 0

    for std_field, source_col in mapping.items():
        cfg_any = fields.get(std_field, {})
        cfg = cfg_any if isinstance(cfg_any, dict) else {}
        ftype = str(cfg.get("type", "str")).strip().lower()

        if source_col not in out.columns:
            continue
        raw = out[source_col]

        if ftype == "money":
            cleaned = _to_money(raw).fillna(fill_numeric).astype(float)
            out[std_field] = cleaned
        elif ftype == "int":
            cleaned = _to_number(raw).fillna(fill_numeric)
            out[std_field] = cleaned.astype(float)
        elif ftype == "float":
            cleaned = _to_number(raw).fillna(fill_numeric).astype(float)
            out[std_field] = cleaned
        elif ftype == "date":
            dt, failed, total = _to_date(raw)
            out[std_field] = dt
            date_failed += failed
            date_total += total
            if failed > 0:
                out[f"{std_field}_raw"] = _as_str_series(raw).fillna(fill_text)
        else:
            out[std_field] = _as_str_series(raw).fillna(fill_text).astype(str)

    for col in ("campaign", "adset", "ad"):
        if col in out.columns:
            out[col] = _as_str_series(out[col]).fillna(fill_text).astype(str)

    if "date" in out.columns:
        if out["date"].notna().sum() == 0 and date_total > 0:
            warnings.append("Date parse failed; trend disabled.")
        elif date_failed > 0:
            warnings.append(f"{date_failed}/{date_total} date values failed to parse; trends exclude those rows.")

    return out, NormalizeProfile(
        date_parse_failed_rows=date_failed,
        date_parse_total_rows=date_total,
        warnings=warnings,
    )
