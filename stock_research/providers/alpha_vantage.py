from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from stock_research.evidence import Claim, EvidencePacket, Source, default_packet_path, new_packet, write_packet


ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"
ALPHA_VANTAGE_DOCS = "https://www.alphavantage.co/documentation/"


class AlphaVantageError(RuntimeError):
    pass


@dataclass(frozen=True)
class AlphaVantageCompanyOptions:
    ticker: str
    include_statements: bool = False


def resolve_alpha_vantage_api_key(api_key: str | None = None) -> str:
    value = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
    if not value:
        raise AlphaVantageError("Alpha Vantage requests require ALPHA_VANTAGE_API_KEY or --api-key.")
    return value


def fetch_json(
    function: str,
    api_key: str,
    params: dict[str, Any] | None = None,
    timeout: int = 60,
    retry_after_seconds: float = 1.2,
) -> dict[str, Any]:
    query = {key: value for key, value in (params or {}).items() if value not in {"", None}}
    query["function"] = function
    query["apikey"] = api_key
    request = Request(
        f"{ALPHA_VANTAGE_BASE_URL}?{urlencode(query)}",
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
        raise AlphaVantageError(f"Alpha Vantage request failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise AlphaVantageError(f"Alpha Vantage request failed: {exc.reason}") from exc
    if is_rate_limit_payload(payload) and retry_after_seconds > 0:
        time.sleep(retry_after_seconds)
        return fetch_json(function, api_key, params, timeout=timeout, retry_after_seconds=0)
    for key in ("Error Message", "Information", "Note"):
        if key in payload:
            raise AlphaVantageError(str(payload[key]))
    return payload


def fetch_alpha_vantage_company_snapshot(options: AlphaVantageCompanyOptions, api_key: str) -> dict[str, Any]:
    ticker = options.ticker.upper()
    snapshot: dict[str, Any] = {
        "ticker": ticker,
        "global_quote": fetch_json("GLOBAL_QUOTE", api_key, {"symbol": ticker}),
    }
    time.sleep(1.1)
    snapshot["overview"] = fetch_json("OVERVIEW", api_key, {"symbol": ticker})
    if options.include_statements:
        time.sleep(1.1)
        snapshot["income_statement"] = fetch_json("INCOME_STATEMENT", api_key, {"symbol": ticker})
        time.sleep(1.1)
        snapshot["balance_sheet"] = fetch_json("BALANCE_SHEET", api_key, {"symbol": ticker})
        time.sleep(1.1)
        snapshot["cash_flow"] = fetch_json("CASH_FLOW", api_key, {"symbol": ticker})
        time.sleep(1.1)
        snapshot["earnings"] = fetch_json("EARNINGS", api_key, {"symbol": ticker})
    return snapshot


def is_rate_limit_payload(payload: dict[str, Any]) -> bool:
    message = " ".join(str(payload.get(key, "")) for key in ("Information", "Note"))
    return "1 request per second" in message.lower()


def build_alpha_vantage_company_packet(
    options: AlphaVantageCompanyOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[AlphaVantageCompanyOptions, str], dict[str, Any]] = fetch_alpha_vantage_company_snapshot,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    ticker = options.ticker.upper()
    try:
        snapshot = fetcher(options, api_key)
    except AlphaVantageError as exc:
        if not is_unavailable_error(exc):
            raise
        snapshot = unavailable_snapshot(ticker, exc)
        raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
        packet = alpha_vantage_unavailable_to_packet(ticker, snapshot, raw_path, today)
        packet_path = default_packet_path(root, run_id, packet)
        write_packet(packet, packet_path)
        return packet, [packet_path, raw_path]

    raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
    packet = alpha_vantage_snapshot_to_packet(ticker, snapshot, raw_path, today, options.include_statements)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def is_unavailable_error(error: Exception) -> bool:
    message = str(error).lower()
    return "rate limit" in message or "premium" in message or "please subscribe" in message


def unavailable_snapshot(ticker: str, error: Exception) -> dict[str, Any]:
    return {
        "ticker": ticker.upper(),
        "status": "rate_limit_unavailable",
        "provider": "alpha_vantage",
        "error": str(error),
    }


def alpha_vantage_unavailable_to_packet(
    ticker: str,
    snapshot: dict[str, Any],
    raw_path: Path,
    today: date,
) -> EvidencePacket:
    ticker_upper = ticker.upper()
    source_id = "alpha_vantage_rate_limit_unavailable"
    source = Source(
        source_id=source_id,
        provider="alpha_vantage",
        source_type="market_data",
        title=f"Alpha Vantage unavailable for {ticker_upper} because of rate limit",
        url=ALPHA_VANTAGE_DOCS,
        publisher="Alpha Vantage",
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes="The configured Alpha Vantage key returned a rate-limit/subscription message. This is a provider-coverage gap, not company evidence.",
    )
    return new_packet(
        provider="alpha_vantage",
        subject_type="company",
        subject_id=ticker_upper,
        time_window="rate_limit_unavailable",
        current_date=today,
        sources=[source],
        claims=[
            Claim(
                claim=f"Alpha Vantage data was unavailable for {ticker_upper} because of API rate limits or subscription limits.",
                evidence=json.dumps(
                    {
                        "status": snapshot.get("status"),
                        "provider": "alpha_vantage",
                        "error_type": "rate_limit_unavailable",
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
            "Alpha Vantage fundamentals were unavailable because of rate limits or subscription limits; rely on yfinance, Polygon/Massive, FMP, SEC, and source-backed research for this run."
        ],
        raw_artifact_path=raw_path.as_posix(),
        notes="Unavailable-provider packet written so planned-provider quality gates distinguish rate-limit coverage gaps from missing execution.",
    )


def alpha_vantage_snapshot_to_packet(
    ticker: str,
    snapshot: dict[str, Any],
    raw_path: Path,
    today: date,
    include_statements: bool,
) -> EvidencePacket:
    ticker_upper = ticker.upper()
    source_id = "alpha_vantage_company_snapshot"
    source = Source(
        source_id=source_id,
        provider="alpha_vantage",
        source_type="market_data",
        title=f"Alpha Vantage company snapshot for {ticker_upper}",
        url=f"{ALPHA_VANTAGE_BASE_URL}?function=OVERVIEW&symbol={ticker_upper}",
        publisher="Alpha Vantage",
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes="Global Quote and Overview; optionally statements and earnings. Rate limits can be tight on free keys.",
    )
    metrics = extract_alpha_vantage_metrics(snapshot)
    claims = [
        Claim(
            claim=f"Alpha Vantage quote and overview snapshot retrieved for {ticker_upper}.",
            evidence=json.dumps(metrics, sort_keys=True),
            source_ids=[source_id],
            confidence="medium",
            impact="medium",
            novelty="new",
        )
    ]
    if include_statements:
        claims.append(
            Claim(
                claim=f"Alpha Vantage financial statement and earnings endpoints were retrieved for {ticker_upper}.",
                evidence="Included income statement, balance sheet, cash flow, and earnings raw payloads.",
                source_ids=[source_id],
                confidence="medium",
                impact="medium",
                novelty="new",
            )
        )
    unknowns = [f"Missing Alpha Vantage metric: {key}" for key, value in metrics.items() if value in {"", None}]
    return new_packet(
        provider="alpha_vantage",
        subject_type="company",
        subject_id=ticker_upper,
        time_window="quote_overview_snapshot",
        current_date=today,
        sources=[source],
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes="Use Alpha Vantage as a cross-check/fallback provider; be mindful of rate limits.",
    )


def extract_alpha_vantage_metrics(snapshot: dict[str, Any]) -> dict[str, Any]:
    quote = snapshot.get("global_quote", {}).get("Global Quote", {})
    overview = snapshot.get("overview", {})
    return {
        "company_name": overview.get("Name", ""),
        "exchange": overview.get("Exchange", ""),
        "currency": overview.get("Currency", ""),
        "sector": overview.get("Sector", ""),
        "industry": overview.get("Industry", ""),
        "country": overview.get("Country", ""),
        "market_cap": overview.get("MarketCapitalization", ""),
        "pe_ratio": overview.get("PERatio", ""),
        "peg_ratio": overview.get("PEGRatio", ""),
        "price_to_book_ratio": overview.get("PriceToBookRatio", ""),
        "profit_margin": overview.get("ProfitMargin", ""),
        "revenue_ttm": overview.get("RevenueTTM", ""),
        "eps": overview.get("EPS", ""),
        "latest_trading_day": quote.get("07. latest trading day", ""),
        "latest_price": quote.get("05. price", ""),
        "previous_close": quote.get("08. previous close", ""),
        "volume": quote.get("06. volume", ""),
    }


def write_raw_artifact(root: Path, run_id: str, ticker: str, snapshot: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "alpha_vantage"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def default_alpha_vantage_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-alpha-vantage"
