from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

import pandas as pd

from . import AdsWkError, __version__
from .aggregate import aggregate_summary, daily_totals
from .charts import ctr_cpc_trend, spend_clicks_trend
from .export_xlsx import export_clean_xlsx
from .io import read_csv_flexible
from .kpi import add_kpi_columns
from .mapping import load_effective_template, resolve_mapping
from .normalize import normalize_dataframe
from .report_html import render_weekly_report_html


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="adswk", description="Meta Ads CSV → Weekly report (HTML + Excel)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    report = sub.add_parser("report", help="Generate weekly_report.html and clean.xlsx")
    report.add_argument("--input", required=True, type=Path, help="Path to Meta Ads CSV export")
    report.add_argument("--output", required=True, type=Path, help="Output directory")
    report.add_argument("--template", default="meta_ads", help="Template name (default: meta_ads) or path to .yaml")
    report.add_argument(
        "--level",
        default="campaign",
        choices=["campaign", "adset", "ad", "account"],
        help="Aggregation level (default: campaign)",
    )
    report.add_argument(
        "--start",
        default=None,
        help="Start date (YYYY-MM-DD), optional. If omitted (and date exists), defaults to last 7 days.",
    )
    report.add_argument(
        "--end",
        default=None,
        help="End date (YYYY-MM-DD), optional. If omitted (and date exists), defaults to last 7 days.",
    )
    report.add_argument("--mapping", default=None, type=Path, help="Optional custom mapping YAML (overrides template)")
    report.add_argument("--verbose", action="store_true", help="Print mapping hits and warnings")
    return parser


def _select_clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    ordered = [
        "date",
        "date_raw",
        "campaign",
        "adset",
        "ad",
        "spend",
        "impressions",
        "link_clicks",
        "purchase_value",
        "purchases",
        "website_purchase_roas",
        "ctr",
        "cpc",
        "cpm",
        "observed_roas",
    ]
    cols = [c for c in ordered if c in df.columns]
    return df[cols].copy()


def _apply_date_window(
    df: pd.DataFrame, start: str | None, end: str | None
) -> tuple[pd.DataFrame, str | None, str | None, list[str]]:
    notes: list[str] = []
    if "date" not in df.columns:
        if start or end:
            notes.append("Start/end ignored because date column is missing or not parseable.")
        return df, None, None, notes

    date_series = pd.to_datetime(df["date"], errors="coerce")
    if date_series.notna().sum() == 0:
        if start or end:
            notes.append("Start/end ignored because date column is missing or not parseable.")
        return df, None, None, notes

    work = df.copy()
    work["date"] = date_series

    used_start = start
    used_end = end

    if used_start is None and used_end is None:
        max_dt = pd.to_datetime(work["date"].max())
        end_ts = pd.Timestamp(max_dt).normalize()
        start_ts = end_ts - pd.Timedelta(days=6)
        used_start = start_ts.date().isoformat()
        used_end = end_ts.date().isoformat()
        notes.append(f"Default date window: last 7 days ({used_start} to {used_end}).")

    try:
        start_ts = pd.to_datetime(used_start).normalize() if used_start else None
    except Exception as e:
        raise AdsWkError(f"Invalid --start '{used_start}'. Expected YYYY-MM-DD.") from e
    try:
        end_ts = pd.to_datetime(used_end).normalize() if used_end else None
    except Exception as e:
        raise AdsWkError(f"Invalid --end '{used_end}'. Expected YYYY-MM-DD.") from e

    if start_ts is not None and end_ts is not None and end_ts < start_ts:
        raise AdsWkError("--end must be >= --start.")

    if start_ts is not None:
        work = work[work["date"] >= start_ts]
    if end_ts is not None:
        work = work[work["date"] < (end_ts + pd.Timedelta(days=1))]

    return work, used_start, used_end, notes


def run_report(args: argparse.Namespace) -> int:
    output_dir: Path = args.output
    output_dir.mkdir(parents=True, exist_ok=True)

    df_raw, io_profile = read_csv_flexible(args.input, verbose=args.verbose)
    template = load_effective_template(args.template, args.mapping)
    mapping, map_profile = resolve_mapping(df_raw.columns.tolist(), template)

    df_norm, norm_profile = normalize_dataframe(df_raw, template, mapping)
    df_kpi = add_kpi_columns(df_norm)

    df_window, used_start, used_end, date_notes = _apply_date_window(df_kpi, args.start, args.end)

    summary_df, agg_profile = aggregate_summary(df_window, level=args.level, start=None, end=None)
    daily_df = daily_totals(df_window)

    charts: dict[str, str] = {"spend_clicks": "", "ctr_cpc": ""}
    notes: list[str] = []

    if norm_profile.warnings:
        notes.extend(norm_profile.warnings)
    if date_notes:
        notes.extend(date_notes)
    if agg_profile.warnings:
        notes.extend(agg_profile.warnings)

    if daily_df is not None and len(daily_df) >= 2:
        charts["spend_clicks"] = spend_clicks_trend(daily_df)
        charts["ctr_cpc"] = ctr_cpc_trend(daily_df)
    else:
        notes.append("Not enough valid dates for trends; trend disabled.")

    date_range = "N/A"
    if daily_df is not None and len(daily_df) > 0:
        date_range = f"{daily_df['date'].min()} → {daily_df['date'].max()}"

    html = render_weekly_report_html(
        clean_df=df_window,
        summary_df=summary_df,
        daily_df=daily_df,
        level=agg_profile.effective_level,
        date_range=date_range,
        charts=charts,
        notes=notes,
    )

    html_path = output_dir / "weekly_report.html"
    html_path.write_text(html, encoding="utf-8")

    xlsx_path = output_dir / "clean.xlsx"
    export_clean_xlsx(clean_df=_select_clean_columns(df_window), summary_df=summary_df, output_path=xlsx_path)

    if args.verbose:
        sys.stderr.write(f"[io] encoding={io_profile.encoding} delimiter={io_profile.delimiter} rows={io_profile.row_count}\n")
        sys.stderr.write("[mapping] hits:\n")
        for std, src in sorted(map_profile.hits.items()):
            sys.stderr.write(f"  - {std} <- {src}\n")
        if map_profile.missing_optional:
            sys.stderr.write(f"[mapping] missing optional: {', '.join(map_profile.missing_optional)}\n")
        for w in notes:
            sys.stderr.write(f"[note] {w}\n")

    sys.stdout.write(f"Wrote: {html_path}\n")
    sys.stdout.write(f"Wrote: {xlsx_path}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "report":
            return run_report(args)
        raise AdsWkError(f"Unknown command: {args.command}")
    except AdsWkError as e:
        sys.stderr.write(str(e).rstrip() + "\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Unexpected error: {e}\n")
        if getattr(args, "verbose", False):
            traceback.print_exc()
        else:
            sys.stderr.write("Re-run with --verbose to see a full traceback.\n")
        return 2
