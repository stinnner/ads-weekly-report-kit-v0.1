from __future__ import annotations

import base64
from io import BytesIO

import matplotlib

matplotlib.use("Agg")

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


def _fig_to_base64(fig: plt.Figure) -> str:
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=160)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def spend_clicks_trend(daily: pd.DataFrame) -> str:
    x = pd.to_datetime(daily["date"])
    spend = daily["spend"].astype(float)
    clicks = daily["link_clicks"].astype(float)

    fig, ax1 = plt.subplots(figsize=(8.5, 3.2))
    ax1.plot(x, spend, color="#2563eb", linewidth=2, label="Spend")
    ax1.set_ylabel("Spend")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x, clicks, color="#16a34a", linewidth=2, label="Link Clicks")
    ax2.set_ylabel("Link Clicks")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax1.set_title("Spend & Link Clicks (Daily)")

    return _fig_to_base64(fig)


def ctr_cpc_trend(daily: pd.DataFrame) -> str:
    x = pd.to_datetime(daily["date"])
    ctr_pct = daily["ctr"].astype(float) * 100.0
    cpc = daily["cpc"].astype(float)

    fig, ax1 = plt.subplots(figsize=(8.5, 3.2))
    ax1.plot(x, ctr_pct, color="#9333ea", linewidth=2, label="CTR (%)")
    ax1.set_ylabel("CTR (%)")
    ax1.grid(True, axis="y", linestyle="--", alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(x, cpc, color="#f97316", linewidth=2, label="CPC")
    ax2.set_ylabel("CPC")

    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax1.set_title("CTR & CPC (Daily)")

    return _fig_to_base64(fig)

