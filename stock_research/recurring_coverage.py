from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from .repo import RepoState
from .validation import parse_date


TRACKED_STOCK_TABLES = ("current_holdings", "monitoring")
COVERAGE_CONFIG_PATH = Path("strategy/portfolio_industry_coverage.json")
RECURRING_STATE_PATH = Path("agents/recurring_research_state.json")
DEFAULT_FRESHNESS_WINDOW_DAYS = 14


def build_recurring_coverage(
    state: RepoState,
    current_date: date,
    *,
    freshness_window_days: int = DEFAULT_FRESHNESS_WINDOW_DAYS,
) -> dict[str, Any]:
    """Build deterministic recurring company/industry scope without mutating repo state."""

    config = load_coverage_config(state.root)
    configured_clusters = list(config["clusters"])
    company_items: list[dict[str, Any]] = []
    cluster_members: dict[str, list[dict[str, str]]] = {}
    cluster_definitions: dict[str, dict[str, Any]] = {
        str(cluster["id"]): dict(cluster) for cluster in configured_clusters
    }

    for bucket in TRACKED_STOCK_TABLES:
        table = state.stock_tables[bucket]
        for row in table.rows:
            ticker = str(row.get("ticker", "")).strip().upper()
            if not ticker:
                continue
            matched_clusters = matching_clusters(row, configured_clusters)
            if not matched_clusters:
                fallback = fallback_cluster(row)
                cluster_definitions.setdefault(str(fallback["id"]), fallback)
                matched_clusters = [fallback]

            cluster_ids = sorted({str(cluster["id"]) for cluster in matched_clusters})
            for cluster_id in cluster_ids:
                cluster_members.setdefault(cluster_id, []).append(
                    {
                        "ticker": ticker,
                        "bucket": bucket,
                        "company_name": str(row.get("company_name", "")).strip(),
                    }
                )

            company_items.append(
                {
                    "ticker": ticker,
                    "company_name": str(row.get("company_name", "")).strip(),
                    "membership_bucket": bucket,
                    "membership_source": table.path.relative_to(state.root).as_posix(),
                    "coverage_reason": company_coverage_reason(bucket, ticker),
                    "sector": str(row.get("sector", "")).strip(),
                    "industry": str(row.get("industry", "")).strip(),
                    "industry_cluster_ids": cluster_ids,
                    "impact_basis": "membership_only",
                    "freshness": company_freshness(row, current_date, freshness_window_days),
                }
            )

    industry_clusters = []
    for cluster_id in sorted(cluster_members):
        definition = cluster_definitions[cluster_id]
        members = sorted(cluster_members[cluster_id], key=lambda item: (item["ticker"], item["bucket"]))
        industry_clusters.append(
            {
                "cluster_id": cluster_id,
                "label": str(definition["label"]),
                "description": str(definition.get("description", "")),
                "themes": sorted({str(item).strip() for item in definition.get("themes", []) if str(item).strip()}),
                "member_tickers": [member["ticker"] for member in members],
                "membership_buckets": sorted({member["bucket"] for member in members}),
                "source_industries": sorted(
                    {
                        item["industry"]
                        for item in company_items
                        if cluster_id in item["industry_cluster_ids"] and item["industry"]
                    }
                ),
                "coverage_reason": (
                    f"Portfolio-industry coverage for {', '.join(member['ticker'] for member in members)}; "
                    "the cluster is researched once and shared across its members."
                ),
                "mapping_source": (
                    COVERAGE_CONFIG_PATH.as_posix()
                    if bool(definition.get("configured", True))
                    else "derived_from_stock_csv_industry"
                ),
                "exa_query": str(definition["exa_query"]),
                "grok_topic": str(definition["grok_topic"]),
            }
        )

    return {
        "schema_version": 1,
        "profile_id": "portfolio_update",
        "scope_policy": "current holdings plus monitoring; rejected stocks and Sheet ideas are excluded",
        "membership_sources": [
            state.stock_tables[bucket].path.relative_to(state.root).as_posix()
            for bucket in TRACKED_STOCK_TABLES
        ],
        "intake_only_sources": ["Google Sheet new_stock_overview"],
        "impact_basis": "membership_only",
        "weights_available": False,
        "impact_note": (
            "Coverage and attention are membership-based because portfolio weights are not stored. "
            "Do not infer exposure or concentration from row order, price, or market capitalization."
        ),
        "freshness_policy": {
            "window_days": freshness_window_days,
            "meaning": (
                "Freshness describes dates recorded in repo CSV metadata only. It does not prove that live provider "
                "research succeeded for this run."
            ),
        },
        "companies": sorted(company_items, key=lambda item: (item["membership_bucket"], item["ticker"])),
        "industry_clusters": industry_clusters,
        "comparison_baseline": build_comparison_baseline(state.root),
        "provider_roles": provider_roles(),
    }


def load_coverage_config(root: Path) -> dict[str, Any]:
    path = root / COVERAGE_CONFIG_PATH
    if not path.exists():
        return {"schema_version": 1, "clusters": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid portfolio industry coverage JSON: {path}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("clusters"), list):
        raise ValueError("Portfolio industry coverage config requires a top-level clusters list.")

    cluster_ids: set[str] = set()
    validated: list[dict[str, Any]] = []
    for raw_cluster in data["clusters"]:
        if not isinstance(raw_cluster, dict):
            raise ValueError("Each portfolio industry cluster must be an object.")
        cluster = dict(raw_cluster)
        cluster_id = str(cluster.get("id", "")).strip()
        label = str(cluster.get("label", "")).strip()
        exa_query = str(cluster.get("exa_query", "")).strip()
        grok_topic = str(cluster.get("grok_topic", "")).strip()
        if not cluster_id or not label or not exa_query or not grok_topic:
            raise ValueError("Each portfolio industry cluster requires id, label, exa_query, and grok_topic.")
        if cluster_id in cluster_ids:
            raise ValueError(f"Duplicate portfolio industry cluster id: {cluster_id}")
        cluster_ids.add(cluster_id)
        cluster["id"] = cluster_id
        cluster["label"] = label
        cluster["exa_query"] = exa_query
        cluster["grok_topic"] = grok_topic
        cluster["configured"] = True
        for field in ("ticker_tags", "industry_tags", "sector_tags", "themes"):
            values = cluster.get(field, [])
            if not isinstance(values, list):
                raise ValueError(f"Portfolio industry cluster {cluster_id} field {field} must be a list.")
            cluster[field] = [str(value).strip() for value in values if str(value).strip()]
        validated.append(cluster)
    return {"schema_version": int(data.get("schema_version", 1)), "clusters": validated}


def matching_clusters(row: dict[str, str], clusters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ticker = str(row.get("ticker", "")).strip().casefold()
    industry = str(row.get("industry", "")).strip().casefold()
    sector = str(row.get("sector", "")).strip().casefold()
    matches = []
    for cluster in clusters:
        ticker_tags = {str(value).casefold() for value in cluster.get("ticker_tags", [])}
        industry_tags = {str(value).casefold() for value in cluster.get("industry_tags", [])}
        sector_tags = {str(value).casefold() for value in cluster.get("sector_tags", [])}
        if ticker in ticker_tags or (industry and industry in industry_tags) or (sector and sector in sector_tags):
            matches.append(cluster)
    return matches


def fallback_cluster(row: dict[str, str]) -> dict[str, Any]:
    label = str(row.get("industry", "")).strip() or str(row.get("sector", "")).strip() or "Unclassified industry"
    cluster_id = f"industry_{slugify(label)}"
    return {
        "id": cluster_id,
        "label": label,
        "description": "Fallback cluster derived directly from the tracked-stock CSV industry or sector field.",
        "themes": [],
        "exa_query": f"{label} latest material developments public companies regulation demand supply chain",
        "grok_topic": f"{label} investor expert and community discussion",
        "configured": False,
    }


def company_freshness(row: dict[str, str], current_date: date, window_days: int) -> dict[str, Any]:
    return {
        "metadata": dated_freshness(row.get("date_last_updated", ""), current_date, window_days),
        "filings": dated_freshness(row.get("last_filing_checked", ""), current_date, window_days),
        "news": dated_freshness(row.get("last_news_checked", ""), current_date, window_days),
        "sentiment": dated_freshness(row.get("last_sentiment_checked", ""), current_date, window_days),
    }


def dated_freshness(value: str | None, current_date: date, window_days: int) -> dict[str, Any]:
    raw_value = str(value or "").strip()
    parsed = parse_date(raw_value)
    if not raw_value:
        return {"as_of": "", "age_days": None, "status": "unknown"}
    if parsed is None:
        return {"as_of": raw_value, "age_days": None, "status": "invalid_date"}
    age_days = (current_date - parsed).days
    if age_days < 0:
        status = "future_date"
    elif age_days <= window_days:
        status = "within_recurring_window"
    else:
        status = "stale"
    return {"as_of": parsed.isoformat(), "age_days": age_days, "status": status}


def build_comparison_baseline(root: Path) -> dict[str, Any]:
    state_path = root / RECURRING_STATE_PATH
    recorded: dict[str, Any] = {}
    if state_path.exists():
        try:
            raw_data = json.loads(state_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid recurring research state JSON: {state_path}") from exc
        if not isinstance(raw_data, dict):
            raise ValueError("Recurring research state must be a JSON object.")
        profile_state = raw_data.get("portfolio_update", {})
        if isinstance(profile_state, dict):
            recorded = profile_state

    accepted_run_id = str(recorded.get("accepted_run_id", "")).strip()
    latest_generated_run_id = latest_generated_weekly_run_id(root)
    accepted_artifact = recurring_run_artifact(root, accepted_run_id) if accepted_run_id else None
    if not accepted_run_id:
        status = "not_recorded"
        note = "No portfolio-update run has been explicitly accepted; do not use the latest generated run as a substitute."
    elif accepted_artifact is None:
        status = "recorded_artifact_missing"
        note = "An accepted run id is recorded, but its active or archived artifact directory was not found."
    else:
        status = "accepted"
        note = "Use only this explicitly accepted run as the comparison baseline."

    return {
        "policy": "explicit_acceptance_only",
        "state_path": RECURRING_STATE_PATH.as_posix(),
        "status": status,
        "accepted_run_id": accepted_run_id,
        "accepted_at": str(recorded.get("accepted_at", "")).strip(),
        "accepted_by": str(recorded.get("accepted_by", "")).strip(),
        "accepted_artifact_path": accepted_artifact,
        "latest_generated_run_id": latest_generated_run_id,
        "latest_generated_is_accepted": bool(accepted_run_id and accepted_run_id == latest_generated_run_id),
        "comparison_run_id": accepted_run_id if status == "accepted" else "",
        "note": note,
    }


def latest_generated_weekly_run_id(root: Path) -> str:
    runs_dir = root / "agents" / "runs"
    if not runs_dir.exists():
        return ""
    candidates = sorted(
        path.name
        for path in runs_dir.iterdir()
        if path.is_dir() and path.name.endswith("_weekly") and parse_date(path.name[:10]) is not None
    )
    return candidates[-1] if candidates else ""


def recurring_run_artifact(root: Path, run_id: str) -> str | None:
    active_path = root / "agents" / "runs" / run_id
    if active_path.exists():
        return active_path.relative_to(root).as_posix()
    archived_path = root / "archive" / "runs" / run_id
    if archived_path.exists():
        return archived_path.relative_to(root).as_posix()
    return None


def provider_roles() -> dict[str, dict[str, str]]:
    return {
        "company_financials": {
            "providers": "yfinance, FMP, Polygon/Massive, Alpha Vantage",
            "role": "normalized market-data snapshots and cross-checks",
        },
        "official_filings": {
            "providers": "SEC EDGAR and company investor relations",
            "role": "verified official company facts and filings",
        },
        "exa_web_research": {
            "providers": "Exa",
            "role": "current web/news discovery, primary-source finding, and selected contents retrieval",
        },
        "grok_x_research": {
            "providers": "xAI Grok 4.6 x_search",
            "role": "X-native expert/community narratives, disagreements, rumors, and emerging signals",
        },
        "grok_web_gap_fill": {
            "providers": "xAI Grok web_search",
            "role": "deferred auxiliary gap filling only; material facts require independent verification",
        },
    }


def company_coverage_reason(bucket: str, ticker: str) -> str:
    if bucket == "current_holdings":
        return f"{ticker} is an explicit current holding in the repo portfolio CSV."
    return f"{ticker} is an explicit monitored stock in the repo monitoring CSV."


def slugify(value: str) -> str:
    slug = "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "unknown"
