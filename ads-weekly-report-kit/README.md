# ads-weekly-report-kit

Turn a Meta Ads reporting CSV into a polished weekly report in minutes.

`ads-weekly-report-kit` is a small Python CLI that produces:

- `weekly_report.html`: a shareable single-file report with KPI cards, trends, top rows, and anomaly hints
- `clean.xlsx`: a cleaned workbook with detail data and a summary sheet for follow-up analysis

The scope is intentionally tight for `v0.1`: Meta CSV in, HTML and Excel out. No API pull, no GUI, and no multi-platform abstraction layer.

## What It Does

- Reads Meta Ads CSV exports with flexible encoding and delimiter handling
- Maps source columns into a standard schema with YAML templates
- Normalizes money, integers, floats, and dates
- Computes KPI fields such as CTR, CPC, CPM, and optional ROAS
- Aggregates by `campaign`, `adset`, `ad`, or `account`
- Renders a weekly HTML report
- Exports clean analysis-ready Excel output

## Requirements

- Python `3.10+`
- A Meta Ads reporting CSV that includes at least `Amount spent` or an equivalent spend column, `Impressions`, and `Link clicks`

## Install

From the project folder:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

After installation, the `adswk` command becomes available.

## Quick Start

```bash
adswk report --input examples/meta_sample.csv --output outputs/ --template meta_ads --level campaign
```

Generated files:

- `outputs/weekly_report.html`
- `outputs/clean.xlsx`

If a usable `date` column exists and `--start/--end` is omitted, the tool automatically uses the latest 7 days.

## Command Reference

```bash
adswk report ^
  --input examples/meta_sample.csv ^
  --output outputs/ ^
  --template meta_ads ^
  --level campaign
```

Available levels:

- `campaign`
- `adset`
- `ad`
- `account`

Optional date arguments:

- `--start YYYY-MM-DD`
- `--end YYYY-MM-DD`

Optional mapping override:

- `--mapping path/to/custom.yaml`

## Mapping Templates

The CLI resolves source columns through YAML templates.

- Built-in template: `templates/meta_ads.yaml`
- Override file: `--mapping path/to/custom.yaml`

Example override:

```yaml
fields:
  spend:
    column: "Amount spent (USD)"
  link_clicks:
    column: "Link clicks"
```

If the required fields `spend`, `impressions`, or `link_clicks` cannot be mapped, the CLI stops with a friendly error.

## KPI Definitions

- `CTR` = `link_clicks / impressions` and returns `0` when impressions are `0`
- `CPC` = `spend / link_clicks` and returns `NaN` when link clicks are `0`
- `CPM` = `spend / impressions * 1000` and returns `NaN` when impressions are `0`
- `ROAS` is optional. If `website_purchase_roas` exists, it is displayed as `Website Purchase ROAS`. Otherwise, if `purchase_value` exists, `Observed ROAS` is derived as `purchase_value / spend`

## Project Structure

```text
ads-weekly-report-kit/
|-- examples/
|-- handbook/
|-- outputs/
|-- src/adswk/
|-- templates/
|-- tests/
|-- CHANGELOG.md
|-- QUICKSTART.md
|-- README.md
|-- pyproject.toml
`-- requirements.txt
```

## Testing

Run the smoke tests from the project folder:

```bash
python -m unittest tests.test_smoke
```

## Documentation

- [QUICKSTART.md](QUICKSTART.md)
- [handbook/META_EXPORT_GUIDE.md](handbook/META_EXPORT_GUIDE.md)
- [handbook/FAQ.md](handbook/FAQ.md)

## Version

Current packaged release: `v0.1.0`
