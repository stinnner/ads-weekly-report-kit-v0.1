from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
from jinja2 import Template


@dataclass(frozen=True)
class ReportContext:
    title: str
    generated_at: str
    level: str
    date_range: str
    kpis: dict[str, Any]
    charts: dict[str, str]
    top_rows: list[dict[str, Any]]
    anomalies: list[str]
    notes: list[str]


_HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{{ ctx.title }}</title>
  <style>
    :root { --bg:#0b1220; --card:#111a2e; --muted:#94a3b8; --text:#e2e8f0; --accent:#60a5fa; --border:#1f2a44; }
    body { margin:0; font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial; background:linear-gradient(180deg,#070b14,#0b1220 30%); color:var(--text); }
    .wrap { max-width:1100px; margin:0 auto; padding:28px 18px 40px; }
    h1 { margin:0 0 6px; font-size:24px; }
    .sub { color:var(--muted); font-size:13px; margin-bottom:18px; }
    .grid { display:grid; grid-template-columns: repeat(6, minmax(0,1fr)); gap:10px; }
    .card { background:rgba(17,26,46,.85); border:1px solid var(--border); border-radius:14px; padding:12px 12px; }
    .label { color:var(--muted); font-size:12px; margin-bottom:6px; }
    .value { font-size:18px; font-weight:650; letter-spacing:.2px; }
    .section { margin-top:18px; }
    .section h2 { font-size:16px; margin:0 0 10px; }
    .panel { background:rgba(17,26,46,.6); border:1px solid var(--border); border-radius:14px; padding:14px; }
    .charts { display:grid; grid-template-columns:1fr; gap:12px; }
    img { max-width:100%; border-radius:10px; border:1px solid rgba(255,255,255,.08); }
    table { width:100%; border-collapse:collapse; }
    th, td { text-align:left; padding:8px 10px; border-bottom:1px solid rgba(255,255,255,.08); font-size:13px; }
    th { color:var(--muted); font-weight:600; }
    .muted { color:var(--muted); }
    .pill { display:inline-block; padding:3px 8px; border:1px solid rgba(96,165,250,.35); color:var(--accent); border-radius:999px; font-size:12px; }
    ul { margin: 8px 0 0 18px; }
    code { background:rgba(255,255,255,.06); padding:2px 6px; border-radius:8px; }
    @media (max-width: 900px) { .grid { grid-template-columns: repeat(2, minmax(0,1fr)); } }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>{{ ctx.title }}</h1>
    <div class="sub">
      <span class="pill">Level: {{ ctx.level }}</span>
      &nbsp;•&nbsp; Date range: {{ ctx.date_range }}
      &nbsp;•&nbsp; Generated: {{ ctx.generated_at }}
    </div>

    <div class="section">
      <h2>KPI Summary</h2>
      <div class="grid">
        {% for item in ctx.kpis.cards %}
        <div class="card">
          <div class="label">{{ item.label }}</div>
          <div class="value">{{ item.value }}</div>
          {% if item.note %}<div class="muted" style="font-size:12px;margin-top:6px">{{ item.note }}</div>{% endif %}
        </div>
        {% endfor %}
      </div>
    </div>

    <div class="section">
      <h2>Trends</h2>
      <div class="panel">
        {% if ctx.charts.spend_clicks and ctx.charts.ctr_cpc %}
          <div class="charts">
            <img alt="Spend and Link Clicks trend" src="data:image/png;base64,{{ ctx.charts.spend_clicks }}">
            <img alt="CTR and CPC trend" src="data:image/png;base64,{{ ctx.charts.ctr_cpc }}">
          </div>
        {% else %}
          <div class="muted">Date parse failed or date column missing; trend disabled.</div>
        {% endif %}
      </div>
    </div>

    <div class="section">
      <h2>Top 10 (by Spend)</h2>
      <div class="panel">
        {% if ctx.top_rows %}
        <table>
          <thead>
            <tr>
              <th>{{ ctx.level }}</th>
              <th>Spend</th>
              <th>Impressions</th>
              <th>Link Clicks</th>
              <th>CTR</th>
              <th>CPC</th>
              <th>CPM</th>
            </tr>
          </thead>
          <tbody>
            {% for r in ctx.top_rows %}
            <tr>
              <td>{{ r.level }}</td>
              <td>{{ r.spend }}</td>
              <td>{{ r.impressions }}</td>
              <td>{{ r.link_clicks }}</td>
              <td>{{ r.ctr }}</td>
              <td>{{ r.cpc }}</td>
              <td>{{ r.cpm }}</td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% else %}
          <div class="muted">Top table unavailable at account level or missing grouping field.</div>
        {% endif %}
      </div>
    </div>

    <div class="section">
      <h2>Anomaly Hints (rule-based)</h2>
      <div class="panel">
        {% if ctx.anomalies %}
          <ul>
            {% for a in ctx.anomalies %}
              <li>{{ a }}</li>
            {% endfor %}
          </ul>
        {% else %}
          <div class="muted">No anomalies detected (with the simple v0.1 rules).</div>
        {% endif %}
      </div>
    </div>

    <div class="section">
      <h2>KPI Definitions (Meta-aligned)</h2>
      <div class="panel">
        <ul>
          <li><b>CTR (link click-through rate)</b> = <code>link_clicks / impressions</code> (if impressions=0 → 0)</li>
          <li><b>CPC (cost per link click)</b> = <code>spend / link_clicks</code> (if link_clicks=0 → NaN)</li>
          <li><b>CPM (cost per 1,000 impressions)</b> = <code>spend / impressions * 1000</code> (if impressions=0 → NaN)</li>
          <li><b>ROAS</b>: if <code>website_purchase_roas</code> is missing, the report shows <i>Observed ROAS (derived)</i> = <code>purchase_value / spend</code>.</li>
        </ul>
        {% if ctx.notes %}
          <div style="margin-top:10px" class="muted">
            {% for n in ctx.notes %}
              <div>• {{ n }}</div>
            {% endfor %}
          </div>
        {% endif %}
      </div>
    </div>
  </div>
</body>
</html>
"""
)


def _format_int(value: float) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    return f"{int(round(float(value))):,}"


def _format_money(value: float) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    return f"${float(value):,.2f}"


def _format_pct(value: float) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    return f"{float(value) * 100:.2f}%"


def _format_float(value: float, *, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "—"
    return f"{float(value):,.{digits}f}"


def _build_anomalies(daily: pd.DataFrame | None) -> list[str]:
    if daily is None or len(daily) < 3:
        return []

    tail = daily.tail(7).copy()
    median_ctr = float(np.nanmedian(tail["ctr"].astype(float))) if tail["ctr"].notna().any() else float("nan")
    median_cpc = float(np.nanmedian(tail["cpc"].astype(float))) if tail["cpc"].notna().any() else float("nan")

    last = daily.iloc[-1]
    last_ctr = float(last["ctr"]) if pd.notna(last["ctr"]) else float("nan")
    last_cpc = float(last["cpc"]) if pd.notna(last["cpc"]) else float("nan")

    hints: list[str] = []
    x = 0.20

    if np.isfinite(median_ctr) and median_ctr > 0 and np.isfinite(last_ctr):
        if last_ctr < median_ctr * (1 - x):
            hints.append(
                f"CTR is low: {last_ctr*100:.2f}% vs 7-day median {median_ctr*100:.2f}% (threshold {(median_ctr*(1-x))*100:.2f}%)."
            )

    if np.isfinite(median_cpc) and np.isfinite(last_cpc):
        if last_cpc > median_cpc * (1 + x):
            hints.append(
                f"CPC is high: ${last_cpc:.2f} vs 7-day median ${median_cpc:.2f} (threshold ${(median_cpc*(1+x)):.2f})."
            )

    if len(daily) >= 4:
        recent2 = daily.tail(2)
        prev2 = daily.tail(4).head(2)
        recent_spend = float(np.nanmean(recent2["spend"].astype(float)))
        prev_spend = float(np.nanmean(prev2["spend"].astype(float)))
        recent_clicks = float(np.nanmean(recent2["link_clicks"].astype(float)))
        prev_clicks = float(np.nanmean(prev2["link_clicks"].astype(float)))
        if np.isfinite(recent_spend) and np.isfinite(prev_spend) and prev_spend > 0:
            if recent_spend > prev_spend * 1.10 and np.isfinite(recent_clicks) and np.isfinite(prev_clicks) and prev_clicks > 0:
                if recent_clicks < prev_clicks * 0.90:
                    hints.append(
                        "Spend is up but clicks are down: last 2 days vs previous 2 days (averages)."
                    )

    return hints


def render_weekly_report_html(
    *,
    clean_df: pd.DataFrame,
    summary_df: pd.DataFrame,
    daily_df: pd.DataFrame | None,
    level: str,
    date_range: str,
    charts: dict[str, str],
    notes: list[str],
) -> str:
    totals = {
        "spend": float(clean_df["spend"].astype(float).sum()) if "spend" in clean_df.columns else 0.0,
        "impressions": float(clean_df["impressions"].astype(float).sum()) if "impressions" in clean_df.columns else 0.0,
        "link_clicks": float(clean_df["link_clicks"].astype(float).sum()) if "link_clicks" in clean_df.columns else 0.0,
    }
    ctr = totals["link_clicks"] / totals["impressions"] if totals["impressions"] > 0 else 0.0
    cpc = totals["spend"] / totals["link_clicks"] if totals["link_clicks"] > 0 else float("nan")
    cpm = totals["spend"] / totals["impressions"] * 1000.0 if totals["impressions"] > 0 else float("nan")

    cards = [
        {"label": "Spend", "value": _format_money(totals["spend"]), "note": ""},
        {"label": "Impressions", "value": _format_int(totals["impressions"]), "note": ""},
        {"label": "Link Clicks", "value": _format_int(totals["link_clicks"]), "note": ""},
        {"label": "CTR", "value": _format_pct(ctr), "note": ""},
        {"label": "CPC", "value": _format_money(cpc), "note": ""},
        {"label": "CPM", "value": _format_money(cpm), "note": ""},
    ]

    if "website_purchase_roas" in clean_df.columns and clean_df["website_purchase_roas"].notna().any():
        weights = clean_df["spend"].astype(float)
        roas_series = pd.to_numeric(clean_df["website_purchase_roas"], errors="coerce")
        mask = (weights > 0) & roas_series.notna()
        denom = float(weights[mask].sum())
        roas_value = float((roas_series[mask] * weights[mask]).sum()) / denom if denom > 0 else float("nan")
        cards.append(
            {
                "label": "Website Purchase ROAS",
                "value": _format_float(roas_value, digits=2),
                "note": "Meta metric (provided by export).",
            }
        )
    elif "purchase_value" in clean_df.columns and clean_df["purchase_value"].notna().any():
        purchase_total = float(clean_df["purchase_value"].astype(float).sum())
        roas_value = purchase_total / totals["spend"] if totals["spend"] > 0 else float("nan")
        cards.append({"label": "Observed ROAS", "value": _format_float(roas_value, digits=2), "note": "Derived: purchase_value / spend."})

    top_rows: list[dict[str, Any]] = []
    if level != "account" and level in summary_df.columns:
        top = summary_df.head(10)
        for _, row in top.iterrows():
            top_rows.append(
                {
                    "level": str(row[level]),
                    "spend": _format_money(float(row["spend"])),
                    "impressions": _format_int(float(row["impressions"])),
                    "link_clicks": _format_int(float(row["link_clicks"])),
                    "ctr": _format_pct(float(row["ctr"])),
                    "cpc": _format_money(float(row["cpc"])) if pd.notna(row["cpc"]) else "—",
                    "cpm": _format_money(float(row["cpm"])) if pd.notna(row["cpm"]) else "—",
                }
            )

    ctx = ReportContext(
        title="Weekly Performance Report (Meta Ads CSV)",
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        level=level,
        date_range=date_range,
        kpis={"cards": cards},
        charts=charts,
        top_rows=top_rows,
        anomalies=_build_anomalies(daily_df),
        notes=notes,
    )
    return _HTML_TEMPLATE.render(ctx=ctx)
