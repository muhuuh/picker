from __future__ import annotations

import json
import os
from dataclasses import dataclass
from dataclasses import replace
from datetime import date
import hashlib
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from stock_research.evidence import Claim, EvidencePacket, Source, default_packet_path, new_packet, write_packet


XAI_RESPONSES_URL = "https://api.x.ai/v1/responses"
XAI_DOCS_TOOLS_OVERVIEW = "https://docs.x.ai/developers/tools/overview"
XAI_DOCS_WEB_SEARCH = "https://docs.x.ai/developers/tools/web-search"
XAI_DOCS_X_SEARCH = "https://docs.x.ai/developers/tools/x-search"
XAI_DOCS_CITATIONS = "https://docs.x.ai/developers/tools/citations"


class XaiGrokError(RuntimeError):
    pass


@dataclass(frozen=True)
class XaiXSearchOptions:
    prompt: str
    subject_type: str
    subject_id: str
    research_kind: str = "x_sentiment"
    model: str = "grok-4.3"
    tool_type: str = "x_search"
    from_date: str = ""
    to_date: str = ""
    allowed_x_handles: tuple[str, ...] = ()
    excluded_x_handles: tuple[str, ...] = ()
    allowed_domains: tuple[str, ...] = ()
    excluded_domains: tuple[str, ...] = ()
    enable_image_understanding: bool = False
    enable_video_understanding: bool = False
    artifact_id: str = ""


def resolve_xai_api_key(api_key: str | None = None) -> str:
    value = api_key or os.getenv("XAI_API_KEY")
    if not value:
        raise XaiGrokError("xAI Grok requests require XAI_API_KEY or --api-key.")
    return value


def fetch_json(url: str, api_key: str, payload: dict[str, Any], timeout: int = 150) -> dict[str, Any]:
    last_timeout: TimeoutError | None = None
    for attempt in range(2):
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Picker Stock Research/0.1",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            last_timeout = exc
            if attempt == 0:
                continue
            break
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise XaiGrokError(f"xAI request failed with HTTP {exc.code}: {body}") from exc
        except URLError as exc:
            raise XaiGrokError(f"xAI request failed: {exc.reason}") from exc
    raise XaiGrokError(f"xAI request timed out after 2 attempt(s) with {timeout}s timeout.") from last_timeout


def build_xai_x_search_payload(options: XaiXSearchOptions) -> dict[str, Any]:
    if not options.prompt.strip():
        raise XaiGrokError("xAI Grok prompt is required.")
    tool = build_search_tool(options)

    return {
        "model": options.model,
        "input": [{"role": "user", "content": options.prompt}],
        "tools": [tool],
    }


def build_search_tool(options: XaiXSearchOptions) -> dict[str, Any]:
    tool_type = (options.tool_type or "x_search").strip()
    if tool_type == "x_search":
        if options.allowed_domains or options.excluded_domains:
            raise XaiGrokError("xAI x_search does not support web domain filters; use web_search.")
        tool: dict[str, Any] = {"type": "x_search"}
        if options.allowed_x_handles:
            tool["allowed_x_handles"] = list(options.allowed_x_handles[:10])
        if options.excluded_x_handles:
            tool["excluded_x_handles"] = list(options.excluded_x_handles[:10])
        if "allowed_x_handles" in tool and "excluded_x_handles" in tool:
            raise XaiGrokError("xAI x_search cannot use allowed_x_handles and excluded_x_handles together.")
        if options.from_date:
            tool["from_date"] = options.from_date
        if options.to_date:
            tool["to_date"] = options.to_date
        if options.enable_image_understanding:
            tool["enable_image_understanding"] = True
        if options.enable_video_understanding:
            tool["enable_video_understanding"] = True
        return tool

    if tool_type == "web_search":
        if options.allowed_x_handles or options.excluded_x_handles:
            raise XaiGrokError("xAI web_search does not support X handle filters; use x_search.")
        if options.from_date or options.to_date:
            raise XaiGrokError("xAI web_search does not support from_date/to_date; put recency requirements in the prompt.")
        tool = {"type": "web_search"}
        if options.allowed_domains and options.excluded_domains:
            raise XaiGrokError("xAI web_search cannot use allowed_domains and excluded_domains together.")
        filters: dict[str, Any] = {}
        if options.allowed_domains:
            filters["allowed_domains"] = list(options.allowed_domains[:5])
        if options.excluded_domains:
            filters["excluded_domains"] = list(options.excluded_domains[:5])
        if filters:
            tool["filters"] = filters
        if options.enable_image_understanding:
            tool["enable_image_understanding"] = True
        if options.enable_video_understanding:
            raise XaiGrokError("xAI web_search does not support video understanding.")
        return tool

    raise XaiGrokError(f"Unsupported xAI search tool: {tool_type}.")


def build_xai_x_search_packet(
    options: XaiXSearchOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[str, str, dict[str, Any]], dict[str, Any]] = fetch_json,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    payload = build_xai_x_search_payload(options)
    response = fetcher(XAI_RESPONSES_URL, api_key, payload)
    artifact_name = artifact_suffix(options.artifact_id, f"{options.tool_type}_{options.research_kind}_{options.subject_id}_{short_digest(options.prompt)}")
    raw_path = write_raw_artifact(root, run_id, artifact_name, {"payload": payload, "response": response})
    packet = xai_response_to_packet(options, response, raw_path, today)
    packet = with_packet_suffix(packet, artifact_name)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def xai_response_to_packet(
    options: XaiXSearchOptions,
    response: dict[str, Any],
    raw_path: Path,
    today: date,
) -> EvidencePacket:
    text = clean_text(extract_output_text(response))
    citation_urls = extract_citations(response, text)
    sources = [
        Source(
            source_id=f"xai_x_source_{index}",
            provider="xai_grok",
            source_type=xai_source_type(options, url),
            title=f"xAI Grok citation {index}",
            url=url,
            publisher="X via xAI Grok" if xai_source_type(options, url) == "social" else source_publisher(url),
            accessed_at=today.isoformat(),
            artifact_path=raw_path.as_posix(),
            notes=xai_source_notes(options),
        )
        for index, url in enumerate(citation_urls, start=1)
    ]
    if not sources:
        sources = [
            Source(
                source_id="xai_grok_raw_response",
                provider="xai_grok",
                source_type="social" if options.tool_type == "x_search" else "web",
                title=f"xAI Grok {options.tool_type} response for {options.subject_id}",
                publisher="xAI Grok",
                accessed_at=today.isoformat(),
                artifact_path=raw_path.as_posix(),
                notes=xai_source_notes(options, no_citations=True),
            )
        ]

    claims = [
        Claim(
            claim=f"xAI Grok {options.research_kind} research completed for {options.subject_id}.",
            evidence=truncate(text or "No output text returned.", 4000),
            source_ids=[source.source_id for source in sources],
            confidence="medium" if citation_urls else "low",
            impact="medium",
            novelty="new",
        )
    ]
    unknowns = []
    if not text:
        unknowns.append("xAI Grok response did not include extractable output text.")
    if not citation_urls:
        unknowns.append("xAI Grok response did not include citation URLs.")

    return new_packet(
        provider="xai_grok",
        subject_type=options.subject_type,
        subject_id=options.subject_id,
        time_window=time_window(options),
        current_date=today,
        sources=sources,
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes=xai_packet_notes(options),
    )


def xai_source_type(options: XaiXSearchOptions, url: str) -> str:
    if options.tool_type == "x_search" and "x.com/" in url:
        return "social"
    return "web"


def xai_source_notes(options: XaiXSearchOptions, no_citations: bool = False) -> str:
    if options.tool_type == "web_search":
        base = "Citation surfaced by Grok web_search. Treat as auxiliary web evidence until independently verified."
    else:
        base = "Citation surfaced by Grok x_search. Treat as social evidence unless independently verified."
    if no_citations:
        return base + " No citation URLs were returned, so confidence is lower."
    return base


def xai_packet_notes(options: XaiXSearchOptions) -> str:
    if options.tool_type == "web_search":
        return "Uses xAI Grok Responses API with built-in web_search for auxiliary company deep-dive/news context. Verify material facts with filings, financial providers, Exa, or company sources."
    return "Uses xAI Grok Responses API with built-in x_search. This replaces direct X API usage."


def stock_sentiment_prompt(ticker: str, company_name: str = "") -> str:
    label = f"{ticker.upper()} {company_name}".strip()
    return (
        f"Search X deeply for recent investor discussion about {label}. "
        "Act as a chronically-online technology/stock analyst with an investor's filter for signal over noise. "
        "The goal is not a sentiment label; it is to surface actionable, non-obvious investor insight from X that a human "
        "would not get from a generic news summary. Use citations to specific X posts/accounts wherever possible. "
        "Be concrete: mention handles, who seems credible vs promotional, what claim is spreading, what changed recently, "
        "whether the narrative is early or crowded, and what would verify or falsify it. "
        "Minimum information density: at least 5 concrete account/post references when available, at least 3 bullish claims, "
        "at least 3 bearish/skeptical claims, at least 3 non-obvious or under-discussed angles, and at least 3 research checks. "
        "Write with these exact sections: "
        "1) Executive X pulse - 4-6 sentences on what the X community currently believes, what changed in the last 14 days, and why it matters. "
        "2) Trend evolution - how the narrative changed vs prior weeks/months; identify acceleration, cooling, divergence, or new debate. "
        "3) Verified facts people are reacting to - separate facts that should be cross-checked with filings/news. "
        "4) Recurring bullish arguments - concrete claims, catalysts, product/tech/industry narratives, and who is saying them. "
        "5) Recurring bearish or skeptical arguments - concrete risks, counters, valuation concerns, execution worries, and who is saying them. "
        "6) Non-obvious or under-discussed angles - second-order implications, customer/supplier/competitor read-throughs, hidden risks, or asymmetric upside. "
        "7) Strategic partnerships, investments, and ecosystem leverage - if relevant, cover AI model partners, cloud commitments, custom silicon, major customers, supplier dependencies, and hidden optionality. "
        "8) Notable accounts/posts worth reviewing - handles, why they matter, whether they look expert/informed/promotional, and citation links. "
        "9) Hype/noise/spam level - assess whether discussion is informed, technical, promotional, bot-heavy, or crowded. "
        "10) Rumors or unverified claims - label speculation clearly and state how to verify it. "
        "11) Investor implications and scorecard - specific research checks plus a compact table with Signal, Evidence, Confidence, What would confirm, What would invalidate. "
        "Do not give buy/sell instructions. Separate verified facts, social narrative, and speculation. Avoid generic phrasing; every bullet should teach a concrete investor insight."
    )


def company_deep_dive_prompt(ticker: str, company_name: str = "") -> str:
    label = f"{ticker.upper()} {company_name}".strip()
    return (
        f"Use current web search and browsing for an evidence-based investor deep dive on {label}. "
        "Prioritize sources with current company facts, recent news, filings/IR pages, reputable financial data, analyst coverage, and credible industry context. "
        "Clearly label facts, consensus estimates, analyst opinion, rumors/speculation, and your synthesis. "
        "Include data recency in each section where possible. Do not give buy/sell instructions. "
        "Write clean markdown with these exact sections: "
        "1) Business & Technology Overview - what the company does, core products/technology, customers/end markets, and moat/strengths. "
        "2) Industry Context & Competitive Landscape - industry health over the next 1-2 years, key competitors, advantages, disadvantages, and market position. "
        "3) Latest News & Rumors - most recent material news, catalysts, controversies, and rumors; label unverified items clearly. "
        "4) Financial Snapshot - market cap, current P/E, forward P/E, revenue growth, margins, cash/debt, and other KPIs if material; state when unavailable. "
        "5) Analyst Forecasts - consensus target range, ratings mix, implied upside/downside, and source/date caveats if available. "
        "6) Catalysts & Tailwinds - concrete drivers that could change the thesis. "
        "7) Risks & Headwinds - valuation, execution, competition, balance-sheet, cyclicality, regulatory, or dilution risks. "
        "8) Overall Assessment & Research Checks - balanced synthesis, why it is or is not worth close monitoring, and the next 3-5 verification tasks. "
        "Every bullet should contain a concrete investor insight, not generic filler. Use citations wherever possible."
    )


def industry_sentiment_prompt(topic: str) -> str:
    return (
        f"Search X deeply for recent investor and expert discussion about {topic}. "
        "Act as a chronically-online market scout looking for trends, hidden champions, raw diamonds, emerging tickers, "
        "and niche companies before they become obvious. Use citations to specific X posts/accounts where possible. "
        "Be concrete: mention handles, why the account/post matters, what is expert signal vs promotional noise, what changed recently, "
        "which companies are being pulled into the narrative, and which claims need external verification. "
        "Minimum information density: at least 8 account/post references when available, at least 8 surfaced companies/tickers/private names, "
        "at least 5 demand/technology drivers, at least 6 bullish narratives, at least 5 risks or skeptical arguments, and at least 5 non-obvious angles. "
        "Write with these exact sections: "
        "1) Industry X pulse - what people currently believe, what changed recently, whether the narrative is early or crowded, and why it matters. "
        "2) Trend evolution - how the narrative changed vs prior weeks/months; identify acceleration, cooling, divergence, or new debate. "
        "3) Key technologies and demand drivers - concrete technologies, customers, policy/macro tailwinds, bottlenecks, and read-throughs. "
        "4) Companies being discussed - incumbents, newcomers, hidden champions, private companies, and public tickers when available. "
        "5) Recurring bullish narratives - at least 6 concrete catalysts, beneficiaries, or supply-chain read-throughs, with who is pushing them. "
        "6) Recurring bearish/skeptical narratives - at least 5 concrete risks, fraud/noise signals, valuation concerns, execution problems, and who is pushing them. "
        "7) Non-obvious or contrarian angles - second-order beneficiaries, suppliers, bottlenecks, unloved names, or reasons the popular trade could be wrong. "
        "8) Hype/noise/rumors map - what looks credible, promotional, bot-like, or unverified. "
        "9) Candidate follow-up list - tickers/companies, why surfaced, source type, verification needed, and priority. "
        "10) Investor implications and scorecard - what to research next plus a compact table with Candidate/Theme, Why interesting, Verification status, Main risk, Next action. "
        "Separate verified facts, social narrative, and speculation. Avoid generic phrasing; every bullet should teach a concrete investor insight."
    )


def latest_news_prompt(topic: str) -> str:
    return (
        f"Search X for the latest material news and market-moving developments about {topic}. "
        "Act as a chronically-online investor research scout. Identify what changed, who is discussing it, niche companies or tickers "
        "being surfaced, which claims need verification, what looks like rumor or hype, and what an investor should investigate next. "
        "Minimum information density: at least 5 account/post references when available, at least 5 concrete developments or claims, "
        "at least 3 non-obvious implications, at least 3 surfaced companies/tickers/private names, and at least 3 verification tasks. "
        "Write with these exact sections: "
        "1) Executive X pulse; 2) What changed recently; 3) Expert/community split; 4) Companies/tickers surfaced; "
        "5) Non-obvious implications; 6) Hype/noise/rumors; 7) Verification tasks; 8) Investor scorecard. "
        "Separate verified facts, social sentiment, and speculation. Include citations to X posts where possible. Avoid generic phrasing."
    )


def extract_output_text(response: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in response.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                parts.append(str(content.get("text", "")))
    if parts:
        return "\n\n".join(part for part in parts if part)
    return str(response.get("output_text", ""))


def extract_citations(response: dict[str, Any], text: str) -> list[str]:
    urls: list[str] = []
    for url in response.get("citations", []) or []:
        add_unique(urls, str(url))
    for item in response.get("output", []):
        for content in item.get("content", []):
            for annotation in content.get("annotations", []) or []:
                if annotation.get("type") == "url_citation":
                    add_unique(urls, str(annotation.get("url", "")))
    for url in markdown_citation_urls(text):
        add_unique(urls, url)
    return urls


def markdown_citation_urls(text: str) -> list[str]:
    urls: list[str] = []
    marker = "]("
    start = 0
    while True:
        index = text.find(marker, start)
        if index == -1:
            return urls
        url_start = index + len(marker)
        url_end = text.find(")", url_start)
        if url_end == -1:
            return urls
        candidate = text[url_start:url_end]
        if candidate.startswith(("http://", "https://")):
            urls.append(candidate)
        start = url_end + 1


def add_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)


def source_publisher(url: str) -> str:
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            return url[len(prefix) :].split("/", 1)[0].removeprefix("www.")
    return "web"


def time_window(options: XaiXSearchOptions) -> str:
    if options.tool_type == "web_search":
        return "current_web_search"
    if options.from_date or options.to_date:
        return f"{options.from_date or 'begin'}_to_{options.to_date or 'now'}"
    return "current_x_search"


def write_raw_artifact(root: Path, run_id: str, name: str, payload: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "xai_grok"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def truncate(value: str, max_length: int) -> str:
    value = clean_text(value)
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def clean_text(value: str) -> str:
    repaired = repair_latin1_mojibake(value)
    if repaired:
        value = repaired
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": "-",
        "\u2014": "-",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for bad, good in replacements.items():
        value = value.replace(bad, good)
    return value


def repair_latin1_mojibake(value: str) -> str:
    if "\u00e2" not in value and "\u00c2" not in value:
        return value
    try:
        repaired = value.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return value
    if len(repaired.strip()) < len(value.strip()) * 0.8:
        return value
    return repaired


def safe_name(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_") or "unknown"


def short_digest(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def artifact_suffix(artifact_id: str, fallback: str) -> str:
    return compact_artifact_suffix(safe_name(artifact_id or fallback))


def compact_artifact_suffix(value: str, max_length: int = 72) -> str:
    if len(value) <= max_length:
        return value
    digest = short_digest(value)
    prefix = value[: max_length - len(digest) - 1].rstrip("_")
    return f"{prefix}_{digest}"


def with_packet_suffix(packet: EvidencePacket, suffix: str) -> EvidencePacket:
    packet_id = compact_artifact_suffix(f"{packet.packet_id}_{safe_name(suffix)}", max_length=110)
    return replace(packet, packet_id=packet_id)


def default_xai_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-xai"
