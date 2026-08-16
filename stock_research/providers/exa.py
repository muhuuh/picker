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
from stock_research.text_excerpt import complete_sentence_excerpt


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
        payload["systemPrompt"] = (
            "Prefer timely, source-diverse, reputable news. Prioritize primary sources, major financial news, "
            "and relevant trade press. Avoid duplicate or syndicated articles. Focus on material developments "
            "such as earnings, guidance, regulation, litigation, customers, suppliers, products, M&A, and management changes."
        )
    if options.search_mode == "industry":
        payload["systemPrompt"] = (
            "Prefer primary sources, reputable trade publications, concrete company mentions, and source-diverse evidence. "
            "Avoid duplicate or low-signal market commentary."
        )
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
    packet = with_source_id_suffix(packet, short_digest(artifact_name))
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
    packet = with_source_id_suffix(packet, short_digest(artifact_name))
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
        highlight_text = result_evidence_text(result, options.search_mode)
        if highlight_text:
            full_evidence = clean_text(str(highlight_text))
            claims.append(
                Claim(
                    claim=f"Relevant Exa result: {result.get('title', result.get('url', 'untitled'))}",
                    evidence=full_evidence,
                    source_ids=[source.source_id],
                    confidence="medium",
                    impact="medium",
                    novelty="new",
                    display_excerpt=complete_sentence_excerpt(full_evidence, 800).text,
                    full_evidence_path=raw_path.as_posix(),
                    full_evidence_selector=f"response.results[{len(claims) - 1}]",
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
            full_evidence = clean_text(str(excerpt))
            claims.append(
                Claim(
                    claim=f"Exa content excerpt from {result.get('title', result.get('url', 'URL'))}",
                    evidence=full_evidence,
                    source_ids=[source.source_id],
                    confidence="medium",
                    impact="medium",
                    novelty="new",
                    display_excerpt=complete_sentence_excerpt(full_evidence, 1000).text,
                    full_evidence_path=raw_path.as_posix(),
                    full_evidence_selector=f"response.results[{len(claims) - 1}]",
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


def result_evidence_text(result: dict[str, Any], search_mode: str) -> str:
    highlight_text = first_text(result.get("highlights", [])) or result.get("summary", "")
    if search_mode != "company":
        return highlight_text

    entity_texts: list[str] = []
    for entity in result.get("entities", []) or []:
        if not isinstance(entity, dict):
            continue
        properties = entity.get("properties", {})
        if not isinstance(properties, dict):
            continue
        name = str(properties.get("name", "")).strip()
        description = str(properties.get("description", "")).strip()
        if name or description:
            entity_texts.append(" ".join(part for part in [name, description] if part))
    parts = [part for part in [str(result.get("title", "")).strip(), *entity_texts, highlight_text] if part]
    return clean_text("\n".join(parts))


def with_source_id_suffix(packet: EvidencePacket, suffix: str) -> EvidencePacket:
    if not suffix:
        return packet
    source_id_map = {source.source_id: f"{source.source_id}_{suffix}" for source in packet.sources}
    return replace(
        packet,
        sources=[replace(source, source_id=source_id_map.get(source.source_id, source.source_id)) for source in packet.sources],
        claims=[replace(claim, source_ids=remap_source_ids(claim.source_ids, source_id_map)) for claim in packet.claims],
        risks=[replace(risk, source_ids=remap_source_ids(risk.source_ids, source_id_map)) for risk in packet.risks],
        contradictions=[
            replace(contradiction, source_ids=remap_source_ids(contradiction.source_ids, source_id_map))
            for contradiction in packet.contradictions
        ],
        recommended_updates=[
            replace(update, source_ids=remap_source_ids(update.source_ids, source_id_map)) for update in packet.recommended_updates
        ],
    )


def remap_source_ids(source_ids: list[str], source_id_map: dict[str, str]) -> list[str]:
    return [source_id_map.get(source_id, source_id) for source_id in source_ids]


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


def search_time_window(options: ExaSearchOptions) -> str:
    if options.start_published_date or options.end_published_date:
        return f"{options.start_published_date or 'begin'}_to_{options.end_published_date or 'now'}"
    return "current_search"


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


def default_exa_run_id(current_date: date | None = None) -> str:
    today = current_date or date.today()
    return f"{today.isoformat()}_manual-exa"
