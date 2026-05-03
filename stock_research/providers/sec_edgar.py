from __future__ import annotations

import gzip
import json
import os
import zlib
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from stock_research.evidence import Claim, EvidencePacket, Source, default_packet_path, new_packet, write_packet


SEC_COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANY_FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
SEC_ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"


class SecEdgarError(RuntimeError):
    pass


@dataclass(frozen=True)
class SecCompany:
    ticker: str
    cik: str
    name: str
    exchange: str = ""


def resolve_sec_user_agent(user_agent: str | None = None) -> str:
    value = user_agent or os.getenv("SEC_USER_AGENT") or os.getenv("STOCK_RESEARCH_SEC_USER_AGENT")
    if not value:
        raise SecEdgarError(
            "SEC EDGAR requests require a declared User-Agent. Set SEC_USER_AGENT or pass --user-agent."
        )
    return value


def fetch_json(url: str, user_agent: str, timeout: int = 30) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = decode_response_body(response.read(), response.headers.get("Content-Encoding", ""))
            return json.loads(body.decode("utf-8"))
    except HTTPError as exc:
        raise SecEdgarError(f"SEC request failed with HTTP {exc.code}: {url}") from exc
    except URLError as exc:
        raise SecEdgarError(f"SEC request failed: {url}: {exc.reason}") from exc


def decode_response_body(body: bytes, content_encoding: str = "") -> bytes:
    encoding = content_encoding.lower()
    if "gzip" in encoding or body.startswith(b"\x1f\x8b"):
        return gzip.decompress(body)
    if "deflate" in encoding:
        return zlib.decompress(body)
    return body


def cik10(cik: str | int) -> str:
    return str(cik).strip().lstrip("0").zfill(10)


def resolve_ticker(
    ticker: str,
    user_agent: str,
    fetcher: Callable[[str, str], dict[str, Any]] = fetch_json,
) -> SecCompany:
    ticker_upper = ticker.upper().strip()
    data = fetcher(SEC_COMPANY_TICKERS_URL, user_agent)
    fields = data.get("fields", [])
    rows = data.get("data", [])
    if not fields or not rows:
        raise SecEdgarError("SEC ticker mapping response did not include fields/data.")

    for row in rows:
        record = dict(zip(fields, row))
        if str(record.get("ticker", "")).upper() == ticker_upper:
            return SecCompany(
                ticker=ticker_upper,
                cik=cik10(record.get("cik", "")),
                name=str(record.get("name", "")),
                exchange=str(record.get("exchange", "")),
            )
    raise SecEdgarError(f"Ticker not found in SEC ticker mapping: {ticker_upper}")


def fetch_submissions(
    cik: str,
    user_agent: str,
    fetcher: Callable[[str, str], dict[str, Any]] = fetch_json,
) -> dict[str, Any]:
    return fetcher(SEC_SUBMISSIONS_URL.format(cik=cik10(cik)), user_agent)


def fetch_company_facts(
    cik: str,
    user_agent: str,
    fetcher: Callable[[str, str], dict[str, Any]] = fetch_json,
) -> dict[str, Any]:
    return fetcher(SEC_COMPANY_FACTS_URL.format(cik=cik10(cik)), user_agent)


def build_sec_company_packet(
    ticker: str,
    user_agent: str,
    run_id: str,
    root: Path,
    include_facts: bool = False,
    current_date: date | None = None,
    fetcher: Callable[[str, str], dict[str, Any]] = fetch_json,
    latest_count: int = 10,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    company = resolve_ticker(ticker, user_agent, fetcher)
    submissions = fetch_submissions(company.cik, user_agent, fetcher)
    facts = fetch_company_facts(company.cik, user_agent, fetcher) if include_facts else None

    raw_paths = write_raw_artifacts(root, run_id, company.ticker, submissions, facts)
    packet = submissions_to_packet(company, submissions, facts, raw_paths, today, latest_count)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, *raw_paths]


def submissions_to_packet(
    company: SecCompany,
    submissions: dict[str, Any],
    facts: dict[str, Any] | None,
    raw_paths: list[Path],
    today: date,
    latest_count: int = 10,
) -> EvidencePacket:
    recent = submissions.get("filings", {}).get("recent", {})
    filings = recent_filings(recent, latest_count)
    source_id = "sec_submissions"
    sources = [
        Source(
            source_id=source_id,
            provider="sec_edgar",
            source_type="filing",
            title=f"SEC submissions for {company.ticker}",
            url=SEC_SUBMISSIONS_URL.format(cik=company.cik),
            publisher="U.S. Securities and Exchange Commission",
            accessed_at=today.isoformat(),
            artifact_path=raw_paths[0].as_posix() if raw_paths else "",
            notes=f"CIK {company.cik}; exchange {company.exchange}",
        )
    ]
    if facts is not None:
        sources.append(
            Source(
                source_id="sec_companyfacts",
                provider="sec_edgar",
                source_type="filing",
                title=f"SEC company facts for {company.ticker}",
                url=SEC_COMPANY_FACTS_URL.format(cik=company.cik),
                publisher="U.S. Securities and Exchange Commission",
                accessed_at=today.isoformat(),
                artifact_path=raw_paths[1].as_posix() if len(raw_paths) > 1 else "",
                notes="Aggregated XBRL company facts.",
            )
        )

    latest_forms = ", ".join(f"{item['form']} filed {item['filingDate']}" for item in filings[:5]) or "no recent filings"
    claims = [
        Claim(
            claim=f"{company.ticker} SEC submissions were retrieved.",
            evidence=f"Company name: {company.name}; CIK: {company.cik}; exchange: {company.exchange}.",
            source_ids=[source_id],
            confidence="high",
            impact="medium",
            novelty="new",
        ),
        Claim(
            claim=f"Latest SEC filing forms for {company.ticker}: {latest_forms}.",
            evidence=json.dumps(filings[:5], sort_keys=True),
            source_ids=[source_id],
            confidence="high",
            impact="medium",
            novelty="new",
        ),
    ]
    if facts is not None:
        claims.append(
            Claim(
                claim=f"{company.ticker} SEC company facts were retrieved.",
                evidence=f"Company facts include taxonomies: {', '.join(sorted(facts.get('facts', {}).keys())) or 'unknown'}.",
                source_ids=["sec_companyfacts"],
                confidence="high",
                impact="medium",
                novelty="new",
            )
        )

    unknowns = []
    if not filings:
        unknowns.append("No recent SEC filings were found in the submissions response.")

    packet = new_packet(
        provider="sec_edgar",
        subject_type="company",
        subject_id=company.ticker,
        time_window=f"latest_{latest_count}_filings",
        current_date=today,
        sources=sources,
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_paths[0].as_posix() if raw_paths else "",
        notes="SEC EDGAR API requires no API key, but requests must declare a User-Agent.",
    )
    return packet


def recent_filings(recent: dict[str, list[Any]], limit: int) -> list[dict[str, str]]:
    forms = recent.get("form", [])
    filing_dates = recent.get("filingDate", [])
    accession_numbers = recent.get("accessionNumber", [])
    primary_documents = recent.get("primaryDocument", [])
    report_dates = recent.get("reportDate", [])
    results = []
    for index, form in enumerate(forms[:limit]):
        accession = value_at(accession_numbers, index)
        filing = {
            "form": str(form),
            "filingDate": value_at(filing_dates, index),
            "reportDate": value_at(report_dates, index),
            "accessionNumber": accession,
            "primaryDocument": value_at(primary_documents, index),
        }
        filing["filingUrl"] = filing_url(accession, filing["primaryDocument"]) if accession else ""
        results.append(filing)
    return results


def filing_url(accession_number: str, primary_document: str) -> str:
    cik_prefix = accession_number.split("-")[0].lstrip("0")
    accession_no_dashes = accession_number.replace("-", "")
    return f"{SEC_ARCHIVES_BASE_URL}/{cik_prefix}/{accession_no_dashes}/{primary_document}"


def value_at(values: list[Any], index: int) -> str:
    if index >= len(values):
        return ""
    value = values[index]
    return "" if value is None else str(value)


def write_raw_artifacts(
    root: Path,
    run_id: str,
    ticker: str,
    submissions: dict[str, Any],
    facts: dict[str, Any] | None,
) -> list[Path]:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "sec_edgar"
    raw_dir.mkdir(parents=True, exist_ok=True)
    submissions_path = raw_dir / f"{ticker.upper()}_submissions.json"
    submissions_path.write_text(json.dumps(submissions, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    paths = [submissions_path]
    if facts is not None:
        facts_path = raw_dir / f"{ticker.upper()}_companyfacts.json"
        facts_path.write_text(json.dumps(facts, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        paths.append(facts_path)
    return paths


def default_sec_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-sec"
