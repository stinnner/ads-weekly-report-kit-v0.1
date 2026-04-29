# Meta Export Guide (CSV)

This tool expects a CSV export from **Meta Ads Reporting / Ads Manager reporting**.

## Where to export

Common paths in Meta UI (names can vary by account locale):

- **Ads Manager → Reports**
- Or in a reporting table view: **Export table data**

Choose **CSV** (preferred). XLSX exports are out of scope for v0.1.

## Required columns (must include)

The export must contain columns equivalent to:

- **Amount spent**
- **Impressions**
- **Link clicks**

These are required to compute Meta-aligned CTR/CPC/CPM.

## Recommended columns (optional)

If you include these, the report becomes more useful:

- Day / Date (for trends)
- Campaign name / Ad set name / Ad name (for Top tables)
- Purchase conversion value / Website purchases conversion value (for derived ROAS)
- Website purchase ROAS (Meta metric, if available in your export preset)

## Tip: export one row per day

For best weekly trend charts, export with a daily breakdown (one row per day per campaign/adset/ad).

