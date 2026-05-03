from __future__ import annotations

import importlib
import json
from datetime import date
from pathlib import Path
from typing import Any, Callable

from stock_research.evidence import Claim, EvidencePacket, Source, default_packet_path, new_packet, write_packet


class YFinanceError(RuntimeError):
    pass


def fetch_yfinance_snapshot(ticker: str, period: str = "5d") -> dict[str, Any]:
    try:
        yf = importlib.import_module("yfinance")
    except ImportError as exc:
        raise YFinanceError("yfinance is not installed. Run `python -m pip install yfinance`.") from exc

    ticker_obj = yf.Ticker(ticker)
    raw_fast_info = safe_mapping(ticker_obj.fast_info)
    raw_info = safe_mapping(getattr(ticker_obj, "info", {}))
    history = safe_history(ticker_obj, period)
    return {
        "ticker": ticker.upper(),
        "fast_info": raw_fast_info,
        "info": raw_info,
        "history": history,
    }


def build_yfinance_company_packet(
    ticker: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    period: str = "5d",
    fetcher: Callable[[str, str], dict[str, Any]] = fetch_yfinance_snapshot,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    snapshot = fetcher(ticker, period)
    raw_path = write_raw_artifact(root, run_id, ticker, snapshot)
    packet = yfinance_snapshot_to_packet(ticker, snapshot, raw_path, today, period)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def yfinance_snapshot_to_packet(
    ticker: str,
    snapshot: dict[str, Any],
    raw_path: Path,
    today: date,
    period: str,
) -> EvidencePacket:
    ticker_upper = ticker.upper()
    fast_info = snapshot.get("fast_info", {})
    info = snapshot.get("info", {})
    history = snapshot.get("history", {})
    source_id = "yfinance_snapshot"
    source = Source(
        source_id=source_id,
        provider="yfinance",
        source_type="market_data",
        title=f"Yahoo Finance market data for {ticker_upper}",
        url=f"https://finance.yahoo.com/quote/{ticker_upper}",
        publisher="Yahoo Finance via yfinance",
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes="Unofficial Yahoo Finance wrapper; use for research and cross-check with paid providers for decisions.",
    )
    metrics = extract_metrics(fast_info, info)
    claims = [
        Claim(
            claim=f"yfinance market snapshot retrieved for {ticker_upper}.",
            evidence=json.dumps(metrics, sort_keys=True),
            source_ids=[source_id],
            confidence="medium",
            impact="medium",
            novelty="new",
        )
    ]
    if history:
        latest_row_key = sorted(history.keys())[-1]
        claims.append(
            Claim(
                claim=f"yfinance returned recent price history for {ticker_upper}.",
                evidence=f"period={period}; latest row {latest_row_key}: {json.dumps(history[latest_row_key], sort_keys=True)}",
                source_ids=[source_id],
                confidence="medium",
                impact="medium",
                novelty="new",
            )
        )

    unknowns = [f"Missing yfinance metric: {key}" for key, value in metrics.items() if value in {"", None}]
    return new_packet(
        provider="yfinance",
        subject_type="company",
        subject_id=ticker_upper,
        time_window=f"snapshot_plus_{period}_history",
        current_date=today,
        sources=[source],
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes="yfinance is useful for quick market-data snapshots, but should be cross-checked with FMP, Polygon, or Alpha Vantage for high-impact decisions.",
    )


def extract_metrics(fast_info: dict[str, Any], info: dict[str, Any]) -> dict[str, Any]:
    return {
        "currency": first_present(fast_info, info, "currency", "financialCurrency"),
        "last_price": first_present(fast_info, info, "lastPrice", "currentPrice", "regularMarketPrice"),
        "previous_close": first_present(fast_info, info, "previousClose", "regularMarketPreviousClose"),
        "market_cap": first_present(fast_info, info, "marketCap"),
        "pe_ratio": first_present(info, fast_info, "trailingPE", "forwardPE"),
        "fifty_two_week_low": first_present(fast_info, info, "yearLow", "fiftyTwoWeekLow"),
        "fifty_two_week_high": first_present(fast_info, info, "yearHigh", "fiftyTwoWeekHigh"),
        "exchange": first_present(info, fast_info, "exchange", "fullExchangeName"),
        "sector": first_present(info, fast_info, "sector"),
        "industry": first_present(info, fast_info, "industry"),
    }


def first_present(primary: dict[str, Any], secondary: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        for source in (primary, secondary):
            if key in source and source[key] not in {"", None}:
                return source[key]
    return ""


def safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return make_jsonable(value)
    keys = getattr(value, "keys", None)
    if callable(keys):
        result: dict[str, Any] = {}
        for key in keys():
            try:
                result[str(key)] = make_jsonable(value[key])
            except Exception:
                continue
        return result
    return {}


def safe_history(ticker_obj: Any, period: str) -> dict[str, Any]:
    try:
        history = ticker_obj.history(period=period)
    except Exception as exc:
        raise YFinanceError(f"yfinance history failed: {exc}") from exc
    to_dict = getattr(history, "to_dict", None)
    if callable(to_dict):
        try:
            return make_jsonable(to_dict(orient="index"))
        except TypeError:
            return make_jsonable(to_dict())
    return make_jsonable(history)


def make_jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): make_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_jsonable(item) for item in value]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        return make_jsonable(to_dict())
    isoformat = getattr(value, "isoformat", None)
    if callable(isoformat):
        return isoformat()
    return str(value)


def write_raw_artifact(root: Path, run_id: str, ticker: str, snapshot: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "yfinance"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_snapshot.json"
    path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def default_yfinance_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-yfinance"
