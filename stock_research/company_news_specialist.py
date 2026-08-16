from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import Claim, EvidencePacket, RecommendedUpdate, Risk, Source, default_packet_path, new_packet, read_packet, write_packet
from .memory import relative_to_root
from .providers.exa import ExaContentsOptions, build_exa_contents_packet, fetch_json as fetch_exa_json
from .report_formatting import compact_complete_text
from .repo import find_repo_root


class CompanyNewsSpecialistError(RuntimeError):
    pass


@dataclass(frozen=True)
class CompanyNewsReviewResult:
    packet: EvidencePacket
    paths: list[Path]
    review: dict[str, Any]


@dataclass(frozen=True)
class CompanyNewsContentsResult:
    packet: EvidencePacket
    paths: list[Path]
    urls: list[str]


def build_company_news_contents_follow_up_packet(
    ticker: str,
    run_id: str,
    root: Path | None,
    api_key: str,
    current_date: date | None = None,
    exa_news_packet_path: Path | None = None,
    max_urls: int = 3,
    artifact_id: str = "",
    fetcher=fetch_exa_json,
) -> CompanyNewsContentsResult:
    repo_root = find_repo_root(root)
    ticker_upper = ticker.upper()
    news_path, news_packet = load_exa_news_packet(repo_root, run_id, ticker_upper, exa_news_packet_path)
    urls = select_contents_follow_up_urls(news_packet, max_urls)
    if not urls:
        raise CompanyNewsSpecialistError(f"No follow-up URLs found in Exa company-news packet {news_path}.")

    packet, paths = build_exa_contents_packet(
        options=ExaContentsOptions(
            urls=tuple(urls),
            subject_type="company",
            subject_id=ticker_upper,
            highlights_query=f"{ticker_upper} investment relevance, material developments, risks, guidance, earnings, regulation, customers",
            text_max_characters=6000,
            artifact_id=artifact_id or f"exa_contents_company_news_{ticker_upper}",
        ),
        api_key=api_key,
        run_id=run_id,
        root=repo_root,
        current_date=current_date,
        fetcher=fetcher,
    )
    return CompanyNewsContentsResult(packet=packet, paths=paths, urls=urls)


def build_company_news_specialist_packet(
    ticker: str,
    run_id: str,
    root: Path | None,
    current_date: date | None = None,
    exa_news_packet_path: Path | None = None,
) -> CompanyNewsReviewResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    ticker_upper = ticker.upper()
    news_path, news_packet = load_exa_news_packet(repo_root, run_id, ticker_upper, exa_news_packet_path)
    validate_exa_news_packet(news_packet, ticker_upper)
    contents_packets = load_exa_contents_packets(repo_root, run_id, ticker_upper)
    review = build_company_news_review(ticker_upper, news_packet, news_path, contents_packets)

    raw_path = write_raw_review(repo_root, run_id, ticker_upper, review)
    report_path = write_markdown_review(repo_root, run_id, ticker_upper, review)
    packet = review_to_packet(ticker_upper, news_path, news_packet, review, raw_path, report_path, today)
    packet_path = default_packet_path(repo_root, run_id, packet)
    write_packet(packet, packet_path)
    return CompanyNewsReviewResult(packet=packet, paths=[packet_path, raw_path, report_path], review=review)


def load_exa_news_packet(
    root: Path,
    run_id: str,
    ticker: str,
    packet_path: Path | None = None,
) -> tuple[Path, EvidencePacket]:
    if packet_path:
        path = packet_path if packet_path.is_absolute() else root / packet_path
        packet = read_packet(path)
        validate_exa_news_packet(packet, ticker)
        return path, packet

    packet_dir = root / "agents" / "runs" / run_id / "evidence_packets"
    candidates: list[tuple[Path, EvidencePacket]] = []
    for path in sorted(packet_dir.glob("*.json")):
        packet = read_packet(path)
        if packet.provider != "exa" or packet.subject_type != "company" or packet.subject_id.upper() != ticker.upper():
            continue
        if is_news_packet(packet):
            candidates.append((path, packet))
    if not candidates:
        raise CompanyNewsSpecialistError(f"No Exa company-news packet found for {ticker} in run {run_id}.")
    return max(candidates, key=lambda item: item[1].created_at)


def validate_exa_news_packet(packet: EvidencePacket, ticker: str) -> None:
    if packet.provider != "exa":
        raise CompanyNewsSpecialistError(f"Expected provider exa, got {packet.provider}.")
    if packet.subject_type != "company" or packet.subject_id.upper() != ticker.upper():
        raise CompanyNewsSpecialistError(f"Expected Exa company packet for {ticker}, got {packet.subject_type}:{packet.subject_id}.")
    if not is_news_packet(packet):
        raise CompanyNewsSpecialistError(f"Expected Exa news packet for {ticker}, got packet {packet.packet_id}.")


def is_news_packet(packet: EvidencePacket) -> bool:
    if any(source.source_type == "news" for source in packet.sources):
        return True
    return "exa_news" in packet.packet_id or "news" in packet.time_window


def load_exa_contents_packets(root: Path, run_id: str, ticker: str) -> list[tuple[Path, EvidencePacket]]:
    packet_dir = root / "agents" / "runs" / run_id / "evidence_packets"
    if not packet_dir.exists():
        return []
    packets: list[tuple[Path, EvidencePacket]] = []
    for path in sorted(packet_dir.glob("*.json")):
        packet = read_packet(path)
        if packet.provider != "exa" or packet.subject_type != "company" or packet.subject_id.upper() != ticker.upper():
            continue
        if is_contents_packet(packet):
            packets.append((path, packet))
    return packets


def is_contents_packet(packet: EvidencePacket) -> bool:
    return "contents" in packet.packet_id or packet.time_window == "contents_extraction"


def build_company_news_review(
    ticker: str,
    news_packet: EvidencePacket,
    news_path: Path,
    contents_packets: list[tuple[Path, EvidencePacket]] | None = None,
) -> dict[str, Any]:
    contents_packets = contents_packets or []
    sources = news_sources(news_packet)
    material_claims = relevant_claims(news_packet)
    contents_sources = unique_sources_by_url([source for _path, packet in contents_packets for source in packet.sources])
    contents_claims = unique_claims(
        [claim for _path, packet in contents_packets for claim in packet.claims if not claim.claim.startswith("Exa contents extracted")]
    )
    recent_sources = [source for source in sources if source.published_at]
    unknowns = list(news_packet.unknowns)
    for _path, packet in contents_packets:
        unknowns.extend(packet.unknowns)
    contradictions = [contradiction.current_repo_claim for contradiction in news_packet.contradictions]
    top_urls = [source.url for source in sources[:5] if source.url]
    extracted_urls = [source.url for source in contents_sources if source.url]
    remaining_urls = [url for url in top_urls if url not in set(extracted_urls)]

    if contradictions:
        status = "needs_human_review"
        status_reason = "News packet contains contradictions that need review before company-file updates."
    elif not sources:
        status = "partial_review"
        status_reason = "Exa news returned no source results; keep this as a low-information scan."
    elif unknowns:
        status = "partial_review"
        status_reason = "News scan found sources but has unresolved unknowns or content extraction gaps."
    elif top_urls and not contents_sources:
        status = "partial_review"
        status_reason = "News scan found source-backed headlines, but Exa contents extraction has not confirmed the high-value URLs yet."
    else:
        status = "ready_for_company_update"
        status_reason = "Company-news scan and contents follow-up produced source-backed developments for review."

    return {
        "ticker": ticker,
        "status": status,
        "status_reason": status_reason,
        "exa_news_packet": news_path.as_posix(),
        "exa_news_packet_id": news_packet.packet_id,
        "source_count": len(sources),
        "recent_source_count": len(recent_sources),
        "claim_count": len(material_claims),
        "contents_packet_count": len(contents_packets),
        "contents_source_count": len(contents_sources),
        "contents_claim_count": len(contents_claims),
        "top_sources": [source_summary(source) for source in sources[:8]],
        "material_claims": [claim_summary(claim) for claim in material_claims[:8]],
        "contents_sources": [source_summary(source) for source in contents_sources[:8]],
        "contents_claims": [claim_summary(claim) for claim in contents_claims[:8]],
        "contents_follow_up_urls": top_urls,
        "contents_extracted_urls": extracted_urls,
        "remaining_content_follow_up_urls": remaining_urls,
        "unknowns": unknowns,
        "contradictions": contradictions,
        "needs_human_review": status == "needs_human_review",
        "recommended_company_file_action": recommended_company_file_action(status, bool(top_urls)),
    }


def news_sources(packet: EvidencePacket) -> list[Source]:
    return [source for source in packet.sources if source.source_type == "news" or source.provider == "exa"]


def unique_sources_by_url(sources: list[Source]) -> list[Source]:
    unique: list[Source] = []
    seen: set[str] = set()
    for source in sources:
        key = source.url or source.source_id
        if key in seen:
            continue
        seen.add(key)
        unique.append(source)
    return unique


def unique_claims(claims: list[Claim]) -> list[Claim]:
    unique: list[Claim] = []
    seen: set[tuple[str, str]] = set()
    for claim in claims:
        key = (claim.claim, claim.evidence)
        if key in seen:
            continue
        seen.add(key)
        unique.append(claim)
    return unique


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            result.append(cleaned)
    return result


def relevant_claims(packet: EvidencePacket) -> list[Claim]:
    return [claim for claim in packet.claims if not claim.claim.lower().startswith("exa news search returned")]


def source_summary(source: Source) -> dict[str, str]:
    return {
        "source_id": source.source_id,
        "title": source.title,
        "publisher": source.publisher,
        "published_at": source.published_at,
        "url": source.url,
    }


def claim_summary(claim: Claim) -> dict[str, Any]:
    return {
        "claim": claim.claim,
        "confidence": claim.confidence,
        "impact": claim.impact,
        "source_ids": claim.source_ids,
        "evidence": claim.evidence,
        "display_excerpt": claim.display_excerpt,
        "full_evidence_path": claim.full_evidence_path,
        "full_evidence_selector": claim.full_evidence_selector,
    }


def recommended_company_file_action(status: str, has_follow_up_urls: bool) -> str:
    if status == "ready_for_company_update":
        return "Update the company file developments/news section from the specialist review."
    if status == "partial_review":
        if has_follow_up_urls:
            return "Run Exa contents on the listed URLs before updating the company file developments/news section."
        return "Record that a news scan ran, but avoid changing the company thesis until better source detail is available."
    return "Do not update company conclusions until the news contradictions are reviewed."


def review_to_packet(
    ticker: str,
    news_path: Path,
    news_packet: EvidencePacket,
    review: dict[str, Any],
    raw_path: Path,
    report_path: Path,
    today: date,
) -> EvidencePacket:
    source_ids = dedupe_strings(
        [
            source["source_id"]
            for source in [*review["top_sources"], *review["contents_sources"]]
            if source.get("source_id")
        ]
    )
    packet_source_id = f"{ticker.lower()}_company_news_input_packet"
    report_source_id = f"{ticker.lower()}_company_news_specialist_report"
    internal_source_ids = [packet_source_id, report_source_id]
    evidence_source_ids = source_ids or internal_source_ids
    sources = [
        Source(
            source_id=packet_source_id,
            provider="company_news_specialist",
            source_type="internal",
            title=f"Exa news packet for {ticker}",
            publisher="exa",
            accessed_at=today.isoformat(),
            artifact_path=news_path.as_posix(),
            notes=f"Input packet {news_packet.packet_id}.",
        ),
        Source(
            source_id=report_source_id,
            provider="company_news_specialist",
            source_type="internal",
            title=f"Company news specialist review for {ticker}",
            publisher="company_news_specialist",
            accessed_at=today.isoformat(),
            artifact_path=report_path.as_posix(),
            notes="Generated deterministic specialist report.",
        ),
    ]
    sources.extend(review_sources_as_packet_sources([*review["top_sources"], *review["contents_sources"]], today))
    claim_summary_payload = {
        "status": review["status"],
        "status_reason": review["status_reason"],
        "source_count": review["source_count"],
        "claim_count": review["claim_count"],
        "contents_packet_count": review["contents_packet_count"],
        "contents_source_count": review["contents_source_count"],
        "top_sources": review["top_sources"],
        "contents_sources": review["contents_sources"],
        "contents_follow_up_urls": review["contents_follow_up_urls"],
        "contents_extracted_urls": review["contents_extracted_urls"],
        "remaining_content_follow_up_urls": review["remaining_content_follow_up_urls"],
    }
    claims = [
        Claim(
            claim=f"Company news specialist review completed for {ticker}.",
            evidence=json.dumps(claim_summary_payload, sort_keys=True),
            source_ids=evidence_source_ids,
            confidence="high" if review["status"] == "ready_for_company_update" else "medium",
            impact="medium",
            novelty="new",
        )
    ]
    risks = build_review_risks(review, evidence_source_ids)
    recommended_updates = [
        RecommendedUpdate(
            target_file="stock_tracking/stock_info_files/",
            update_type="company_file",
            summary=review["recommended_company_file_action"],
            needs_human_review=bool(review["needs_human_review"]),
            source_ids=evidence_source_ids,
        )
    ]
    if source_ids:
        claims.append(
            Claim(
                claim=f"Company news scan identified {len(source_ids)} top source(s) for {ticker}.",
                evidence=json.dumps(review["top_sources"][:5], sort_keys=True),
                source_ids=source_ids[:8],
                confidence="medium",
                impact="medium",
                novelty="new",
            )
        )

    return new_packet(
        provider="company_news_specialist",
        subject_type="company",
        subject_id=ticker,
        time_window="latest_company_news_review",
        current_date=today,
        sources=sources,
        claims=claims,
        risks=risks,
        recommended_updates=recommended_updates,
        unknowns=list(review["unknowns"]),
        raw_artifact_path=raw_path.as_posix(),
        notes="Deterministic company-news specialist synthesis built from an Exa company-news packet.",
    )


def review_sources_as_packet_sources(sources: list[dict[str, str]], today: date) -> list[Source]:
    packet_sources: list[Source] = []
    seen: set[str] = set()
    for source in sources:
        source_id = source.get("source_id", "").strip()
        if not source_id or source_id in seen:
            continue
        seen.add(source_id)
        packet_sources.append(
            Source(
                source_id=source_id,
                provider="exa",
                source_type="news",
                title=source.get("title", ""),
                publisher=source.get("publisher", ""),
                published_at=source.get("published_at", ""),
                accessed_at=today.isoformat(),
                url=source.get("url", ""),
            )
        )
    return packet_sources


def build_review_risks(review: dict[str, Any], source_ids: list[str]) -> list[Risk]:
    risks: list[Risk] = []
    if review["contradictions"]:
        risks.append(
            Risk(
                risk="Company-news packet contains contradictions requiring review.",
                evidence=json.dumps(review["contradictions"], sort_keys=True),
                source_ids=source_ids,
                severity="medium",
                time_horizon="current_review",
            )
        )
    if not review["source_count"]:
        risks.append(
            Risk(
                risk="Company-news scan returned no source results.",
                evidence="No Exa news sources were available in the packet.",
                source_ids=source_ids,
                severity="medium",
                time_horizon="current_review",
            )
        )
    if review["contents_follow_up_urls"] and not review["contents_source_count"]:
        risks.append(
            Risk(
                risk="News highlights need Exa contents extraction before company-file updates.",
                evidence=json.dumps(review["contents_follow_up_urls"][:5], sort_keys=True),
                source_ids=source_ids,
                severity="medium",
                time_horizon="current_review",
            )
        )
    elif review.get("remaining_content_follow_up_urls"):
        risks.append(
            Risk(
                risk="Some lower-priority news URLs were not extracted by Exa contents.",
                evidence=json.dumps(review["remaining_content_follow_up_urls"][:5], sort_keys=True),
                source_ids=source_ids,
                severity="low",
                time_horizon="current_review",
            )
        )
    return risks


def write_raw_review(root: Path, run_id: str, ticker: str, review: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "company_news_specialist"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_company_news_review.json"
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_markdown_review(root: Path, run_id: str, ticker: str, review: dict[str, Any]) -> Path:
    report_dir = root / "agents" / "runs" / run_id / "reports" / "company_news_specialist"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{ticker.upper()}_company_news_review.md"
    path.write_text(format_company_news_review_markdown(root, review), encoding="utf-8")
    return path


def format_company_news_review_markdown(root: Path, review: dict[str, Any]) -> str:
    lines = [
        f"# Company News Review: {review['ticker']}",
        "",
        f"Status: {review['status']}",
        f"Reason: {review['status_reason']}",
        "",
        "## Top Sources",
        "",
        "| Title | Publisher | Published | URL |",
        "| --- | --- | --- | --- |",
    ]
    if review["top_sources"]:
        for source in review["top_sources"]:
            lines.append(f"| {source['title'] or 'untitled'} | {source['publisher'] or 'unknown'} | {source['published_at'] or 'unknown'} | {source['url'] or 'internal'} |")
    else:
        lines.append("| none | none | none | none |")
    lines.extend(["", "## Material Claims", ""])
    if review["material_claims"]:
        for claim in review["material_claims"]:
            lines.append(f"- {claim['claim']} ({claim['confidence']}, {claim['impact']})")
    else:
        lines.append("- No material claims extracted from the Exa news packet.")
    lines.extend(["", "## Contents Follow-Up", ""])
    if review["contents_sources"]:
        lines.append("| Title | Publisher | Published | URL |")
        lines.append("| --- | --- | --- | --- |")
        for source in review["contents_sources"]:
            lines.append(f"| {source['title'] or 'untitled'} | {source['publisher'] or 'unknown'} | {source['published_at'] or 'unknown'} | {source['url'] or 'internal'} |")
    else:
        lines.append("- Exa contents follow-up has not been run for the listed URLs.")
    lines.extend(["", "## Contents Claims", ""])
    if review["contents_claims"]:
        for claim in review["contents_claims"]:
            lines.append(f"- {claim['claim']} ({claim['confidence']}, {claim['impact']})")
            if claim.get("evidence"):
                display_evidence = str(claim.get("display_excerpt") or "") or format_inline_evidence(str(claim["evidence"]))
                if display_evidence:
                    lines.append(f"  - Evidence: {display_evidence}")
                else:
                    lines.append("  - Evidence excerpt omitted because the selected source text is incomplete.")
                full_path = str(claim.get("full_evidence_path") or "").strip()
                if full_path and (display_evidence != str(claim["evidence"])):
                    selector = str(claim.get("full_evidence_selector") or "").strip()
                    suffix = f" ({selector})" if selector else ""
                    lines.append(f"  - Full evidence: `{full_path}`{suffix}")
    else:
        lines.append("- No Exa contents claims available.")
    lines.extend(["", "## Review Notes", ""])
    lines.append(f"- input evidence packet: `{relative_to_root(root, Path(review['exa_news_packet'])).as_posix()}`")
    lines.append(f"- input evidence packet id: `{review.get('exa_news_packet_id', 'unknown')}`")
    lines.append(f"- source_count: {review['source_count']}")
    lines.append(f"- claim_count: {review['claim_count']}")
    lines.append(f"- contents_packet_count: {review['contents_packet_count']}")
    lines.append(f"- contents_source_count: {review['contents_source_count']}")
    lines.append(f"- contents_claim_count: {review['contents_claim_count']}")
    lines.append(f"- contents_follow_up_urls: {', '.join(review['contents_follow_up_urls']) or 'none'}")
    lines.append(f"- contents_extracted_urls: {', '.join(review['contents_extracted_urls']) or 'none'}")
    lines.append(f"- remaining_content_follow_up_urls: {', '.join(review['remaining_content_follow_up_urls']) or 'none'}")
    lines.append(f"- unknowns: {len(review['unknowns'])}")
    lines.append(f"- contradictions: {len(review['contradictions'])}")
    lines.append(f"- recommended_company_file_action: {review['recommended_company_file_action']}")
    return "\n".join(lines).rstrip() + "\n"


def select_contents_follow_up_urls(packet: EvidencePacket, max_urls: int) -> list[str]:
    urls: list[str] = []
    for source in packet.sources:
        if not source.url:
            continue
        if source.url in urls:
            continue
        urls.append(source.url)
        if len(urls) >= max_urls:
            break
    return urls


def format_inline_evidence(value: str, max_length: int = 500) -> str:
    return compact_complete_text(value, max_length)
