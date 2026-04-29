# FAQ

## Q: I got an error about missing required fields. What do I do?

Re-export from Meta Ads Reporting and make sure your export includes:

- Amount spent
- Impressions
- Link clicks

If your column names differ, provide a custom mapping file via `--mapping`.

## Q: My CSV uses `;` instead of `,`. Is that supported?

Yes. v0.1 auto-detects `,` and `;` for common Meta exports.

## Q: Why is ROAS missing in the report?

ROAS is optional:

- If your export contains `Website Purchase ROAS`, it will be shown.
- Otherwise, if `Purchase conversion value` exists, the tool shows **Observed ROAS (derived)** = `purchase_value/spend`.

If neither field exists, ROAS is omitted.

## Q: Trend charts are disabled (date parse failed). Why?

Your export likely contains an unexpected date format. The tool continues and still generates:

- KPI summary
- Top table
- Excel outputs

Fix: export with a standard Day/Date column (e.g., `YYYY-MM-DD`) or adjust `--mapping` to point to the right date column.

