# Quickstart (3 commands)

```bash
python -m venv .venv
pip install -r requirements.txt && pip install -e .
adswk report --input meta.csv --output outputs/ --template meta_ads
```

Outputs:

- `outputs/weekly_report.html` (single-file report you can share)
- `outputs/clean.xlsx` (`clean_data` + `summary` sheets)

Note: if your export has a date column and you omit `--start/--end`, the report defaults to the latest 7 days.
