from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import AdsWkError


def export_clean_xlsx(*, clean_df: pd.DataFrame, summary_df: pd.DataFrame, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            clean_df.to_excel(writer, sheet_name="clean_data", index=False)
            summary_df.head(50).to_excel(writer, sheet_name="summary", index=False)
    except Exception as e:
        raise AdsWkError(f"Failed to write Excel output: {e}") from e

