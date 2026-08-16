from __future__ import annotations

import json
import re
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
    "forward_pe": 0.05,
    "peg_ratio": 0.05,
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
    "fifty_two_week_low": 0.02,
    "fifty_two_week_high": 0.02,
}
PREFERRED_PROVIDERS = {
    "latest_price": ["polygon", "fmp", "alpha_vantage", "yfinance"],
    "market_cap": ["fmp", "polygon", "alpha_vantage", "yfinance"],
    "pe_ratio": ["fmp", "alpha_vantage", "yfinance"],
    "forward_pe": ["fmp", "alpha_vantage", "yfinance"],
    "price_to_sales_ttm": ["fmp", "alpha_vantage", "yfinance"],
    "price_to_book_ratio": ["fmp", "alpha_vantage", "yfinance"],
    "peg_ratio": ["alpha_vantage", "yfinance"],
    "ev_to_ebitda_ttm": ["fmp", "yfinance"],
    "revenue_ttm": ["fmp", "alpha_vantage", "yfinance"],
    "eps": ["alpha_vantage", "yfinance"],
    "profit_margin": ["alpha_vantage", "yfinance"],
    "debt_to_equity_ttm": ["fmp", "yfinance"],
    "company_name": ["fmp", "polygon", "alpha_vantage", "yfinance"],
    "exchange": ["fmp", "alpha_vantage", "polygon", "yfinance"],
    "currency": ["fmp", "alpha_vantage", "polygon", "yfinance"],
    "sector": ["fmp", "alpha_vantage", "yfinance"],
    "industry": ["fmp", "alpha_vantage", "yfinance"],
    "country": ["fmp", "alpha_vantage", "polygon"],
}
NON_MATERIAL_TEXT_CONFLICT_METRICS = {"company_name", "exchange", "sector", "industry"}
TRUSTED_VALUATION_PROVIDERS = {"fmp", "alpha_vantage"}
MARKET_PRICE_PROVIDERS = {"polygon", "yfinance"}
VALUATION_SANITY_METRICS = {"latest_price", "market_cap", "pe_ratio", "fifty_two_week_low", "fifty_two_week_high"}
PROVIDER_METRIC_MAP = {
    "yfinance": {
        "company_name": "company_name",
        "currency": "currency",
        "latest_price": "last_price",
        "market_cap": "market_cap",
        "pe_ratio": "pe_ratio",
        "forward_pe": "forward_pe",
        "peg_ratio": "peg_ratio",
        "price_to_sales_ttm": "price_to_sales_ttm",
        "price_to_book_ratio": "price_to_book_ratio",
        "ev_to_ebitda_ttm": "ev_to_ebitda_ttm",
        "revenue_ttm": "revenue_ttm",
        "eps": "eps",
        "profit_margin": "profit_margin",
        "debt_to_equity_ttm": "debt_to_equity_ttm",
        "exchange": "exchange",
        "country": "country",
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

    valuation_sanity_warnings = apply_valuation_sanity_checks(consensus)
    unknowns.extend(f"Valuation sanity warning: {warning}" for warning in valuation_sanity_warnings)

    return {
        "consensus": consensus,
        "conflicts": conflicts,
        "unknowns": unknowns,
        "provider_count": len({observation.provider for observation in observations}),
        "valuation_sanity_warnings": valuation_sanity_warnings,
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


def apply_valuation_sanity_checks(consensus: dict[str, Any]) -> list[str]:
    """Flag valuation snapshots that look internally plausible but still unsafe to trust."""

    latest = result_number(consensus, "latest_price")
    low = result_number(consensus, "fifty_two_week_low")
    high = result_number(consensus, "fifty_two_week_high")
    pe_result = consensus.get("pe_ratio") or {}
    headline_providers = providers_for_metrics(consensus, ["latest_price", "market_cap", "pe_ratio"])
    trusted_coverage = bool(headline_providers & TRUSTED_VALUATION_PROVIDERS)
    market_only_coverage = bool(headline_providers) and headline_providers <= MARKET_PRICE_PROVIDERS
    warnings: list[str] = []

    extreme_range = False
    if low is not None and high is not None and low > 0 and high > low:
        range_multiple = high / low
        if range_multiple >= 20:
            extreme_range = True
            warnings.append(
                f"52-week range is unusually wide ({range_multiple:.1f}x from low to high); check for split, corporate-action, ticker, or stale-data issues before using valuation metrics."
            )

    outside_range = False
    if latest is not None and high is not None and high > 0 and latest > high * 1.15:
        outside_range = True
        warnings.append(
            f"Latest price {latest:.4g} is more than 15% above the recorded 52-week high {high:.4g}; verify price and range before using valuation metrics."
        )
    if latest is not None and low is not None and low > 0 and latest < low * 0.85:
        outside_range = True
        warnings.append(
            f"Latest price {latest:.4g} is more than 15% below the recorded 52-week low {low:.4g}; verify price and range before using valuation metrics."
        )

    single_provider_pe = pe_result.get("value") not in {"", None} and len(pe_result.get("providers", [])) <= 1
    if market_only_coverage and (extreme_range or outside_range):
        warnings.append(
            "Headline valuation coverage comes only from market-price providers (Polygon/yfinance) without FMP or Alpha Vantage cross-check; treat price, market cap, and P/E as verification-needed."
        )
    if single_provider_pe and (extreme_range or outside_range):
        warnings.append("P/E ratio is single-provider while the valuation snapshot has weak or suspicious coverage; do not treat the multiple as clean consensus.")

    warnings = dedupe_preserve_order(warnings)
    if not warnings:
        return []

    severe = outside_range or (extreme_range and not trusted_coverage)
    for metric in VALUATION_SANITY_METRICS:
        add_sanity_warnings(consensus, metric, warnings, severe=severe)
    return warnings


def result_number(consensus: dict[str, Any], metric: str) -> float | None:
    result = consensus.get(metric)
    if not isinstance(result, dict):
        return None
    return to_float(result.get("value"))


def providers_for_metrics(consensus: dict[str, Any], metrics: list[str]) -> set[str]:
    providers: set[str] = set()
    for metric in metrics:
        result = consensus.get(metric)
        if isinstance(result, dict):
            providers.update(str(provider) for provider in result.get("providers", []) if provider)
    return providers


def add_sanity_warnings(consensus: dict[str, Any], metric: str, warnings: list[str], severe: bool) -> None:
    result = consensus.get(metric)
    if not isinstance(result, dict):
        return
    existing = list(result.get("sanity_warnings") or [])
    result["sanity_warnings"] = dedupe_preserve_order([*existing, *warnings])
    if severe and result.get("confidence") != "low":
        result["confidence"] = "low"
        result["reason"] = f"{result.get('reason', '').rstrip()} Valuation sanity warning requires cross-provider verification.".strip()


def dedupe_preserve_order(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_text_metric(metric: str, value: Any) -> str:
    text = str(value).strip().lower()
    if metric == "company_name":
        text = normalize_company_name(text)
        return " ".join(text.split())
    if metric == "country" and text in {"us", "usa", "united states", "united states of america"}:
        return "united states"
    if metric == "exchange":
        return normalize_exchange(text)
    if metric == "currency":
        return text.upper()
    return " ".join(text.split())


def normalize_company_name(text: str) -> str:
    cleaned = text.replace("&", " and ")
    for phrase in (
        "class a common stock",
        "class b common stock",
        "class c common stock",
        "common stock",
        "ordinary shares",
        "american depositary shares",
        "american depository shares",
        "american depositary receipt",
        "american depository receipt",
    ):
        cleaned = cleaned.replace(phrase, " ")
    cleaned = re.sub(r"\b(class|ordinary|shares?|ads|adr)\b", " ", cleaned)
    cleaned = re.sub(r"[.,()]", " ", cleaned)
    return " ".join(cleaned.split())


def normalize_exchange(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()
    compact = cleaned.replace(" ", "")
    if compact in {"xnas", "nasdaq", "nms", "ngm", "ncm", "nasdaqgs", "nasdaqgm", "nasdaqcm"}:
        return "nasdaq"
    if cleaned in {"nasdaq capital market", "nasdaq global market", "nasdaq global select market"}:
        return "nasdaq"
    if compact in {"xnys", "nyse", "nyq"} or cleaned == "new york stock exchange":
        return "nyse"
    if compact in {"otcqb", "oqb"}:
        return "otcqb"
    if compact in {"otcqx", "oqx"}:
        return "otcqx"
    if compact in {"otc", "pinx", "pink"}:
        return "otc"
    return " ".join(cleaned.split())


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
            "values": result.get("values", {}),
            "reason": result.get("reason", ""),
            "sanity_warnings": result.get("sanity_warnings", []),
        }
        for metric, result in comparison["consensus"].items()
        if result["status"] != "non_numeric"
    }
    conflicts = comparison["conflicts"]
    material_conflicts = [conflict for conflict in conflicts if is_material_financial_conflict(str(conflict.get("metric", "")))]
    valuation_sanity_warnings = list(comparison.get("valuation_sanity_warnings") or [])
    claims = [
        Claim(
            claim=f"Financial data comparison completed for {ticker}.",
            evidence=json.dumps(consensus_summary, sort_keys=True),
            source_ids=source_ids,
            confidence="high" if not material_conflicts and not valuation_sanity_warnings else "medium",
            impact="medium",
            novelty="new",
        )
    ]
    contradictions = [
        Contradiction(
            current_repo_claim=f"Financial provider conflict for {conflict['metric']}.",
            new_evidence=json.dumps(conflict["values"], sort_keys=True),
            source_ids=source_ids_for_conflict(conflict, sources),
            suggested_action="Preserve the provider disagreement and avoid updating this metric without review.",
        )
        for conflict in material_conflicts
    ]
    recommended_updates = [
        RecommendedUpdate(
            target_file="stock_tracking/stock_info_files/",
            update_type="company_file",
            summary=f"Update {ticker} financial snapshot with consensus metrics from financial_compare packet.",
            needs_human_review=bool(material_conflicts or valuation_sanity_warnings),
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


def is_material_financial_conflict(metric: str) -> bool:
    return metric not in NON_MATERIAL_TEXT_CONFLICT_METRICS


def source_id_for_provider(provider: str) -> str:
    return f"{provider}_packet"


def write_raw_artifact(root: Path, run_id: str, ticker: str, comparison: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "financial_compare"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_comparison.json"
    path.write_text(json.dumps(comparison, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
