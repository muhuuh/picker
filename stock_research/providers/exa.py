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
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from stock_research.evidence import Claim, EvidencePacket, Source, default_packet_path, new_packet, write_packet


EXA_SEARCH_URL = "https://api.exa.ai/search"
EXA_CONTENTS_URL = "https://api.exa.ai/contents"
EXA_DOCS_SEARCH_API = "https://exa.ai/docs/reference/search-api-guide-for-coding-agents"
EXA_DOCS_SEARCH_BEST_PRACTICES = "https://exa.ai/docs/reference/search-best-practices"
EXA_DOCS_COMPANY = "https://exa.ai/docs/reference/verticals/company-for-coding-agents"
EXA_DOCS_NEWS = "https://exa.ai/docs/reference/verticals/news-for-coding-agents"
EXA_DOCS_CONTENTS_API = "https://exa.ai/docs/reference/contents-api-guide-for-coding-agents"
EXA_DOCS_CONTENTS_BEST_PRACTICES = "https://exa.ai/docs/reference/contents-best-practices"


class ExaError(RuntimeError):
    pass


@dataclass(frozen=True)
class ExaSearchOptions:
    query: str
    subject_type: str
    subject_id: str
    search_mode: str = "general"
    search_type: str = "auto"
    num_results: int = 10
    start_published_date: str = ""
    end_published_date: str = ""
    include_domains: tuple[str, ...] = ()
    exclude_domains: tuple[str, ...] = ()
    max_age_hours: int | None = None
    artifact_id: str = ""


@dataclass(frozen=True)
class ExaContentsOptions:
    urls: tuple[str, ...]
    subject_type: str
    subject_id: str
    highlights_query: str = ""
    text_max_characters: int | None = None
    max_age_hours: int | None = None
    livecrawl_timeout: int = 12000
    artifact_id: str = ""


def resolve_exa_api_key(api_key: str | None = None) -> str:
    value = api_key or os.getenv("EXA_API_KEY")
    if not value:
        raise ExaError("Exa requests require EXA_API_KEY or --api-key.")
    return value


def fetch_json(
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: int = 45,
) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Picker Stock Research/0.1",
            "x-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ExaError(f"Exa request failed with HTTP {exc.code}: {body}") from exc
    except URLError as exc:
        raise ExaError(f"Exa request failed: {exc.reason}") from exc


def build_exa_search_payload(options: ExaSearchOptions) -> dict[str, Any]:
    if not options.query.strip():
        raise ExaError("Exa search query is required.")
    if options.search_mode not in {"general", "company", "news", "industry"}:
        raise ExaError(f"Unsupported Exa search mode: {options.search_mode}")
    if options.search_mode == "company" and (
        options.start_published_date or options.end_published_date or options.exclude_domains
    ):
        raise ExaError("Exa company search does not support date filters or excludeDomains.")

    payload: dict[str, Any] = {
        "query": options.query,
        "type": options.search_type,
        "numResults": options.num_results,
        "contents": {"highlights": True},
    }
    if options.search_mode == "company":
        payload["category"] = "company"
    if options.search_mode == "news":
        payload["systemPrompt"] = "Prefer timely, source-diverse news and avoid duplicate articles."
    if options.search_mode == "industry":
        payload["systemPrompt"] = "Prefer primary sources, trade publications, and concrete company mentions."
    if options.start_published_date:
        payload["startPublishedDate"] = options.start_published_date
    if options.end_published_date:
        payload["endPublishedDate"] = options.end_published_date
    if options.include_domains:
        payload["includeDomains"] = list(options.include_domains)
    if options.exclude_domains:
        payload["excludeDomains"] = list(options.exclude_domains)
    if options.max_age_hours is not None:
        payload["contents"]["maxAgeHours"] = options.max_age_hours
    return payload


def build_exa_contents_payload(options: ExaContentsOptions) -> dict[str, Any]:
    if not options.urls:
        raise ExaError("At least one URL is required for Exa contents.")
    payload: dict[str, Any] = {
        "urls": list(options.urls),
        "highlights": True if not options.highlights_query else {"query": options.highlights_query},
        "livecrawlTimeout": options.livecrawl_timeout,
    }
    if options.text_max_characters:
        payload["text"] = {"maxCharacters": options.text_max_characters}
    if options.max_age_hours is not None:
        payload["maxAgeHours"] = options.max_age_hours
    return payload


def build_exa_search_packet(
    options: ExaSearchOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[str, str, dict[str, Any]], dict[str, Any]] = fetch_json,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    payload = build_exa_search_payload(options)
    response = fetcher(EXA_SEARCH_URL, api_key, payload)
    artifact_name = artifact_suffix(options.artifact_id, f"search_{options.search_mode}_{options.subject_id}_{short_digest(options.query)}")
    raw_path = write_raw_artifact(root, run_id, "exa", artifact_name, {"payload": payload, "response": response})
    packet = exa_search_to_packet(options, response, raw_path, today)
    packet = with_packet_suffix(packet, artifact_name)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def build_exa_contents_packet(
    options: ExaContentsOptions,
    api_key: str,
    run_id: str,
    root: Path,
    current_date: date | None = None,
    fetcher: Callable[[str, str, dict[str, Any]], dict[str, Any]] = fetch_json,
) -> tuple[EvidencePacket, list[Path]]:
    today = current_date or date.today()
    payload = build_exa_contents_payload(options)
    response = fetcher(EXA_CONTENTS_URL, api_key, payload)
    artifact_name = artifact_suffix(options.artifact_id, f"contents_{options.subject_id}_{short_digest('|'.join(options.urls))}")
    raw_path = write_raw_artifact(root, run_id, "exa", artifact_name, {"payload": payload, "response": response})
    packet = exa_contents_to_packet(options, response, raw_path, today)
    packet = with_packet_suffix(packet, artifact_name)
    packet_path = default_packet_path(root, run_id, packet)
    write_packet(packet, packet_path)
    return packet, [packet_path, raw_path]


def exa_search_to_packet(
    options: ExaSearchOptions,
    response: dict[str, Any],
    raw_path: Path,
    today: date,
) -> EvidencePacket:
    results = list(response.get("results", []))
    source_type = "news" if options.search_mode == "news" else "web"
    sources = [source_from_result(index, result, source_type, raw_path, today) for index, result in enumerate(results, start=1)]
    claims = [
        Claim(
            claim=f"Exa {options.search_mode} search returned {len(results)} result(s) for: {options.query}",
            evidence=f"requestId: {response.get('requestId', 'unknown')}; searchType: {response.get('searchType', 'unknown')}; cost: {response.get('costDollars', {}).get('total', 'unknown')}",
            source_ids=[source.source_id for source in sources],
            confidence="medium" if results else "low",
            impact="medium",
            novelty="new",
        )
    ]
    for source, result in zip(sources[:5], results[:5]):
        highlight_text = first_text(result.get("highlights", [])) or result.get("summary", "")
        if highlight_text:
            claims.append(
                Claim(
                    claim=f"Relevant Exa result: {result.get('title', result.get('url', 'untitled'))}",
                    evidence=truncate(str(highlight_text), 800),
                    source_ids=[source.source_id],
                    confidence="medium",
                    impact="medium",
                    novelty="new",
                )
            )

    unknowns = []
    if not results:
        unknowns.append("Exa returned no results for this query.")

    return new_packet(
        provider="exa",
        subject_type=options.subject_type,
        subject_id=options.subject_id,
        time_window=search_time_window(options),
        current_date=today,
        sources=sources,
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes="Exa search uses highlights by default for token-efficient agent workflows.",
    )


def exa_contents_to_packet(
    options: ExaContentsOptions,
    response: dict[str, Any],
    raw_path: Path,
    today: date,
) -> EvidencePacket:
    results = list(response.get("results", []))
    sources = [source_from_result(index, result, "web", raw_path, today) for index, result in enumerate(results, start=1)]
    claims = [
        Claim(
            claim=f"Exa contents extracted {len(results)} result(s) for {len(options.urls)} URL(s).",
            evidence=f"requestId: {response.get('requestId', 'unknown')}; cost: {response.get('costDollars', {}).get('total', 'unknown')}",
            source_ids=[source.source_id for source in sources],
            confidence="medium" if results else "low",
            impact="medium",
            novelty="new",
        )
    ]
    for source, result in zip(sources[:5], results[:5]):
        excerpt = first_text(result.get("highlights", [])) or result.get("summary", "") or result.get("text", "")
        if excerpt:
            claims.append(
                Claim(
                    claim=f"Exa content excerpt from {result.get('title', result.get('url', 'URL'))}",
                    evidence=truncate(str(excerpt), 1000),
                    source_ids=[source.source_id],
                    confidence="medium",
                    impact="medium",
                    novelty="new",
                )
            )

    unknowns = []
    for status in response.get("statuses", []):
        if status.get("status") == "error":
            unknowns.append(f"Exa contents failed for {status.get('id')}: {status.get('error', {}).get('tag', 'unknown_error')}")
    if not results:
        unknowns.append("Exa contents returned no extracted results.")

    return new_packet(
        provider="exa",
        subject_type=options.subject_type,
        subject_id=options.subject_id,
        time_window="contents_extraction",
        current_date=today,
        sources=sources,
        claims=claims,
        unknowns=unknowns,
        raw_artifact_path=raw_path.as_posix(),
        notes="Exa contents uses top-level highlights/text parameters, not nested contents.",
    )


def source_from_result(index: int, result: dict[str, Any], source_type: str, raw_path: Path, today: date) -> Source:
    url = str(result.get("url", ""))
    return Source(
        source_id=f"exa_result_{index}",
        provider="exa",
        source_type=source_type,
        title=str(result.get("title", "")),
        url=url,
        publisher=domain_from_url(url),
        published_at=str(result.get("publishedDate") or ""),
        accessed_at=today.isoformat(),
        artifact_path=raw_path.as_posix(),
        notes=f"author={result.get('author') or ''}; id={result.get('id') or url}",
    )


def write_raw_artifact(root: Path, run_id: str, provider: str, name: str, payload: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / provider
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def first_text(values: Any) -> str:
    if isinstance(values, list) and values:
        return str(values[0])
    if isinstance(values, str):
        return values
    return ""


def truncate(value: str, max_length: int) -> str:
    if len(value) <= max_length:
        return value
    return value[: max_length - 3].rstrip() + "..."


def search_time_window(options: ExaSearchOptions) -> str:
    if options.start_published_date or options.end_published_date:
        return f"{options.start_published_date or 'begin'}_to_{options.end_published_date or 'now'}"
    return "current_search"


def safe_name(value: str) -> str:
    return "".join(character.lower() if character.isalnum() else "_" for character in value).strip("_") or "unknown"


def short_digest(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def artifact_suffix(artifact_id: str, fallback: str) -> str:
    return safe_name(artifact_id or fallback)


def with_packet_suffix(packet: EvidencePacket, suffix: str) -> EvidencePacket:
    return replace(packet, packet_id=f"{packet.packet_id}_{safe_name(suffix)}")


def default_exa_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-exa"
