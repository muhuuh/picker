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


POLYGON_BASE_URL = "https://api.polygon.io"
POLYGON_DOCS_TICKER = "https://massive.com/docs/rest/stocks/tickers/ticker-overview"
POLYGON_DOCS_PREV_BAR = "https://massive.com/docs/rest/stocks/aggregates/previous-day-bar"


class PolygonError(RuntimeError):
    pass


@dataclass(frozen=True)
class PolygonCompanyOptions:
    ticker: str
    adjusted: bool = True


def resolve_polygon_api_key(api_key: str | None = None) -> str:
    value = api_key or os.getenv("POLYGON_API_KEY") or os.getenv("MASSIVE_API_KEY")
    if not value:
        raise PolygonError("Polygon/Massive requests require POLYGON_API_KEY, MASSIVE_API_KEY, or --api-key.")
    return value


def fetch_json(path: str, api_key: str, params: dict[str, Any] | None = None, timeout: int = 60) -> dict[str, Any]:
    query = {key: value for key, value in (params or {}).items() if value not in {"", None}}
    url = f"{POLYGON_BASE_URL}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{urlencode(query)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "Picker Stock Research/0.1",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise PolygonError(f"Polygon/Massive request failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise PolygonError(f"Polygon/Massive request failed: {exc.reason}") from exc
    if isinstance(payload, dict) and str(payload.get("status", "")).upper() in {"ERROR", "NOT_AUTHORIZED"}:
        raise PolygonError(json.dumps(payload, sort_keys=True))
    return payload


def fetch_polygon_company_snapshot(options: PolygonCompanyOptions, api_key: str) -> dict[str, Any]:
    ticker = options.ticker.upper()
    return {
        "ticker": ticker,
        "ticker_details": fetch_json(f"v3/reference/tickers/{ticker}", api_key),
        "previous_day_bar": fetch_json(f"v2/aggs/ticker/{ticker}/prev", api_key, {"adjusted": str(options.adjusted).lower()}),
    }


def build_polygon_company_packet(
    options: PolygonCompanyOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[PolygonCompanyOptions, str], dict[str, Any]] = fetch_polygon_company_snapshot,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    snapshot = fetcher(options, api_key)
    ticker = options.ticker.upper()
    raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
    packet = polygon_snapshot_to_packet(ticker, snapshot, raw_path, today, options.adjusted)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def polygon_snapshot_to_packet(
    ticker: str,
    snapshot: dict[str, Any],
    raw_path: Path,
    today: date,
    adjusted: bool,
) -> EvidencePacket:
    ticker_upper = ticker.upper()
    source_id = "polygon_company_snapshot"
    source = Source(
        source_id=source_id,
        provider="polygon",
        source_type="market_data",
        title=f"Polygon/Massive market data for {ticker_upper}",
        url=f"{POLYGON_BASE_URL}/v3/reference/tickers/{ticker_upper}",
        publisher="Polygon.io / Massive",
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes="Ticker details plus previous-day OHLC bar. Polygon/Massive stock data is mainly U.S. equity market data.",
    )
    metrics = extract_polygon_metrics(snapshot)
    claims = [
        Claim(
            claim=f"Polygon/Massive ticker reference and previous-day OHLC data retrieved for {ticker_upper}.",
            evidence=json.dumps(metrics, sort_keys=True),
            source_ids=[source_id],
            confidence="high",
            impact="medium",
            novelty="new",
        )
    ]
    unknowns = [f"Missing Polygon/Massive metric: {key}" for key, value in metrics.items() if value in {"", None}]
    return new_packet(
        provider="polygon",
        subject_type="company",
        subject_id=ticker_upper,
        time_window="ticker_details_plus_previous_day_bar",
        current_date=today,
        sources=[source],
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes=f"Use Polygon/Massive to cross-check U.S. ticker identity and previous-day OHLCV. adjusted={adjusted}.",
    )


def extract_polygon_metrics(snapshot: dict[str, Any]) -> dict[str, Any]:
    details = snapshot.get("ticker_details", {}).get("results", {})
    prev_bar = first_record(snapshot.get("previous_day_bar", {}).get("results"))
    return {
        "company_name": details.get("name", ""),
        "ticker": details.get("ticker", snapshot.get("ticker", "")),
        "primary_exchange": details.get("primary_exchange", ""),
        "currency": details.get("currency_name", ""),
        "market": details.get("market", ""),
        "locale": details.get("locale", ""),
        "market_cap": details.get("market_cap", ""),
        "sic_description": details.get("sic_description", ""),
        "previous_open": prev_bar.get("o", ""),
        "previous_high": prev_bar.get("h", ""),
        "previous_low": prev_bar.get("l", ""),
        "previous_close": prev_bar.get("c", ""),
        "previous_volume": prev_bar.get("v", ""),
        "previous_vwap": prev_bar.get("vw", ""),
    }


def first_record(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    if isinstance(value, dict):
        return value
    return {}


def write_raw_artifact(root: Path, run_id: str, ticker: str, snapshot: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "polygon"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def default_polygon_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-polygon"
