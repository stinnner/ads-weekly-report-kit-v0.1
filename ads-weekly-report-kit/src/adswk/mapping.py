from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from . import AdsWkError
from .io import canonicalize_column_name


BUILTIN_META_ADS_TEMPLATE_YAML = """\
name: meta_ads
required:
  - spend
  - impressions
  - link_clicks
fields:
  date:
    aliases: ["day", "date", "reporting_start", "reporting_start_date", "reporting start", "reporting start date"]
    type: "date"
  campaign:
    aliases: ["campaign name", "campaign", "campaign_name"]
    type: "str"
  adset:
    aliases: ["ad set name", "adset", "adset_name", "ad set"]
    type: "str"
  ad:
    aliases: ["ad name", "ad", "ad_name"]
    type: "str"
  spend:
    aliases: ["amount spent", "amount spent (usd)", "amount_spent", "amount_spent_usd", "spend", "cost"]
    type: "money"
  impressions:
    aliases: ["impressions"]
    type: "int"
  link_clicks:
    aliases: ["link clicks", "clicks (link)", "clicks_link", "link_clicks"]
    type: "int"
  purchase_value:
    aliases: ["purchase conversion value", "website purchases conversion value", "purchase conversion value (usd)", "purchase_value"]
    type: "money"
  purchases:
    aliases: ["website purchases", "purchases"]
    type: "int"
  website_purchase_roas:
    aliases: ["website purchase roas", "website_purchase_roas"]
    type: "float"
"""


@dataclass(frozen=True)
class MappingProfile:
    template_name: str
    hits: dict[str, str]
    missing_required: list[str]
    missing_optional: list[str]


def _load_yaml_text(text: str) -> dict[str, Any]:
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise AdsWkError("Invalid template YAML: root must be a mapping/object.")
    return data


def _load_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AdsWkError(f"Mapping file not found: {path}")
    text = path.read_text(encoding="utf-8")
    return _load_yaml_text(text)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = dict(base)
    for key, value in override.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_template(template: str) -> dict[str, Any]:
    template_path = Path(template)
    if template_path.suffix.lower() in {".yaml", ".yml"} and template_path.exists():
        return _load_yaml_file(template_path)

    name = template.strip()
    candidates = [
        Path.cwd() / "templates" / f"{name}.yaml",
        Path(__file__).resolve().parents[2] / "templates" / f"{name}.yaml",
    ]
    for c in candidates:
        if c.exists():
            return _load_yaml_file(c)

    if name == "meta_ads":
        return _load_yaml_text(BUILTIN_META_ADS_TEMPLATE_YAML)

    raise AdsWkError(
        f"Template not found: {template}. Expected a name like 'meta_ads' or a path to a .yaml file."
    )


def load_effective_template(template: str, mapping_override: Path | None) -> dict[str, Any]:
    base = load_template(template)
    if mapping_override is None:
        return base
    override = _load_yaml_file(mapping_override)
    return _deep_merge(base, override)


def resolve_mapping(df_columns: list[str], template: dict[str, Any]) -> tuple[dict[str, str], MappingProfile]:
    fields = template.get("fields")
    if not isinstance(fields, dict):
        raise AdsWkError("Template YAML must contain a 'fields' mapping.")

    required = template.get("required", [])
    if not isinstance(required, list):
        raise AdsWkError("Template YAML 'required' must be a list.")

    hits: dict[str, str] = {}
    missing_optional: list[str] = []

    available = set(df_columns)
    for std_field, cfg_any in fields.items():
        cfg = cfg_any if isinstance(cfg_any, dict) else {}
        aliases = cfg.get("aliases", [])
        if aliases is None:
            aliases = []
        if not isinstance(aliases, list):
            raise AdsWkError(f"Template field '{std_field}' aliases must be a list.")

        candidates_raw: list[str] = []
        column_override = cfg.get("column")
        if isinstance(column_override, str) and column_override.strip():
            candidates_raw.append(column_override.strip())
        candidates_raw.extend([a for a in aliases if isinstance(a, str)])
        candidates_raw.append(std_field)

        candidates = [canonicalize_column_name(c) for c in candidates_raw]
        chosen: str | None = None
        for c in candidates:
            if c in available:
                chosen = c
                break

        if chosen is None:
            if std_field in required:
                continue
            missing_optional.append(std_field)
            continue
        hits[std_field] = chosen

    missing_required = [f for f in required if f not in hits]
    profile = MappingProfile(
        template_name=str(template.get("name", "")) or "unknown",
        hits=hits,
        missing_required=missing_required,
        missing_optional=missing_optional,
    )
    if missing_required:
        missing_str = ", ".join(missing_required)
        raise AdsWkError(
            "Missing required fields after mapping: "
            f"{missing_str}\n\n"
            "请在 Meta Ads Reporting 导出时包含：Amount spent / Impressions / Link clicks（或等价列）再导出 CSV。\n"
            "Tip: use --mapping to provide a custom column mapping if your export uses different names."
        )

    return hits, profile

