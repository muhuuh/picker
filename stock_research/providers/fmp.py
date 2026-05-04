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
    snapshot: dict[str, Any] = {
        "ticker": ticker,
        "quote": fetch_json("quote", api_key, {"symbol": ticker}),
        "profile": fetch_json("profile", api_key, {"symbol": ticker}),
        "key_metrics_ttm": fetch_json("key-metrics-ttm", api_key, {"symbol": ticker}),
        "ratios_ttm": fetch_json("ratios-ttm", api_key, {"symbol": ticker}),
    }
    if options.include_statements:
        snapshot["income_statement_ttm"] = fetch_json("income-statement-ttm", api_key, {"symbol": ticker})
        snapshot["balance_sheet_statement_ttm"] = fetch_json("balance-sheet-statement-ttm", api_key, {"symbol": ticker})
        snapshot["cash_flow_statement_ttm"] = fetch_json("cash-flow-statement-ttm", api_key, {"symbol": ticker})
    return snapshot


def build_fmp_company_packet(
    options: FmpCompanyOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[FmpCompanyOptions, str], dict[str, Any]] = fetch_fmp_company_snapshot,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    snapshot = fetcher(options, api_key)
    ticker = options.ticker.upper()
    raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
    packet = fmp_snapshot_to_packet(ticker, snapshot, raw_path, today, options.include_statements)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


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
    claims = [
        Claim(
            claim=f"FMP company market-data and fundamentals snapshot retrieved for {ticker_upper}.",
            evidence=json.dumps(metrics, sort_keys=True),
            source_ids=[source_id],
            confidence="high",
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
