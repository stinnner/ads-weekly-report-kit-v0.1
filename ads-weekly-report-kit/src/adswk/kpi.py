from __future__ import annotations

import numpy as np
import pandas as pd

from . import AdsWkError


def add_kpi_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not {"spend", "impressions", "link_clicks"}.issubset(df.columns):
        raise AdsWkError("Internal error: KPI requires spend/impressions/link_clicks columns.")

    out = df.copy()
    spend = pd.to_numeric(out["spend"], errors="coerce").fillna(0.0).astype(float)
    impressions = pd.to_numeric(out["impressions"], errors="coerce").fillna(0.0).astype(float)
    clicks = pd.to_numeric(out["link_clicks"], errors="coerce").fillna(0.0).astype(float)

    out["ctr"] = np.where(impressions > 0, clicks / impressions, 0.0).astype(float)
    out["cpc"] = np.where(clicks > 0, spend / clicks, np.nan).astype(float)
    out["cpm"] = np.where(impressions > 0, spend / impressions * 1000.0, np.nan).astype(float)

    if "purchase_value" in out.columns:
        purchase_value = pd.to_numeric(out["purchase_value"], errors="coerce").fillna(0.0).astype(float)
        out["observed_roas"] = np.where(spend > 0, purchase_value / spend, np.nan).astype(float)

    if "website_purchase_roas" in out.columns:
        out["website_purchase_roas"] = pd.to_numeric(out["website_purchase_roas"], errors="coerce")

    return out

