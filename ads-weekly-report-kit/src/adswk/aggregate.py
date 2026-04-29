from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AggregateProfile:
    effective_level: str
    date_filter_applied: bool
    warnings: list[str]


def _parse_iso_date(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _compute_rates(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    spend = out["spend"].astype(float)
    impressions = out["impressions"].astype(float)
    clicks = out["link_clicks"].astype(float)

    out["ctr"] = np.where(impressions > 0, clicks / impressions, 0.0)
    out["cpc"] = np.where(clicks > 0, spend / clicks, np.nan)
    out["cpm"] = np.where(impressions > 0, spend / impressions * 1000.0, np.nan)

    if "purchase_value" in out.columns:
        pv = out["purchase_value"].astype(float)
        out["observed_roas"] = np.where(spend > 0, pv / spend, np.nan)

    return out


def aggregate_summary(
    df: pd.DataFrame,
    *,
    level: str = "campaign",
    start: str | None = None,
    end: str | None = None,
) -> tuple[pd.DataFrame, AggregateProfile]:
    warnings: list[str] = []
    work = df.copy()

    date_filter_applied = False
    if (start or end) and "date" in work.columns and work["date"].notna().sum() > 0:
        start_dt = _parse_iso_date(start) if start else None
        end_dt = _parse_iso_date(end) if end else None
        if start_dt is not None:
            work = work[work["date"] >= start_dt]
        if end_dt is not None:
            work = work[work["date"] <= end_dt]
        date_filter_applied = True
    elif start or end:
        warnings.append("Start/end ignored because date column is missing or not parseable.")

    requested_level = level.strip().lower()
    if requested_level not in {"campaign", "adset", "ad", "account"}:
        raise ValueError("level must be one of: campaign, adset, ad, account")

    effective_level = requested_level
    if requested_level == "account":
        group_col = "__account"
        work[group_col] = "account"
        group_keys = [group_col]
    else:
        if requested_level not in work.columns or work[requested_level].astype(str).str.strip().eq("").all():
            warnings.append(f"Level '{requested_level}' not found; aggregated at account level.")
            effective_level = "account"
            group_col = "__account"
            work[group_col] = "account"
            group_keys = [group_col]
        else:
            group_keys = [requested_level]

    sum_cols = ["spend", "impressions", "link_clicks"]
    for optional in ("purchase_value", "purchases"):
        if optional in work.columns:
            sum_cols.append(optional)

    grouped = work.groupby(group_keys, dropna=False)[sum_cols].sum(numeric_only=True).reset_index()
    grouped = grouped.rename(columns={grouped.columns[0]: effective_level})
    grouped = _compute_rates(grouped)
    grouped = grouped.sort_values("spend", ascending=False)
    return grouped, AggregateProfile(effective_level=effective_level, date_filter_applied=date_filter_applied, warnings=warnings)


def daily_totals(df: pd.DataFrame) -> pd.DataFrame | None:
    if "date" not in df.columns or df["date"].notna().sum() == 0:
        return None
    work = df.copy()
    work = work[work["date"].notna()]
    work["date_day"] = pd.to_datetime(work["date"]).dt.date

    sum_cols = ["spend", "impressions", "link_clicks"]
    if "purchase_value" in work.columns:
        sum_cols.append("purchase_value")

    daily = work.groupby("date_day")[sum_cols].sum(numeric_only=True).reset_index().rename(columns={"date_day": "date"})
    daily = _compute_rates(daily)
    daily = daily.sort_values("date")
    return daily

