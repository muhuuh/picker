from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import Claim, EvidencePacket, RecommendedUpdate, Risk, Source, default_packet_path, new_packet, read_packet, write_packet
from .memory import relative_to_root
from .repo import find_repo_root


class CompanyNewsSpecialistError(RuntimeError):
    pass


@dataclass(frozen=True)
class CompanyNewsReviewResult:
    packet: EvidencePacket
    paths: list[Path]
    review: dict[str, Any]


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
    review = build_company_news_review(ticker_upper, news_packet, news_path)

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


def build_company_news_review(ticker: str, news_packet: EvidencePacket, news_path: Path) -> dict[str, Any]:
    sources = news_sources(news_packet)
    material_claims = relevant_claims(news_packet)
    recent_sources = [source for source in sources if source.published_at]
    unknowns = list(news_packet.unknowns)
    contradictions = [contradiction.current_repo_claim for contradiction in news_packet.contradictions]
    top_urls = [source.url for source in sources[:5] if source.url]

    if contradictions:
        status = "needs_human_review"
        status_reason = "News packet contains contradictions that need review before company-file updates."
    elif not sources:
        status = "partial_review"
        status_reason = "Exa news returned no source results; keep this as a low-information scan."
    elif unknowns:
        status = "partial_review"
        status_reason = "News scan found sources but has unresolved unknowns."
    else:
        status = "ready_for_company_update"
        status_reason = "Company-news scan produced source-backed developments for review."

    return {
        "ticker": ticker,
        "status": status,
        "status_reason": status_reason,
        "exa_news_packet": news_path.as_posix(),
        "exa_news_packet_id": news_packet.packet_id,
        "source_count": len(sources),
        "recent_source_count": len(recent_sources),
        "claim_count": len(material_claims),
        "top_sources": [source_summary(source) for source in sources[:8]],
        "material_claims": [claim_summary(claim) for claim in material_claims[:8]],
        "contents_follow_up_urls": top_urls,
        "unknowns": unknowns,
        "contradictions": contradictions,
        "needs_human_review": status == "needs_human_review",
        "recommended_company_file_action": recommended_company_file_action(status, bool(top_urls)),
    }


def news_sources(packet: EvidencePacket) -> list[Source]:
    return [source for source in packet.sources if source.source_type == "news" or source.provider == "exa"]


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
    }


def recommended_company_file_action(status: str, has_follow_up_urls: bool) -> str:
    if status == "ready_for_company_update":
        if has_follow_up_urls:
            return "Update the company file developments/news section, and run Exa contents on the listed URLs before making deeper thesis changes."
        return "Update the company file developments/news section from the specialist review."
    if status == "partial_review":
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
    source_ids = [source["source_id"] for source in review["top_sources"]]
    sources = [
        Source(
            source_id="exa_news_packet",
            provider="company_news_specialist",
            source_type="internal",
            title=f"Exa news packet for {ticker}",
            publisher="exa",
            accessed_at=today.isoformat(),
            artifact_path=news_path.as_posix(),
            notes=f"Input packet {news_packet.packet_id}.",
        ),
        Source(
            source_id="company_news_specialist_report",
            provider="company_news_specialist",
            source_type="internal",
            title=f"Company news specialist review for {ticker}",
            publisher="company_news_specialist",
            accessed_at=today.isoformat(),
            artifact_path=report_path.as_posix(),
            notes="Generated deterministic specialist report.",
        ),
    ]
    claim_summary_payload = {
        "status": review["status"],
        "status_reason": review["status_reason"],
        "source_count": review["source_count"],
        "claim_count": review["claim_count"],
        "top_sources": review["top_sources"],
        "contents_follow_up_urls": review["contents_follow_up_urls"],
    }
    claims = [
        Claim(
            claim=f"Company news specialist review completed for {ticker}.",
            evidence=json.dumps(claim_summary_payload, sort_keys=True),
            source_ids=["exa_news_packet", "company_news_specialist_report"],
            confidence="high" if review["status"] == "ready_for_company_update" else "medium",
            impact="medium",
            novelty="new",
        )
    ]
    risks = build_review_risks(review, ["exa_news_packet", "company_news_specialist_report"])
    recommended_updates = [
        RecommendedUpdate(
            target_file="stock_tracking/stock_info_files/",
            update_type="company_file",
            summary=review["recommended_company_file_action"],
            needs_human_review=bool(review["needs_human_review"]),
            source_ids=["exa_news_packet", "company_news_specialist_report"],
        )
    ]
    if source_ids:
        claims.append(
            Claim(
                claim=f"Company news scan identified {len(source_ids)} top source(s) for {ticker}.",
                evidence=json.dumps(review["top_sources"][:5], sort_keys=True),
                source_ids=["exa_news_packet"],
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
    if review["contents_follow_up_urls"]:
        risks.append(
            Risk(
                risk="News highlights should be followed by Exa contents extraction before deeper thesis updates.",
                evidence=json.dumps(review["contents_follow_up_urls"][:5], sort_keys=True),
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
    lines.extend(["", "## Review Notes", ""])
    lines.append(f"- exa_news_packet: `{relative_to_root(root, Path(review['exa_news_packet'])).as_posix()}`")
    lines.append(f"- source_count: {review['source_count']}")
    lines.append(f"- claim_count: {review['claim_count']}")
    lines.append(f"- contents_follow_up_urls: {', '.join(review['contents_follow_up_urls']) or 'none'}")
    lines.append(f"- unknowns: {len(review['unknowns'])}")
    lines.append(f"- contradictions: {len(review['contradictions'])}")
    lines.append(f"- recommended_company_file_action: {review['recommended_company_file_action']}")
    return "\n".join(lines).rstrip() + "\n"
