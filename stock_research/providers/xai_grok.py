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
    from_date: str = ""
    to_date: str = ""
    allowed_x_handles: tuple[str, ...] = ()
    excluded_x_handles: tuple[str, ...] = ()
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

    return {
        "model": options.model,
        "input": [{"role": "user", "content": options.prompt}],
        "tools": [tool],
    }


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
    artifact_name = artifact_suffix(options.artifact_id, f"x_search_{options.research_kind}_{options.subject_id}_{short_digest(options.prompt)}")
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
    text = extract_output_text(response)
    citation_urls = extract_citations(response, text)
    sources = [
        Source(
            source_id=f"xai_x_source_{index}",
            provider="xai_grok",
            source_type="social" if "x.com/" in url else "web",
            title=f"xAI Grok citation {index}",
            url=url,
            publisher="X via xAI Grok" if "x.com/" in url else source_publisher(url),
            accessed_at=today.isoformat(),
            artifact_path=raw_path.as_posix(),
            notes="Citation surfaced by Grok x_search. Treat as social evidence unless independently verified.",
        )
        for index, url in enumerate(citation_urls, start=1)
    ]
    if not sources:
        sources = [
            Source(
                source_id="xai_grok_raw_response",
                provider="xai_grok",
                source_type="social",
                title=f"xAI Grok x_search response for {options.subject_id}",
                publisher="xAI Grok",
                accessed_at=today.isoformat(),
                artifact_path=raw_path.as_posix(),
                notes="No citation URLs were returned; use only as low-confidence social signal.",
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
        notes="Uses xAI Grok Responses API with built-in x_search. This replaces direct X API usage.",
    )


def stock_sentiment_prompt(ticker: str, company_name: str = "") -> str:
    label = f"{ticker.upper()} {company_name}".strip()
    return (
        f"Search X for recent discussion about {label}. "
        "Summarize community sentiment, recurring bullish and bearish claims, notable news people are reacting to, "
        "credible accounts or posts worth reviewing, hype/noise level, rumors or unverified claims, "
        "and concrete implications for an investor. Separate verified facts, social sentiment, and speculation. "
        "Include citations to X posts where possible."
    )


def industry_sentiment_prompt(topic: str) -> str:
    return (
        f"Search X for recent discussion about {topic}. "
        "Summarize industry sentiment, emerging narratives, new public companies/tickers people are discussing, "
        "niche or under-followed companies, rumors or unverified claims, bullish and bearish arguments, "
        "likely hype cycles, credible accounts/posts worth reviewing, and concrete follow-up research tasks. "
        "Separate verified facts, social sentiment, and speculation. Include citations to X posts where possible."
    )


def latest_news_prompt(topic: str) -> str:
    return (
        f"Search X for the latest material news and market-moving developments about {topic}. "
        "Identify what changed, who is discussing it, niche companies or tickers being surfaced, which claims need verification, "
        "what looks like rumor or hype, and what an investor should investigate next. "
        "Separate verified facts, social sentiment, and speculation. Include citations to X posts where possible."
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
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def safe_name(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_") or "unknown"


def short_digest(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def artifact_suffix(artifact_id: str, fallback: str) -> str:
    return safe_name(artifact_id or fallback)


def with_packet_suffix(packet: EvidencePacket, suffix: str) -> EvidencePacket:
    return replace(packet, packet_id=f"{packet.packet_id}_{safe_name(suffix)}")


def default_xai_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-xai"
