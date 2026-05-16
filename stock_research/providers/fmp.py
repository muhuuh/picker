from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from stock_research.evidence import Claim, EvidencePacket, Source, default_packet_path, new_packet, write_packet


FMP_BASE_URL = "https://financialmodelingprep.com/stable"
FMP_DOCS = "https://site.financialmodelingprep.com/developer/docs/stable"
FMP_SNAPSHOT_ENDPOINTS = (
    ("quote", "quote"),
    ("profile", "profile"),
    ("key_metrics_ttm", "key-metrics-ttm"),
    ("ratios_ttm", "ratios-ttm"),
)
FMP_STATEMENT_ENDPOINTS = (
    ("income_statement_ttm", "income-statement-ttm"),
    ("balance_sheet_statement_ttm", "balance-sheet-statement-ttm"),
    ("cash_flow_statement_ttm", "cash-flow-statement-ttm"),
)


class FmpError(RuntimeError):
    pass


@dataclass(frozen=True)
class FmpCompanyOptions:
    ticker: str
    include_statements: bool = False


def resolve_fmp_api_key(api_key: str | None = None) -> str:
    value = api_key or os.getenv("FMP_API_KEY") or os.getenv("FINANCIAL_MODELING_PREP_API_KEY")
    if not value:
        raise FmpError("FMP requests require FMP_API_KEY, FINANCIAL_MODELING_PREP_API_KEY, or --api-key.")
    return value


def resolve_fmp_fallback_api_key(api_key: str | None = None) -> str:
    return (api_key or os.getenv("FMP_API_KEY2") or "").strip()


def fetch_json(path: str, api_key: str, params: dict[str, Any] | None = None, timeout: int = 60) -> Any:
    query = {key: value for key, value in (params or {}).items() if value not in {"", None}}
    query["apikey"] = api_key
    url = f"{FMP_BASE_URL}/{path.lstrip('?')}"
    separator = "&" if "?" in url else "?"
    request = Request(
        f"{url}{separator}{urlencode(query)}",
        headers={
            "Accept": "application/json",
            "User-Agent": "Picker Stock Research/0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise FmpError(f"FMP request failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise FmpError(f"FMP request failed: {exc.reason}") from exc
    if isinstance(payload, dict) and payload.get("Error Message"):
        raise FmpError(str(payload["Error Message"]))
    return payload


def fetch_fmp_company_snapshot(options: FmpCompanyOptions, api_key: str) -> dict[str, Any]:
    ticker = options.ticker.upper()
    snapshot: dict[str, Any] = {"ticker": ticker}
    endpoint_errors: list[dict[str, str]] = []
    endpoints = list(FMP_SNAPSHOT_ENDPOINTS)
    if options.include_statements:
        endpoints.extend(FMP_STATEMENT_ENDPOINTS)
    for key, path in endpoints:
        try:
            snapshot[key] = fetch_json(path, api_key, {"symbol": ticker})
        except FmpError as exc:
            if not is_fallback_eligible_error(exc):
                raise
            snapshot[key] = []
            endpoint_errors.append(
                {
                    "endpoint": key,
                    "path": path,
                    "error_type": fmp_unavailable_error_type(exc) or "provider_unavailable",
                    "error": sanitize_error_text(exc, [api_key]),
                }
            )
    if endpoint_errors:
        snapshot["endpoint_errors"] = endpoint_errors
    if len(endpoint_errors) == len(endpoints):
        first_error = endpoint_errors[0]["error"]
        raise FmpError(f"FMP all configured snapshot endpoints unavailable for {ticker}: {first_error}")
    return snapshot


def build_fmp_company_packet(
    options: FmpCompanyOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[FmpCompanyOptions, str], dict[str, Any]] = fetch_fmp_company_snapshot,
    fallback_api_key: str | None = None,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    ticker = options.ticker.upper()
    attempts: list[dict[str, str]] = []
    fallback_used_for_partial = False
    try:
        snapshot = fetcher(options, api_key)
        secondary_key = normalize_fallback_key(api_key, fallback_api_key)
        if secondary_key and snapshot.get("endpoint_errors"):
            attempts.extend(endpoint_attempt_records("primary", snapshot))
            try:
                fallback_snapshot = fetcher(options, secondary_key)
                snapshot = merge_fmp_partial_snapshots(snapshot, fallback_snapshot)
                fallback_used_for_partial = True
                if fallback_snapshot.get("endpoint_errors"):
                    attempts.extend(endpoint_attempt_records("secondary", fallback_snapshot))
            except FmpError as fallback_exc:
                if not is_fallback_eligible_error(fallback_exc):
                    raise
                attempts.append(attempt_record("secondary", fallback_exc, api_key, fallback_api_key))
        snapshot = annotate_credential_metadata(
            snapshot,
            api_key_label="primary",
            fallback_used=fallback_used_for_partial,
            attempts=attempts,
        )
    except FmpError as exc:
        if not is_fallback_eligible_error(exc):
            raise
        attempts.append(attempt_record("primary", exc, api_key, fallback_api_key))
        secondary_key = normalize_fallback_key(api_key, fallback_api_key)
        if secondary_key:
            try:
                snapshot = fetcher(options, secondary_key)
                snapshot = annotate_credential_metadata(
                    snapshot,
                    api_key_label="secondary",
                    fallback_used=True,
                    attempts=attempts,
                )
            except FmpError as fallback_exc:
                if not is_fallback_eligible_error(fallback_exc):
                    raise
                attempts.append(attempt_record("secondary", fallback_exc, api_key, fallback_api_key))
                snapshot = unavailable_snapshot(ticker, fallback_exc, attempts=attempts, fallback_attempted=True)
                snapshot["error"] = sanitize_error_text(fallback_exc, [api_key, fallback_api_key or ""])
        else:
            snapshot = unavailable_snapshot(ticker, exc, attempts=attempts, fallback_attempted=False)
            snapshot["error"] = sanitize_error_text(exc, [api_key, fallback_api_key or ""])
        raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
        if is_unavailable_snapshot(snapshot):
            packet = fmp_unavailable_to_packet(ticker, snapshot, raw_path, today)
            packet_path = default_packet_path(root, run_id, packet)
            write_packet(packet, packet_path)
            return packet, [packet_path, raw_path]
        packet = fmp_snapshot_to_packet(ticker, snapshot, raw_path, today, options.include_statements)
        packet_path = default_packet_path(root, run_id, packet)
        write_packet(packet, packet_path)
        return packet, [packet_path, raw_path]

    raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
    packet = fmp_snapshot_to_packet(ticker, snapshot, raw_path, today, options.include_statements)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def is_subscription_unavailable_error(error: Exception) -> bool:
    return fmp_unavailable_error_type(error) == "subscription_unavailable"


def is_fallback_eligible_error(error: Exception) -> bool:
    return bool(fmp_unavailable_error_type(error))


def fmp_unavailable_error_type(error: Exception) -> str:
    message = str(error).lower()
    if "http 402" in message or "premium query parameter" in message or "subscription" in message or "premium" in message:
        return "subscription_unavailable"
    if "http 429" in message or "rate limit" in message or "too many requests" in message or "quota" in message:
        return "rate_limit_unavailable"
    if (
        "http 401" in message
        or "http 403" in message
        or "unauthorized" in message
        or "forbidden" in message
        or "invalid api key" in message
        or "invalid apikey" in message
    ):
        return "credential_unavailable"
    return ""


def unavailable_snapshot(
    ticker: str,
    error: Exception,
    attempts: list[dict[str, str]] | None = None,
    fallback_attempted: bool = False,
) -> dict[str, Any]:
    error_type = fmp_unavailable_error_type(error) or "provider_unavailable"
    return {
        "ticker": ticker.upper(),
        "status": error_type,
        "provider": "fmp",
        "error": str(error),
        "credential": {
            "fallback_supported": True,
            "fallback_attempted": fallback_attempted,
            "final_status": error_type,
            "attempts": attempts or [],
        },
    }


def normalize_fallback_key(primary_key: str, fallback_api_key: str | None) -> str:
    secondary_key = (fallback_api_key or "").strip()
    if not secondary_key or secondary_key == primary_key:
        return ""
    return secondary_key


def attempt_record(label: str, error: Exception, primary_key: str, fallback_api_key: str | None) -> dict[str, str]:
    return {
        "api_key_label": label,
        "error_type": fmp_unavailable_error_type(error) or "provider_unavailable",
        "error": sanitize_error_text(error, [primary_key, fallback_api_key or ""]),
    }


def endpoint_attempt_records(label: str, snapshot: dict[str, Any]) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    for item in snapshot.get("endpoint_errors", []) or []:
        if not isinstance(item, dict):
            continue
        records.append(
            {
                "api_key_label": label,
                "endpoint": str(item.get("endpoint", "")),
                "error_type": str(item.get("error_type", "provider_unavailable")),
                "error": str(item.get("error", "")),
            }
        )
    return records


def sanitize_error_text(error: Exception, secrets: list[str]) -> str:
    text = str(error)
    for secret in secrets:
        if secret:
            text = text.replace(secret, "[redacted]")
    return text


def annotate_credential_metadata(
    snapshot: dict[str, Any],
    api_key_label: str,
    fallback_used: bool,
    attempts: list[dict[str, str]],
) -> dict[str, Any]:
    result = dict(snapshot)
    result["credential"] = {
        "api_key_label": api_key_label,
        "fallback_supported": True,
        "fallback_used": fallback_used,
        "prior_attempts": attempts,
    }
    return result


def merge_fmp_partial_snapshots(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    result = dict(primary)
    secondary_errors = {
        str(error.get("endpoint", "")): error
        for error in secondary.get("endpoint_errors", []) or []
        if isinstance(error, dict)
    }
    remaining_errors: list[dict[str, str]] = []
    for error in primary.get("endpoint_errors", []) or []:
        if not isinstance(error, dict):
            continue
        endpoint = str(error.get("endpoint", ""))
        fallback_value = secondary.get(endpoint)
        if has_fmp_payload(fallback_value):
            result[endpoint] = fallback_value
            continue
        merged_error = dict(error)
        fallback_error = secondary_errors.get(endpoint)
        if fallback_error:
            merged_error["fallback_error_type"] = str(fallback_error.get("error_type", "provider_unavailable"))
            merged_error["fallback_error"] = str(fallback_error.get("error", ""))
        remaining_errors.append(merged_error)
    if remaining_errors:
        result["endpoint_errors"] = remaining_errors
    else:
        result.pop("endpoint_errors", None)
    return result


def has_fmp_payload(value: Any) -> bool:
    if isinstance(value, list):
        return bool(value)
    if isinstance(value, dict):
        return bool(value)
    return value not in {"", None}


def is_unavailable_snapshot(snapshot: dict[str, Any]) -> bool:
    return str(snapshot.get("status", "")).endswith("_unavailable")


def fmp_unavailable_to_packet(
    ticker: str,
    snapshot: dict[str, Any],
    raw_path: Path,
    today: date,
) -> EvidencePacket:
    ticker_upper = ticker.upper()
    status = str(snapshot.get("status") or "subscription_unavailable")
    source_id = f"fmp_{status}"
    credential = snapshot.get("credential", {})
    source = Source(
        source_id=source_id,
        provider="fmp",
        source_type="market_data",
        title=f"FMP unavailable for {ticker_upper}",
        url=FMP_DOCS,
        publisher="Financial Modeling Prep",
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes="The configured FMP key(s) returned a tier, quota, or credential limitation. This is a provider-coverage gap, not company evidence.",
    )
    return new_packet(
        provider="fmp",
        subject_type="company",
        subject_id=ticker_upper,
        time_window=status,
        current_date=today,
        sources=[source],
        claims=[
            Claim(
                claim=f"FMP data was unavailable for {ticker_upper} after configured credential attempts.",
                evidence=json.dumps(
                    {
                        "status": snapshot.get("status"),
                        "provider": "fmp",
                        "error_type": status,
                        "fallback_attempted": credential.get("fallback_attempted", False),
                        "attempt_labels": [
                            attempt.get("api_key_label", "")
                            for attempt in credential.get("attempts", [])
                            if isinstance(attempt, dict)
                        ],
                    },
                    sort_keys=True,
                ),
                source_ids=[source_id],
                confidence="high",
                impact="low",
                novelty="new",
            )
        ],
        unknowns=[
            "FMP fundamentals were unavailable under the configured key(s); rely on yfinance, Polygon/Massive, Alpha Vantage, SEC, and source-backed research for this run."
        ],
        raw_artifact_path=raw_path.as_posix(),
        notes="Unavailable-provider packet written so planned-provider quality gates distinguish credential/tier/quota coverage gaps from missing execution.",
    )


def fmp_snapshot_to_packet(
    ticker: str,
    snapshot: dict[str, Any],
    raw_path: Path,
    today: date,
    include_statements: bool,
) -> EvidencePacket:
    ticker_upper = ticker.upper()
    source_id = "fmp_company_snapshot"
    source = Source(
        source_id=source_id,
        provider="fmp",
        source_type="market_data",
        title=f"FMP company snapshot for {ticker_upper}",
        url=f"{FMP_BASE_URL}/quote?symbol={ticker_upper}",
        publisher="Financial Modeling Prep",
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes="FMP stable API snapshot: quote, profile, TTM key metrics, TTM ratios, and optionally TTM statements.",
    )
    metrics = extract_fmp_metrics(snapshot)
    endpoint_errors = [
        error
        for error in snapshot.get("endpoint_errors", []) or []
        if isinstance(error, dict)
    ]
    claims = [
        Claim(
            claim=f"FMP company market-data and fundamentals snapshot retrieved for {ticker_upper}.",
            evidence=json.dumps(
                {
                    **metrics,
                    "endpoint_errors": [
                        {
                            "endpoint": error.get("endpoint", ""),
                            "error_type": error.get("error_type", ""),
                            "fallback_error_type": error.get("fallback_error_type", ""),
                        }
                        for error in endpoint_errors
                    ],
                },
                sort_keys=True,
            ),
            source_ids=[source_id],
            confidence="medium" if endpoint_errors else "high",
            impact="medium",
            novelty="new",
        )
    ]
    if include_statements:
        claims.append(
            Claim(
                claim=f"FMP TTM financial statement endpoints were retrieved for {ticker_upper}.",
                evidence="Included income-statement-ttm, balance-sheet-statement-ttm, and cash-flow-statement-ttm raw payloads.",
                source_ids=[source_id],
                confidence="high",
                impact="medium",
                novelty="new",
            )
        )
    unknowns = [f"Missing FMP metric: {key}" for key, value in metrics.items() if value in {"", None}]
    unknowns.extend(
        f"FMP endpoint unavailable: {error.get('endpoint', '')} ({error.get('error_type', 'provider_unavailable')})"
        for error in endpoint_errors
    )
    return new_packet(
        provider="fmp",
        subject_type="company",
        subject_id=ticker_upper,
        time_window="snapshot_ttm",
        current_date=today,
        sources=[source],
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes="Use FMP to cross-check yfinance market data and add TTM valuation/fundamental ratios.",
    )


def extract_fmp_metrics(snapshot: dict[str, Any]) -> dict[str, Any]:
    quote = first_record(snapshot.get("quote"))
    profile = first_record(snapshot.get("profile"))
    key_metrics = first_record(snapshot.get("key_metrics_ttm"))
    ratios = first_record(snapshot.get("ratios_ttm"))
    return {
        "company_name": first_present(profile, quote, "companyName", "name"),
        "exchange": first_present(profile, quote, "exchangeShortName", "exchange"),
        "currency": first_present(profile, quote, "currency"),
        "price": first_present(quote, profile, "price"),
        "market_cap": first_present(quote, profile, "marketCap", "mktCap"),
        "pe_ratio_ttm": first_present(ratios, key_metrics, "priceToEarningsRatioTTM", "peRatioTTM"),
        "price_to_sales_ttm": first_present(ratios, key_metrics, "priceToSalesRatioTTM"),
        "ev_to_ebitda_ttm": first_present(key_metrics, ratios, "enterpriseValueOverEBITDATTM", "enterpriseValueMultipleTTM"),
        "free_cash_flow_per_share_ttm": first_present(key_metrics, ratios, "freeCashFlowPerShareTTM"),
        "debt_to_equity_ttm": first_present(ratios, key_metrics, "debtToEquityRatioTTM"),
        "sector": first_present(profile, quote, "sector"),
        "industry": first_present(profile, quote, "industry"),
        "country": first_present(profile, quote, "country"),
    }


def first_record(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    if isinstance(value, dict):
        return value
    return {}


def first_present(primary: dict[str, Any], secondary: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        for source in (primary, secondary):
            if key in source and source[key] not in {"", None}:
                return source[key]
    return ""


def write_raw_artifact(root: Path, run_id: str, ticker: str, snapshot: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "fmp"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def default_fmp_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-fmp"
