from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import (
    Claim,
    Contradiction,
    EvidencePacket,
    RecommendedUpdate,
    Source,
    default_packet_path,
    new_packet,
    read_packet,
    write_packet,
)


FINANCIAL_PROVIDERS = {"yfinance", "fmp", "polygon", "alpha_vantage", "sec_edgar"}
NUMERIC_METRICS = {
    "latest_price": 0.01,
    "market_cap": 0.03,
    "pe_ratio": 0.05,
    "price_to_sales_ttm": 0.05,
    "ev_to_ebitda_ttm": 0.05,
    "free_cash_flow_per_share_ttm": 0.05,
    "debt_to_equity_ttm": 0.05,
    "revenue_ttm": 0.05,
    "eps": 0.05,
    "profit_margin": 0.05,
    "price_to_book_ratio": 0.05,
    "previous_volume": 0.10,
    "previous_vwap": 0.02,
}
PREFERRED_PROVIDERS = {
    "latest_price": ["polygon", "fmp", "alpha_vantage", "yfinance"],
    "market_cap": ["fmp", "polygon", "alpha_vantage", "yfinance"],
    "pe_ratio": ["fmp", "alpha_vantage", "yfinance"],
    "company_name": ["fmp", "polygon", "alpha_vantage", "yfinance"],
    "exchange": ["fmp", "alpha_vantage", "polygon", "yfinance"],
    "currency": ["fmp", "alpha_vantage", "polygon", "yfinance"],
    "sector": ["fmp", "alpha_vantage", "yfinance"],
    "industry": ["fmp", "alpha_vantage", "yfinance"],
    "country": ["fmp", "alpha_vantage", "polygon"],
}
PROVIDER_METRIC_MAP = {
    "yfinance": {
        "company_name": "company_name",
        "currency": "currency",
        "latest_price": "last_price",
        "market_cap": "market_cap",
        "pe_ratio": "pe_ratio",
        "exchange": "exchange",
        "sector": "sector",
        "industry": "industry",
        "fifty_two_week_low": "fifty_two_week_low",
        "fifty_two_week_high": "fifty_two_week_high",
    },
    "fmp": {
        "company_name": "company_name",
        "country": "country",
        "currency": "currency",
        "exchange": "exchange",
        "latest_price": "price",
        "market_cap": "market_cap",
        "pe_ratio": "pe_ratio_ttm",
        "price_to_sales_ttm": "price_to_sales_ttm",
        "ev_to_ebitda_ttm": "ev_to_ebitda_ttm",
        "free_cash_flow_per_share_ttm": "free_cash_flow_per_share_ttm",
        "debt_to_equity_ttm": "debt_to_equity_ttm",
        "sector": "sector",
        "industry": "industry",
    },
    "polygon": {
        "company_name": "company_name",
        "currency": "currency",
        "exchange": "primary_exchange",
        "latest_price": "previous_close",
        "market_cap": "market_cap",
        "previous_open": "previous_open",
        "previous_high": "previous_high",
        "previous_low": "previous_low",
        "previous_volume": "previous_volume",
        "previous_vwap": "previous_vwap",
    },
    "alpha_vantage": {
        "company_name": "company_name",
        "country": "country",
        "currency": "currency",
        "exchange": "exchange",
        "latest_price": "latest_price",
        "market_cap": "market_cap",
        "pe_ratio": "pe_ratio",
        "peg_ratio": "peg_ratio",
        "price_to_book_ratio": "price_to_book_ratio",
        "profit_margin": "profit_margin",
        "revenue_ttm": "revenue_ttm",
        "eps": "eps",
        "sector": "sector",
        "industry": "industry",
    },
}


class FinancialCompareError(RuntimeError):
    pass


@dataclass(frozen=True)
class FinancialObservation:
    metric: str
    provider: str
    value: Any
    source_id: str


def build_financial_compare_packet(
    ticker: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    packet_paths: list[Path] | None = None,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    ticker_upper = ticker.upper()
    loaded = load_financial_packets(root, run_id, ticker_upper, packet_paths)
    if not loaded:
        raise FinancialCompareError(f"No financial evidence packets found for {ticker_upper} in run {run_id}.")

    selected = select_latest_packet_per_provider(loaded)
    observations = collect_observations(selected)
    observed_providers = {observation.provider for observation in observations}
    sources = build_sources([(path, packet) for path, packet in selected if packet.provider in observed_providers], today)
    comparison = compare_observations(observations)
    raw_path = write_raw_artifact(root, run_id, ticker_upper, comparison)
    packet = comparison_to_packet(ticker_upper, comparison, sources, raw_path, today)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def load_financial_packets(
    root: Path,
    run_id: str,
    ticker: str,
    packet_paths: list[Path] | None = None,
) -> list[tuple[Path, EvidencePacket]]:
    paths = packet_paths or sorted((root / "agents" / "runs" / run_id / "evidence_packets").glob("*.json"))
    loaded: list[tuple[Path, EvidencePacket]] = []
    for path in paths:
        packet = read_packet(path)
        if packet.provider not in FINANCIAL_PROVIDERS:
            continue
        if packet.subject_type != "company" or packet.subject_id.upper() != ticker.upper():
            continue
        loaded.append((path, packet))
    return loaded


def select_latest_packet_per_provider(loaded: list[tuple[Path, EvidencePacket]]) -> list[tuple[Path, EvidencePacket]]:
    latest: dict[str, tuple[Path, EvidencePacket]] = {}
    for path, packet in loaded:
        current = latest.get(packet.provider)
        if current is None or packet.created_at >= current[1].created_at:
            latest[packet.provider] = (path, packet)
    return [latest[provider] for provider in sorted(latest)]


def build_sources(selected: list[tuple[Path, EvidencePacket]], today: date) -> list[Source]:
    sources: list[Source] = []
    for path, packet in selected:
        source_id = source_id_for_provider(packet.provider)
        sources.append(
            Source(
                source_id=source_id,
                provider="financial_compare",
                source_type="internal",
                title=f"{packet.provider} evidence packet for {packet.subject_id}",
                publisher=packet.provider,
                accessed_at=today.isoformat(),
                artifact_path=path.as_posix(),
                notes=f"Input evidence packet {packet.packet_id}.",
            )
        )
    return sources


def collect_observations(selected: list[tuple[Path, EvidencePacket]]) -> list[FinancialObservation]:
    observations: list[FinancialObservation] = []
    for _path, packet in selected:
        metrics = extract_packet_metrics(packet)
        mapping = PROVIDER_METRIC_MAP.get(packet.provider, {})
        source_id = source_id_for_provider(packet.provider)
        for canonical_metric, provider_metric in mapping.items():
            value = metrics.get(provider_metric, "")
            if value in {"", None}:
                continue
            observations.append(FinancialObservation(canonical_metric, packet.provider, value, source_id))
    return observations


def extract_packet_metrics(packet: EvidencePacket) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    for claim in packet.claims:
        try:
            parsed = json.loads(claim.evidence)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            metrics.update(parsed)
    return metrics


def compare_observations(observations: list[FinancialObservation]) -> dict[str, Any]:
    grouped: dict[str, list[FinancialObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.metric, []).append(observation)

    consensus: dict[str, Any] = {}
    conflicts: list[dict[str, Any]] = []
    unknowns: list[str] = []
    all_metrics = sorted({metric for provider_map in PROVIDER_METRIC_MAP.values() for metric in provider_map})

    for metric in all_metrics:
        values = grouped.get(metric, [])
        if not values:
            unknowns.append(f"No provider value found for {metric}.")
            continue
        if metric in NUMERIC_METRICS:
            result = compare_numeric_metric(metric, values)
        else:
            result = compare_text_metric(metric, values)
        consensus[metric] = result
        if result["status"] == "conflict":
            conflicts.append({"metric": metric, "values": result["values"], "reason": result["reason"]})

    return {
        "consensus": consensus,
        "conflicts": conflicts,
        "unknowns": unknowns,
        "provider_count": len({observation.provider for observation in observations}),
    }


def compare_numeric_metric(metric: str, values: list[FinancialObservation]) -> dict[str, Any]:
    numeric_values = [(observation, to_float(observation.value)) for observation in values]
    numeric_values = [(observation, value) for observation, value in numeric_values if value is not None]
    raw_values = provider_values(values)
    if not numeric_values:
        return {
            "value": preferred_observation(metric, values).value,
            "confidence": "low",
            "status": "non_numeric",
            "providers": sorted({value.provider for value in values}),
            "values": raw_values,
            "reason": "Provider values were not parseable as numbers.",
        }
    preferred = preferred_observation(metric, [observation for observation, _value in numeric_values])
    preferred_value = to_float(preferred.value)
    minimum = min(value for _observation, value in numeric_values)
    maximum = max(value for _observation, value in numeric_values)
    relative_spread = relative_difference(minimum, maximum)
    tolerance = NUMERIC_METRICS[metric]
    status = "consistent" if relative_spread <= tolerance else "conflict"
    confidence = "high" if status == "consistent" and len(numeric_values) >= 2 else "medium"
    if status == "conflict":
        confidence = "low"
    return {
        "value": preferred_value,
        "confidence": confidence,
        "status": status,
        "providers": sorted({observation.provider for observation, _value in numeric_values}),
        "values": raw_values,
        "range": {"min": minimum, "max": maximum, "relative_spread": relative_spread},
        "reason": "Values are within tolerance." if status == "consistent" else f"Relative spread exceeds {tolerance:.0%} tolerance.",
    }


def compare_text_metric(metric: str, values: list[FinancialObservation]) -> dict[str, Any]:
    normalized: dict[str, list[FinancialObservation]] = {}
    for observation in values:
        normalized.setdefault(normalize_text_metric(metric, observation.value), []).append(observation)
    largest_group = max(normalized.values(), key=len)
    preferred = preferred_observation(metric, largest_group)
    status = "consistent" if len(normalized) == 1 else "conflict"
    confidence = "high" if status == "consistent" and len(largest_group) >= 2 else "medium"
    if status == "conflict" and len(largest_group) == 1:
        confidence = "low"
    return {
        "value": preferred.value,
        "confidence": confidence,
        "status": status,
        "providers": sorted({observation.provider for observation in values}),
        "values": provider_values(values),
        "reason": "Text values normalize consistently." if status == "consistent" else "Providers disagree after normalization.",
    }


def provider_values(values: list[FinancialObservation]) -> dict[str, Any]:
    return {observation.provider: observation.value for observation in values}


def preferred_observation(metric: str, values: list[FinancialObservation]) -> FinancialObservation:
    order = PREFERRED_PROVIDERS.get(metric, ["fmp", "polygon", "alpha_vantage", "yfinance", "sec_edgar"])
    for provider in order:
        for observation in values:
            if observation.provider == provider:
                return observation
    return values[0]


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def relative_difference(minimum: float, maximum: float) -> float:
    denominator = max(abs(minimum), abs(maximum), 1.0)
    return abs(maximum - minimum) / denominator


def normalize_text_metric(metric: str, value: Any) -> str:
    text = str(value).strip().lower()
    if metric == "company_name":
        for suffix in (".", ","):
            text = text.replace(suffix, "")
        return " ".join(text.split())
    if metric == "country" and text in {"us", "usa", "united states", "united states of america"}:
        return "united states"
    if metric == "exchange" and text in {"xnas", "nasdaq", "nms", "ngm"}:
        return "nasdaq"
    if metric == "currency":
        return text.upper()
    return " ".join(text.split())


def comparison_to_packet(
    ticker: str,
    comparison: dict[str, Any],
    sources: list[Source],
    raw_path: Path,
    today: date,
) -> EvidencePacket:
    source_ids = [source.source_id for source in sources]
    consensus_summary = {
        metric: {
            "value": result["value"],
            "confidence": result["confidence"],
            "status": result["status"],
            "providers": result["providers"],
        }
        for metric, result in comparison["consensus"].items()
        if result["status"] != "non_numeric"
    }
    conflicts = comparison["conflicts"]
    claims = [
        Claim(
            claim=f"Financial data comparison completed for {ticker}.",
            evidence=json.dumps(consensus_summary, sort_keys=True),
            source_ids=source_ids,
            confidence="high" if not conflicts else "medium",
            impact="medium",
            novelty="new",
        )
    ]
    contradictions = [
        Contradiction(
            current_repo_claim=f"Provider values for {conflict['metric']} are consistent.",
            new_evidence=json.dumps(conflict["values"], sort_keys=True),
            source_ids=source_ids_for_conflict(conflict, sources),
            suggested_action="Preserve the provider disagreement and avoid updating this metric without review.",
        )
        for conflict in conflicts
    ]
    recommended_updates = [
        RecommendedUpdate(
            target_file="stock_tracking/stock_info_files/",
            update_type="company_file",
            summary=f"Update {ticker} financial snapshot with consensus metrics from financial_compare packet.",
            needs_human_review=bool(conflicts),
            source_ids=source_ids,
        )
    ]
    return new_packet(
        provider="financial_compare",
        subject_type="company",
        subject_id=ticker,
        time_window="latest_financial_packets",
        current_date=today,
        sources=sources,
        claims=claims,
        contradictions=contradictions,
        recommended_updates=recommended_updates,
        unknowns=comparison["unknowns"],
        raw_artifact_path=raw_path.as_posix(),
        notes="Deterministic financial-data reconciliation across provider evidence packets. Exa/Grok are intentionally excluded.",
    )


def source_ids_for_conflict(conflict: dict[str, Any], sources: list[Source]) -> list[str]:
    providers = set(conflict.get("values", {}).keys())
    ids = [source.source_id for source in sources if source.publisher in providers]
    return ids or [source.source_id for source in sources]


def source_id_for_provider(provider: str) -> str:
    return f"{provider}_packet"


def write_raw_artifact(root: Path, run_id: str, ticker: str, comparison: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "financial_compare"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_comparison.json"
    path.write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
