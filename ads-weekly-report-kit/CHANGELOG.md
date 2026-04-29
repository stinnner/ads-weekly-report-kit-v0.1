# Changelog

## v0.1.0

- Read Meta Ads CSV (UTF-8 / UTF-8-SIG; delimiter tolerant for `,` and `;`)
- YAML template-based field mapping with optional override mapping file
- Data normalization for money / ints / floats / dates
- KPI computation (CTR, CPC, CPM, optional ROAS)
- Aggregation by campaign/adset/ad/account
- Single-file HTML weekly report (KPI cards, trends, top table, anomaly hints)
- Excel export (`clean_data`, `summary`)
- Smoke tests for outputs + missing required fields

