from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import Claim, EvidencePacket, Risk, Source, default_packet_path, new_packet, read_packet, write_packet
from .memory import relative_to_root
from .repo import find_repo_root


class OpportunityAssessmentError(RuntimeError):
    pass


@dataclass(frozen=True)
class OpportunityAssessmentResult:
    packet: EvidencePacket
    paths: list[Path]
    assessment: dict[str, Any]


def build_opportunity_assessment_packet(
    ticker: str,
    run_id: str,
    root: Path | None,
    current_date: date | None = None,
) -> OpportunityAssessmentResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    ticker_upper = ticker.upper()
    packets = load_company_packets(repo_root, run_id, ticker_upper)
    if not packets:
        raise OpportunityAssessmentError(f"No evidence packets found for {ticker_upper} in run {run_id}.")

    assessment = build_opportunity_assessment(repo_root, run_id, ticker_upper, packets)
    raw_path = write_raw_assessment(repo_root, run_id, ticker_upper, assessment)
    report_path = write_markdown_assessment(repo_root, run_id, ticker_upper, assessment)
    packet = assessment_to_packet(ticker_upper, packets, assessment, raw_path, report_path, today)
    packet_path = default_packet_path(repo_root, run_id, packet)
    write_packet(packet, packet_path)
    return OpportunityAssessmentResult(packet=packet, paths=[packet_path, raw_path, report_path], assessment=assessment)


def load_company_packets(root: Path, run_id: str, ticker: str) -> list[EvidencePacket]:
    packet_dir = root / "agents" / "runs" / run_id / "evidence_packets"
    if not packet_dir.exists():
        return []
    packets: list[EvidencePacket] = []
    for path in sorted(packet_dir.glob("*.json")):
        try:
            packet = read_packet(path)
        except Exception:
            continue
        if packet.subject_type == "company" and packet.subject_id.upper() == ticker.upper():
            packets.append(packet)
    return packets


def build_opportunity_assessment(root: Path, run_id: str, ticker: str, packets: list[EvidencePacket]) -> dict[str, Any]:
    financial_review = read_run_json(root, run_id, "raw", "financial_data_specialist", f"{ticker}_financial_review.json")
    news_review = read_run_json(root, run_id, "raw", "company_news_specialist", f"{ticker}_company_news_review.json")
    providers = {packet.provider for packet in packets}
    financial = summarize_financials(financial_review)
    news = summarize_news(news_review)
    social = summarize_social(packets)
    filings = summarize_filings(packets)
    source_ids = selected_source_ids(packets)
    score, score_factors = score_opportunity(financial, news, social, filings, packets)
    risk_level = classify_risk(score, financial, news, social, filings, packets)
    opportunity_view = classify_opportunity(score, risk_level)
    thesis_freshness = classify_thesis_freshness(news, social, filings)
    confidence = classify_confidence(providers, financial, news, social, filings)
    status = "ready_for_human_review"
    if not financial_review and not news_review:
        status = "partial_review"
    if "financial_data_specialist" not in providers and "company_news_specialist" not in providers:
        status = "needs_more_evidence"

    positives = build_positives(financial, news, social, filings)
    negatives = build_negatives(financial, news, social, filings, packets)
    watch_items = build_watch_items(financial, news, social, filings, packets)

    return {
        "ticker": ticker,
        "status": status,
        "opportunity_view": opportunity_view,
        "opportunity_score": score,
        "risk_level": risk_level,
        "confidence": confidence,
        "thesis_freshness": thesis_freshness,
        "summary": build_summary(ticker, opportunity_view, score, risk_level, confidence, positives, negatives),
        "financial_snapshot": financial,
        "news_snapshot": news,
        "social_snapshot": social,
        "filing_snapshot": filings,
        "positives": positives,
        "negatives": negatives,
        "watch_items": watch_items,
        "score_factors": score_factors,
        "source_ids": source_ids,
        "provider_coverage": sorted(providers),
        "packet_count": len(packets),
        "recommended_next_action": recommended_next_action(opportunity_view, risk_level, confidence, watch_items),
        "human_review_required": True,
    }


def read_run_json(root: Path, run_id: str, *parts: str) -> dict[str, Any]:
    path = root / "agents" / "runs" / run_id
    for part in parts:
        path = path / part
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def summarize_financials(review: dict[str, Any]) -> dict[str, Any]:
    metrics = review.get("headline_metrics") or {}
    return {
        "status": review.get("status", "missing"),
        "reason": review.get("status_reason", ""),
        "latest_price": metric_value(metrics, "latest_price"),
        "market_cap": metric_value(metrics, "market_cap"),
        "pe_ratio": metric_value(metrics, "pe_ratio"),
        "price_to_sales_ttm": metric_value(metrics, "price_to_sales_ttm"),
        "ev_to_ebitda_ttm": metric_value(metrics, "ev_to_ebitda_ttm"),
        "revenue_ttm": metric_value(metrics, "revenue_ttm"),
        "profit_margin": metric_value(metrics, "profit_margin"),
        "free_cash_flow_per_share_ttm": metric_value(metrics, "free_cash_flow_per_share_ttm"),
        "currency": metric_value(metrics, "currency"),
        "sector": metric_value(metrics, "sector"),
        "industry": metric_value(metrics, "industry"),
        "conflict_count": len(review.get("conflicts") or []),
        "material_conflict_count": len(review.get("material_conflicts") or []),
        "taxonomy_conflict_count": len(review.get("taxonomy_conflicts") or []),
        "missing_core_metrics": list(review.get("missing_core_metrics") or []),
        "single_provider_metric_count": len(review.get("single_provider_metrics") or []),
    }


def metric_value(metrics: dict[str, Any], name: str) -> Any:
    item = metrics.get(name)
    if isinstance(item, dict):
        return item.get("value")
    return None


def summarize_news(review: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": review.get("status", "missing"),
        "reason": review.get("status_reason", ""),
        "source_count": int(review.get("source_count") or 0),
        "contents_claim_count": int(review.get("contents_claim_count") or 0),
        "top_sources": list(review.get("top_sources") or [])[:5],
        "contents_claims": list(review.get("contents_claims") or [])[:5],
        "remaining_content_follow_up_count": len(review.get("remaining_content_follow_up_urls") or []),
        "unknown_count": len(review.get("unknowns") or []),
        "contradiction_count": len(review.get("contradictions") or []),
    }


def summarize_social(packets: list[EvidencePacket]) -> dict[str, Any]:
    social_packets = [packet for packet in packets if packet.provider == "xai_grok"]
    claims = [claim.evidence for packet in social_packets for claim in packet.claims]
    sources = [source for packet in social_packets for source in packet.sources]
    text = "\n".join(claims)
    lower = text.lower()
    rumor_flag = any(word in lower for word in ("rumor", "unverified", "speculation", "speculative"))
    hype_terms = sum(lower.count(word) for word in ("hype", "viral", "enthusiasm", "bullish", "momentum"))
    risk_terms = sum(lower.count(word) for word in ("bearish", "concern", "risk", "worry", "slowdown"))
    if not social_packets:
        sentiment = "missing"
    elif hype_terms > risk_terms + 1:
        sentiment = "positive_social_signal"
    elif risk_terms > hype_terms + 1:
        sentiment = "negative_social_signal"
    else:
        sentiment = "mixed_social_signal"
    return {
        "status": "available" if social_packets else "missing",
        "packet_count": len(social_packets),
        "citation_count": len([source for source in sources if source.url]),
        "sentiment": sentiment,
        "rumor_flag": rumor_flag,
        "hype_signal_count": hype_terms,
        "risk_signal_count": risk_terms,
        "summary_excerpt": compact_text(text, 700),
    }


def summarize_filings(packets: list[EvidencePacket]) -> dict[str, Any]:
    filing_packets = [packet for packet in packets if packet.provider == "sec_edgar"]
    recent_forms: list[str] = []
    for packet in filing_packets:
        for claim in packet.claims[:5]:
            recent_forms.append(claim.claim)
    return {
        "status": "available" if filing_packets else "missing",
        "packet_count": len(filing_packets),
        "recent_items": recent_forms[:5],
        "unknown_count": sum(len(packet.unknowns) for packet in filing_packets),
    }


def selected_source_ids(packets: list[EvidencePacket]) -> list[str]:
    ids: list[str] = []
    for packet in packets:
        for source in packet.sources[:3]:
            if source.source_id not in ids:
                ids.append(source.source_id)
    return ids[:12]


def score_opportunity(
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    packets: list[EvidencePacket],
) -> tuple[int, list[str]]:
    score = 50
    factors: list[str] = []
    financial_status = str(financial.get("status", ""))
    if financial_status == "ready_for_company_update":
        score += 12
        factors.append("+12 financial review is ready with core metrics available.")
    elif financial_status == "partial_review":
        score += 5
        factors.append("+5 financial review is usable but incomplete.")
    elif financial_status == "needs_human_review":
        score -= 4
        factors.append("-4 financial review has conflicts or review gates.")
    if numeric(financial.get("profit_margin")) and numeric(financial.get("profit_margin")) > 0.08:
        score += 6
        factors.append("+6 profit margin is meaningfully positive.")
    if numeric(financial.get("pe_ratio")) and numeric(financial.get("pe_ratio")) > 45:
        score -= 8
        factors.append("-8 valuation multiple is high enough to require stronger growth support.")
    elif numeric(financial.get("pe_ratio")) and numeric(financial.get("pe_ratio")) <= 35:
        score += 3
        factors.append("+3 valuation multiple is not extreme for a large growth platform.")
    if str(news.get("status")) == "ready_for_company_update":
        score += 10
        factors.append("+10 recent news/contents review is source-backed.")
    if int(news.get("contents_claim_count") or 0) >= 3:
        score += 4
        factors.append("+4 Exa contents produced multiple material claims.")
    if social.get("sentiment") == "positive_social_signal":
        score += 4
        factors.append("+4 Grok/X social signal leans positive.")
    elif social.get("sentiment") == "negative_social_signal":
        score -= 4
        factors.append("-4 Grok/X social signal leans negative.")
    if social.get("rumor_flag"):
        score -= 3
        factors.append("-3 social signal includes rumor/speculation language.")
    if filings.get("status") == "available":
        score += 3
        factors.append("+3 SEC filing lane is available for primary-source cross-checks.")
    if int(financial.get("material_conflict_count") or 0):
        score -= 8
        factors.append("-8 at least one material financial contradiction remains unresolved.")
    elif int(financial.get("taxonomy_conflict_count") or 0):
        score -= 1
        factors.append("-1 provider taxonomy labels differ, but this is a watch item rather than a thesis blocker.")
    if not factors:
        factors.append("Neutral score: evidence coverage exists but did not trigger strong positive or negative factors.")
    return max(0, min(100, score)), factors


def numeric(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def classify_risk(
    score: int,
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    packets: list[EvidencePacket],
) -> str:
    if financial.get("material_conflict_count") or news.get("contradiction_count"):
        return "high"
    if score < 45 or social.get("rumor_flag") or filings.get("status") == "missing" or financial.get("taxonomy_conflict_count"):
        return "medium"
    return "low"


def classify_opportunity(score: int, risk_level: str) -> str:
    if score >= 70 and risk_level != "high":
        return "interesting"
    if score >= 58:
        return "constructive_but_watch"
    if score >= 45:
        return "neutral"
    return "weak_or_risky"


def classify_thesis_freshness(news: dict[str, Any], social: dict[str, Any], filings: dict[str, Any]) -> str:
    if news.get("contents_claim_count") or social.get("packet_count"):
        return "fresh_recent_evidence"
    if filings.get("status") == "available":
        return "primary_source_available_but_needs_news_context"
    return "stale_or_under_evidenced"


def classify_confidence(
    providers: set[str],
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
) -> str:
    required = {"financial_data_specialist", "company_news_specialist", "xai_grok", "sec_edgar"}
    if required.issubset(providers) and not financial.get("conflict_count") and news.get("contents_claim_count"):
        return "high"
    if {"financial_data_specialist", "company_news_specialist"}.issubset(providers):
        return "medium"
    return "low"


def build_positives(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any], filings: dict[str, Any]) -> list[str]:
    positives: list[str] = []
    if financial.get("revenue_ttm"):
        positives.append(f"Revenue TTM is available at {format_value(financial['revenue_ttm'])}, giving a scale anchor.")
    if numeric(financial.get("profit_margin")) and numeric(financial.get("profit_margin")) > 0:
        positives.append(f"Profit margin is positive at {format_percent(financial['profit_margin'])}.")
    for claim in news.get("contents_claims", [])[:3]:
        claim_text = claim.get("claim") if isinstance(claim, dict) else ""
        if claim_text:
            positives.append(f"Recent source-backed development: {claim_text}")
    if social.get("sentiment") == "positive_social_signal":
        positives.append("Grok/X scan found a positive social signal, treated as narrative evidence only.")
    if filings.get("status") == "available":
        positives.append("SEC filing lane is available for primary-source validation.")
    return positives[:6] or ["No strong positive signal was detected from the current evidence set."]


def build_negatives(
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    packets: list[EvidencePacket],
) -> list[str]:
    negatives: list[str] = []
    if financial.get("status") == "needs_human_review":
        negatives.append(f"Financial review needs human review: {financial.get('reason') or 'unresolved financial gate'}.")
    if financial.get("taxonomy_conflict_count"):
        negatives.append("Providers disagree on industry taxonomy; treat this as a classification/watch item, not a numeric conflict.")
    if numeric(financial.get("free_cash_flow_per_share_ttm")) and numeric(financial.get("free_cash_flow_per_share_ttm")) < 0:
        negatives.append(f"Free cash flow per share TTM is negative at {format_value(financial['free_cash_flow_per_share_ttm'])}.")
    if social.get("rumor_flag"):
        negatives.append("Grok/X scan includes rumor or speculation language; do not treat it as verified fact.")
    if filings.get("status") == "missing":
        negatives.append("SEC filing lane is missing, so primary-source filing coverage is incomplete.")
    contradiction_count = int(financial.get("material_conflict_count") or 0) + int(news.get("contradiction_count") or 0)
    if contradiction_count:
        negatives.append(f"{contradiction_count} contradiction(s) remain unresolved across evidence.")
    return negatives[:6] or ["No blocking negative signal was detected, but this is not an investment recommendation."]


def build_watch_items(
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    packets: list[EvidencePacket],
) -> list[str]:
    items: list[str] = []
    if financial.get("material_conflict_count"):
        items.append("Resolve material financial provider conflict before updating company-file conclusions.")
    if financial.get("taxonomy_conflict_count"):
        items.append("Pick the preferred industry taxonomy label for the company file.")
    if financial.get("single_provider_metric_count"):
        items.append("Treat single-provider financial metrics as lower-confidence until cross-checked.")
    if news.get("remaining_content_follow_up_count"):
        items.append("Run Exa contents follow-up for remaining high-value news URLs if they look material.")
    if social.get("status") == "missing":
        items.append("Run Grok/X sentiment if social narrative matters for the next decision.")
    if filings.get("status") == "missing":
        items.append("Run or inspect SEC filing coverage for primary-source validation.")
    if not any(packet.provider == "exa" for packet in packets):
        items.append("Run Exa company/news search before treating the report as complete.")
    return items[:7] or ["No immediate blocking follow-up identified."]


def build_summary(
    ticker: str,
    opportunity_view: str,
    score: int,
    risk_level: str,
    confidence: str,
    positives: list[str],
    negatives: list[str],
) -> str:
    return (
        f"{ticker} assessment is {opportunity_view} with score {score}/100, {risk_level} risk, and {confidence} confidence. "
        f"Main positive: {positives[0]} Main caution: {negatives[0]}"
    )


def recommended_next_action(
    opportunity_view: str,
    risk_level: str,
    confidence: str,
    watch_items: list[str],
) -> str:
    if risk_level == "high" or confidence == "low":
        return "Review blocking evidence gaps before updating the company thesis."
    if opportunity_view in {"interesting", "constructive_but_watch"}:
        return "Use this as a reviewable holding update and inspect watch items before changing the thesis."
    if watch_items:
        return "Keep monitoring and resolve the listed watch items before making a stronger judgment."
    return "No action beyond routine monitoring."


def assessment_to_packet(
    ticker: str,
    packets: list[EvidencePacket],
    assessment: dict[str, Any],
    raw_path: Path,
    report_path: Path,
    today: date,
) -> EvidencePacket:
    sources = [
        Source(
            source_id="opportunity_assessment_report",
            provider="opportunity_assessment_specialist",
            source_type="internal",
            title=f"Opportunity assessment for {ticker}",
            publisher="opportunity_assessment_specialist",
            accessed_at=today.isoformat(),
            artifact_path=report_path.as_posix(),
            notes="Deterministic expert-opinion assessment synthesized from run evidence.",
        )
    ]
    for packet in packets[:8]:
        sources.append(
            Source(
                source_id=f"packet_{packet.packet_id}",
                provider="opportunity_assessment_specialist",
                source_type="internal",
                title=f"{packet.provider} evidence packet for {ticker}",
                publisher=packet.provider,
                accessed_at=today.isoformat(),
                artifact_path=default_packet_path_from_packet(raw_path, packet).as_posix(),
                notes=f"Referenced input packet {packet.packet_id}.",
            )
        )
    source_ids = [source.source_id for source in sources]
    claims = [
        Claim(
            claim=f"Opportunity assessment completed for {ticker}.",
            evidence=json.dumps(
                {
                    "opportunity_view": assessment["opportunity_view"],
                    "opportunity_score": assessment["opportunity_score"],
                    "risk_level": assessment["risk_level"],
                    "confidence": assessment["confidence"],
                    "summary": assessment["summary"],
                },
                sort_keys=True,
            ),
            source_ids=source_ids,
            confidence=assessment["confidence"],
            impact="medium",
            novelty="new",
        )
    ]
    risks = [
        Risk(
            risk=f"Opportunity assessment risk level is {assessment['risk_level']}.",
            evidence=json.dumps(assessment["negatives"][:5], sort_keys=True),
            source_ids=source_ids,
            severity="medium" if assessment["risk_level"] == "medium" else assessment["risk_level"],
            time_horizon="current_review",
        )
    ]
    return new_packet(
        provider="opportunity_assessment_specialist",
        subject_type="company",
        subject_id=ticker,
        time_window="latest_opportunity_assessment",
        current_date=today,
        sources=sources,
        claims=claims,
        risks=risks,
        unknowns=list(assessment["watch_items"]),
        raw_artifact_path=raw_path.as_posix(),
        notes="This is a research-opinion artifact, not a trading instruction.",
    )


def default_packet_path_from_packet(raw_path: Path, packet: EvidencePacket) -> Path:
    run_dir = raw_path.parents[2]
    return run_dir / "evidence_packets" / f"{packet.packet_id}.json"


def write_raw_assessment(root: Path, run_id: str, ticker: str, assessment: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "opportunity_assessment"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_opportunity_assessment.json"
    path.write_text(json.dumps(assessment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_markdown_assessment(root: Path, run_id: str, ticker: str, assessment: dict[str, Any]) -> Path:
    report_dir = root / "agents" / "runs" / run_id / "reports" / "opportunity_assessment"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{ticker.upper()}_opportunity_assessment.md"
    path.write_text(format_opportunity_assessment_markdown(root, run_id, assessment), encoding="utf-8")
    return path


def format_opportunity_assessment_markdown(root: Path, run_id: str, assessment: dict[str, Any]) -> str:
    lines = [
        f"# Opportunity Assessment: {assessment['ticker']}",
        "",
        f"Status: {assessment['status']}",
        f"Opportunity view: {assessment['opportunity_view']}",
        f"Opportunity score: {assessment['opportunity_score']}/100",
        f"Risk level: {assessment['risk_level']}",
        f"Confidence: {assessment['confidence']}",
        f"Thesis freshness: {assessment['thesis_freshness']}",
        "",
        "## Expert Opinion",
        "",
        assessment["summary"],
        "",
        "This is a research synthesis for human review, not an automatic trade instruction.",
        "",
        "## Key Positives",
        "",
    ]
    lines.extend(f"- {item}" for item in assessment["positives"])
    lines.extend(["", "## Key Negatives / Risks", ""])
    lines.extend(f"- {item}" for item in assessment["negatives"])
    lines.extend(["", "## Watch Items", ""])
    lines.extend(f"- {item}" for item in assessment["watch_items"])
    lines.extend(["", "## Financial Snapshot", ""])
    for key, value in assessment["financial_snapshot"].items():
        lines.append(f"- {key}: {format_value(value)}")
    lines.extend(["", "## News And Developments", ""])
    news = assessment["news_snapshot"]
    lines.append(f"- status: {news.get('status')}")
    lines.append(f"- source_count: {news.get('source_count')}")
    lines.append(f"- contents_claim_count: {news.get('contents_claim_count')}")
    for claim in news.get("contents_claims", [])[:3]:
        if isinstance(claim, dict):
            lines.append(f"- claim: {claim.get('claim', '')}")
    lines.extend(["", "## Grok/X Social Signal", ""])
    social = assessment["social_snapshot"]
    lines.append(f"- status: {social.get('status')}")
    lines.append(f"- sentiment: {social.get('sentiment')}")
    lines.append(f"- citation_count: {social.get('citation_count')}")
    lines.append(f"- rumor_flag: {social.get('rumor_flag')}")
    if social.get("summary_excerpt"):
        lines.append(f"- excerpt: {social['summary_excerpt']}")
    lines.extend(["", "## Filing Signal", ""])
    filing = assessment["filing_snapshot"]
    lines.append(f"- status: {filing.get('status')}")
    lines.append(f"- packet_count: {filing.get('packet_count')}")
    for item in filing.get("recent_items", [])[:3]:
        lines.append(f"- item: {item}")
    lines.extend(["", "## Score Factors", ""])
    lines.extend(f"- {item}" for item in assessment["score_factors"])
    lines.extend(["", "## Sources", ""])
    for packet_id in assessment.get("source_ids", []):
        lines.append(f"- {packet_id}")
    lines.append(f"- run: `{relative_to_root(root, root / 'agents' / 'runs' / run_id).as_posix()}`")
    lines.extend(["", "## Recommended Next Action", "", f"- {assessment['recommended_next_action']}"])
    return "\n".join(lines).rstrip() + "\n"


def compact_text(value: str, max_length: int) -> str:
    compact = " ".join(line.strip() for line in value.splitlines() if line.strip())
    compact = repair_latin1_mojibake(compact)
    if len(compact) <= max_length:
        return compact
    return compact[: max_length - 3].rstrip() + "..."


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


def format_value(value: Any) -> str:
    if value is None:
        return "unknown"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)


def format_percent(value: Any) -> str:
    number = numeric(value)
    if number is None:
        return "unknown"
    return f"{number * 100:.2f}%"
