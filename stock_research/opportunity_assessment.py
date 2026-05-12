from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import Claim, EvidencePacket, Risk, Source, default_packet_path, new_packet, read_packet, write_packet
from .memory import relative_to_root
from .repo import find_repo_root
from .report_formatting import format_financial_value, format_percent as format_ratio_percent, format_plain_value


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
    data_quality_notes = build_data_quality_notes(financial, news)

    assessment = {
        "ticker": ticker,
        "status": status,
        "opportunity_view": opportunity_view,
        "opportunity_score": score,
        "risk_level": risk_level,
        "confidence": confidence,
        "thesis_freshness": thesis_freshness,
        "summary": build_summary(ticker, opportunity_view, score, risk_level, confidence, positives, negatives, social),
        "financial_snapshot": financial,
        "news_snapshot": news,
        "social_snapshot": social,
        "filing_snapshot": filings,
        "positives": positives,
        "negatives": negatives,
        "watch_items": watch_items,
        "data_quality_notes": data_quality_notes,
        "score_factors": score_factors,
        "source_ids": source_ids,
        "provider_coverage": sorted(providers),
        "packet_count": len(packets),
        "recommended_next_action": recommended_next_action(opportunity_view, risk_level, confidence, financial, news, social, watch_items),
        "human_review_required": True,
    }
    assessment["quality_findings"] = validate_opportunity_assessment(assessment)
    return assessment


def validate_opportunity_assessment(assessment: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    ticker = str(assessment.get("ticker", "unknown"))
    providers = set(assessment.get("provider_coverage") or [])
    if "financial_data_specialist" not in providers:
        findings.append(f"{ticker} opportunity assessment is missing financial-data specialist evidence.")
    if "company_news_specialist" not in providers:
        findings.append(f"{ticker} opportunity assessment is missing company-news specialist evidence.")
    if not assessment.get("source_ids"):
        findings.append(f"{ticker} opportunity assessment has no source ids.")
    social = assessment.get("social_snapshot") or {}
    if social.get("status") == "available" and not str(social.get("sentiment", "")).endswith("_social_signal"):
        findings.append(f"{ticker} Grok/X signal must be labeled as social signal, not fact.")
    if social.get("status") == "available" and not social.get("x_pulse"):
        findings.append(f"{ticker} opportunity assessment is missing an actionable Grok/X pulse narrative.")
    if social.get("status") == "available" and not (social.get("bullish_claims") or social.get("bearish_claims")):
        findings.append(f"{ticker} opportunity assessment is missing concrete Grok/X bullish or bearish claims.")
    news = assessment.get("news_snapshot") or {}
    if news.get("status") != "missing" and not news.get("material_developments"):
        findings.append(f"{ticker} opportunity assessment is missing concrete source-backed news developments.")
    financial = assessment.get("financial_snapshot") or {}
    if financial.get("taxonomy_conflict_count") and not financial.get("material_conflict_count") and assessment.get("risk_level") == "high":
        findings.append(f"{ticker} taxonomy-only conflict should not create a high-risk opportunity assessment.")
    if contains_direct_trade_language(str(assessment.get("summary", ""))):
        findings.append(f"{ticker} opportunity summary contains direct trade language.")
    if contains_direct_trade_language(str(assessment.get("recommended_next_action", ""))):
        findings.append(f"{ticker} opportunity next action contains direct trade language.")
    return findings


def contains_direct_trade_language(value: str) -> bool:
    lower = value.lower()
    patterns = [
        r"\b(buy|sell|short)\s+(the\s+)?(stock|shares|position|ticker)\b",
        r"\b(stock|shares|position|ticker)\s+(is|are)\s+a\s+(buy|sell|short)\b",
        r"\b(go|going)\s+(long|short)\b",
        r"\b(add|increase|reduce|trim|exit)\s+(the\s+)?(stock|shares|position)\b",
        r"\b(position\s+size|position\s+sizing|size\s+the\s+position)\b",
    ]
    import re

    return any(re.search(pattern, lower) for pattern in patterns)


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
    material_developments = build_material_developments(review)
    return {
        "status": review.get("status", "missing"),
        "reason": review.get("status_reason", ""),
        "source_count": int(review.get("source_count") or 0),
        "contents_claim_count": int(review.get("contents_claim_count") or 0),
        "top_sources": list(review.get("top_sources") or [])[:5],
        "contents_claims": list(review.get("contents_claims") or [])[:5],
        "material_developments": material_developments[:6],
        "remaining_content_follow_up_count": len(review.get("remaining_content_follow_up_urls") or []),
        "remaining_content_follow_up_urls": list(review.get("remaining_content_follow_up_urls") or [])[:5],
        "unknown_count": len(review.get("unknowns") or []),
        "contradiction_count": len(review.get("contradictions") or []),
    }


def build_material_developments(review: dict[str, Any]) -> list[dict[str, Any]]:
    developments: list[dict[str, Any]] = []
    seen: set[str] = set()
    for claim in review.get("contents_claims", []) or []:
        if not isinstance(claim, dict):
            continue
        evidence = str(claim.get("evidence", ""))
        source_ids = list(claim.get("source_ids") or [])
        for item in extract_development_items(evidence):
            key = normalize_claim_key(item)
            if not key or key in seen:
                continue
            seen.add(key)
            developments.append({"claim": item, "source_ids": source_ids, "confidence": claim.get("confidence", "medium")})
            if len(developments) >= 8:
                return developments
    for claim in review.get("material_claims", []) or []:
        if not isinstance(claim, dict):
            continue
        evidence = str(claim.get("evidence", ""))
        source_ids = list(claim.get("source_ids") or [])
        for item in extract_development_items(evidence):
            key = normalize_claim_key(item)
            if not key or key in seen:
                continue
            seen.add(key)
            developments.append({"claim": item, "source_ids": source_ids, "confidence": claim.get("confidence", "medium")})
            if len(developments) >= 8:
                return developments
    return developments


def extract_development_items(evidence: str) -> list[str]:
    text = compact_text(evidence, 2500).replace("[...]", "\n")
    candidates: list[str] = []
    for line in text.splitlines():
        line = clean_report_text(line.strip(" -\t"))
        if not line:
            continue
        if not looks_investor_relevant(line):
            continue
        candidates.append(line)
    if candidates:
        return candidates[:6]
    sentences = re.split(r"(?<=[.!?])\s+", clean_report_text(text))
    return [sentence for sentence in sentences if looks_investor_relevant(sentence)][:6]


def looks_investor_relevant(value: str) -> bool:
    lower = value.lower()
    if len(value) < 35:
        return False
    keywords = (
        "revenue",
        "sales",
        "aws",
        "margin",
        "operating income",
        "income",
        "eps",
        "guidance",
        "growth",
        "capex",
        "capital expenditure",
        "backlog",
        "ai",
        "anthropic",
        "openai",
        "advertising",
        "transportation",
        "cost",
        "cash flow",
        "supply",
        "partnership",
        "customer",
        "launched",
        "contract",
    )
    return any(keyword in lower for keyword in keywords)


def summarize_social(packets: list[EvidencePacket]) -> dict[str, Any]:
    social_packets = [packet for packet in packets if packet.provider == "xai_grok"]
    raw_texts = [text for packet in social_packets if (text := read_xai_raw_output(packet.raw_artifact_path))]
    claims = raw_texts or [claim.evidence for packet in social_packets for claim in packet.claims]
    sources = [source for packet in social_packets for source in packet.sources]
    text = "\n".join(claims)
    lower = text.lower()
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
    sections = parse_grok_sections(text)
    rumors = section_items(sections, ["rumors or unverified claims"], limit=4)
    rumor_flag = bool(rumors) or (
        any(word in lower for word in ("rumor", "speculation", "speculative"))
        and "no major unverified rumors" not in lower
        and "no major rumors" not in lower
    )
    notable_accounts = extract_notable_accounts(text)
    return {
        "status": "available" if social_packets else "missing",
        "packet_count": len(social_packets),
        "citation_count": len([source for source in sources if source.url]),
        "sentiment": sentiment,
        "rumor_flag": rumor_flag,
        "hype_signal_count": hype_terms,
        "risk_signal_count": risk_terms,
        "x_pulse": first_non_empty_section(
            sections,
            [
                "executive x pulse",
                "community sentiment on x (as of mid-may 2026)",
                "recent x discussion on $amzn (early-to-mid may 2026) shows moderately bullish community sentiment",
                "social sentiment",
            ],
            fallback=first_paragraph(text),
        ),
        "verified_facts": section_items(sections, ["verified facts", "verified facts (from earnings/news reactions)"], limit=5),
        "bullish_claims": section_items(sections, ["recurring bullish claims", "bull case narratives"], limit=5),
        "bearish_claims": section_items(sections, ["recurring bearish/neutral claims", "recurring bearish claims", "recurring bearish or skeptical arguments", "bear/skeptic narratives"], limit=5),
        "news_reactions": section_items(sections, ["notable news people are reacting to"], limit=5),
        "notable_accounts": notable_accounts[:6],
        "hype_noise": first_non_empty_section(sections, ["hype / noise level", "hype/noise level", "hype/noise/spam level"], fallback=""),
        "rumors": rumors,
        "investor_implications": section_items(
            sections,
            [
                "concrete implications for an investor",
                "concrete implications for an investor (separate verified facts vs. sentiment vs. speculation)",
                "investor implications",
                "bottom-line investor takeaway",
            ],
            limit=5,
            fallback_paragraph=True,
        ),
        "summary_excerpt": compact_text(text, 1200),
    }


def read_xai_raw_output(path_value: str) -> str:
    if not path_value:
        return ""
    path = Path(path_value)
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    response = data.get("response", {}) if isinstance(data, dict) else {}
    parts: list[str] = []
    for item in response.get("output", []) if isinstance(response, dict) else []:
        if item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if content.get("type") == "output_text":
                parts.append(str(content.get("text", "")))
    return "\n\n".join(part for part in parts if part)


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
    if score < 45 or social.get("rumor_flag") or filings.get("status") == "missing":
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
    for development in news.get("material_developments", [])[:3]:
        claim_text = development.get("claim") if isinstance(development, dict) else ""
        if claim_text:
            positives.append(claim_text)
    for claim_text in social.get("bullish_claims", [])[:2]:
        positives.append(f"X bull narrative: {claim_text}")
    if financial.get("revenue_ttm") and numeric(financial.get("profit_margin")) and numeric(financial.get("profit_margin")) > 0:
        positives.append(
            f"Scale/profitability anchor: revenue TTM {format_financial_value('revenue_ttm', financial['revenue_ttm'])}, profit margin {format_percent(financial['profit_margin'])}."
        )
    if social.get("sentiment") == "positive_social_signal":
        positives.append("Grok/X scan found a positive social narrative, treated as sentiment evidence until verified.")
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
    for claim_text in social.get("bearish_claims", [])[:3]:
        negatives.append(f"X bear/skeptic narrative: {claim_text}")
    if numeric(financial.get("free_cash_flow_per_share_ttm")) and numeric(financial.get("free_cash_flow_per_share_ttm")) < 0:
        negatives.append(
            "Free cash flow per share TTM is negative at "
            f"{format_financial_value('free_cash_flow_per_share_ttm', financial['free_cash_flow_per_share_ttm'])}."
        )
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
    for implication in social.get("investor_implications", [])[:3]:
        items.append(implication)
    for rumor in social.get("rumors", [])[:2]:
        items.append(f"Verify X rumor/speculation: {rumor}")
    if news.get("remaining_content_follow_up_count"):
        urls = news.get("remaining_content_follow_up_urls", [])
        if urls:
            items.append(f"Extract remaining high-value Exa articles in next run, especially {urls[0]}.")
        else:
            items.append("Extract remaining high-value Exa articles in the next run.")
    if social.get("status") == "missing":
        items.append("Run Grok/X sentiment if social narrative matters for the next decision.")
    if filings.get("status") == "missing":
        items.append("Run or inspect SEC filing coverage for primary-source validation.")
    if not any(packet.provider == "exa" for packet in packets):
        items.append("Run Exa company/news search before treating the report as complete.")
    return items[:7] or ["No immediate blocking follow-up identified beyond routine thesis monitoring."]


def build_data_quality_notes(financial: dict[str, Any], news: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    if financial.get("taxonomy_conflict_count"):
        notes.append("Provider industry labels differ; keep this as internal classification hygiene, not an investment risk.")
    if financial.get("single_provider_metric_count"):
        notes.append("Some financial metrics are single-provider; use them as directional until cross-provider coverage improves.")
    if news.get("remaining_content_follow_up_count"):
        notes.append("Some Exa URLs remain unextracted; schedule contents follow-up as an internal run-quality task.")
    return notes


def build_summary(
    ticker: str,
    opportunity_view: str,
    score: int,
    risk_level: str,
    confidence: str,
    positives: list[str],
    negatives: list[str],
    social: dict[str, Any],
) -> str:
    pulse = social.get("x_pulse", "")
    pulse_sentence = f" X pulse: {compact_text(strip_citations_and_markdown(pulse), 220)}" if pulse else ""
    positive = compact_text(strip_citations_and_markdown(positives[0]), 180)
    negative = compact_text(strip_citations_and_markdown(negatives[0]), 180)
    return (
        f"{ticker} is {opportunity_view} ({score}/100, {risk_level} risk, {confidence} confidence) because {positive} "
        f"Main caveat: {negative}{pulse_sentence}"
    )


def unique_claim_texts(claims: list[Any], limit: int) -> list[str]:
    result: list[str] = []
    keys: list[str] = []
    for claim in claims:
        claim_text = claim.get("claim") if isinstance(claim, dict) else ""
        if not claim_text:
            continue
        key = normalize_claim_key(claim_text)
        if not key:
            continue
        if any(key in previous or previous in key for previous in keys):
            continue
        result.append(claim_text)
        keys.append(key)
        if len(result) >= limit:
            break
    return result


def normalize_claim_key(value: str) -> str:
    normalized = value.lower()
    normalized = normalized.removeprefix("exa content excerpt from ")
    normalized = re.sub(r"\b(inc|incorporated|corp|corporation|plc|ltd|limited)\b", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())


def recommended_next_action(
    opportunity_view: str,
    risk_level: str,
    confidence: str,
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    watch_items: list[str],
) -> str:
    if risk_level == "high" or confidence == "low":
        return "Review blocking evidence gaps before updating the company thesis."
    if social.get("bearish_claims") and social.get("bullish_claims"):
        bull = compact_text(strip_citations_and_markdown(str(social["bullish_claims"][0])), 130)
        bear = compact_text(strip_citations_and_markdown(str(social["bearish_claims"][0])), 130)
        return (
            "Next research decision: test whether the social bull case is fundamental or mostly momentum. "
            f"Verify the bull claim ({bull}) against filings/earnings and compare it with the main pushback ({bear})."
        )
    if news.get("material_developments"):
        return "Update the company thesis around the strongest source-backed development and verify whether it changes growth, margin, or valuation assumptions."
    if opportunity_view in {"interesting", "constructive_but_watch"}:
        return "Keep on the active review list and use the listed evidence checks to decide whether the thesis improved, weakened, or stayed unchanged."
    if watch_items:
        return "Resolve the listed research checks before making a stronger thesis judgment."
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
    lines.extend(["", "## Next Research Checks", ""])
    lines.extend(f"- {item}" for item in assessment["watch_items"])
    lines.extend(["", "## Financial Snapshot", ""])
    for key, value in assessment["financial_snapshot"].items():
        lines.append(f"- {key}: {format_financial_value(key, value)}")
    lines.extend(["", "## News And Developments", ""])
    news = assessment["news_snapshot"]
    developments = news.get("material_developments") or []
    if developments:
        for development in developments[:6]:
            claim_text = development.get("claim") if isinstance(development, dict) else str(development)
            source_ids = ", ".join(development.get("source_ids") or []) if isinstance(development, dict) else ""
            suffix = f" [{source_ids}]" if source_ids else ""
            lines.append(f"- {claim_text}{suffix}")
    else:
        lines.append("- No concrete source-backed development was extracted.")
    if news.get("remaining_content_follow_up_urls"):
        lines.append(
            "- Internal follow-up: remaining Exa URLs should be extracted in a later run, especially "
            f"{news['remaining_content_follow_up_urls'][0]}."
        )
    lines.extend(["", "## Grok/X Community And Sentiment", ""])
    social = assessment["social_snapshot"]
    lines.append(
        "- Evidence type: social/community signal from Grok/X; cite-backed but not treated as verified company fact "
        f"({social.get('citation_count')} citation(s), rumor_flag={social.get('rumor_flag')})."
    )
    if social.get("x_pulse"):
        lines.extend(["", "### X Pulse", "", social["x_pulse"]])
    if social.get("bullish_claims"):
        lines.extend(["", "### Recurring Bullish Claims", ""])
        lines.extend(f"- {item}" for item in social["bullish_claims"][:5])
    if social.get("bearish_claims"):
        lines.extend(["", "### Recurring Bearish / Skeptical Claims", ""])
        lines.extend(f"- {item}" for item in social["bearish_claims"][:5])
    if social.get("news_reactions"):
        lines.extend(["", "### News People Are Reacting To", ""])
        lines.extend(f"- {item}" for item in social["news_reactions"][:5])
    if social.get("notable_accounts"):
        lines.extend(["", "### Accounts / Posts Worth Reviewing", ""])
        lines.extend(f"- {item}" for item in social["notable_accounts"][:6])
    if social.get("hype_noise"):
        lines.extend(["", "### Hype / Noise", "", social["hype_noise"]])
    if social.get("rumors"):
        lines.extend(["", "### Rumors Or Unverified Claims", ""])
        lines.extend(f"- {item}" for item in social["rumors"][:4])
    if social.get("investor_implications"):
        lines.extend(["", "### Investor Implications From X", ""])
        lines.extend(f"- {item}" for item in social["investor_implications"][:5])
    lines.extend(["", "## Filing Signal", ""])
    filing = assessment["filing_snapshot"]
    lines.append(f"- status: {filing.get('status')}")
    lines.append(f"- packet_count: {filing.get('packet_count')}")
    for item in filing.get("recent_items", [])[:3]:
        lines.append(f"- item: {item}")
    lines.extend(["", "## Score Factors", ""])
    lines.extend(f"- {item}" for item in assessment["score_factors"])
    if assessment.get("data_quality_notes"):
        lines.extend(["", "## Internal Data Quality Notes", ""])
        lines.extend(f"- {item}" for item in assessment["data_quality_notes"])
    lines.extend(["", "## Sources", ""])
    for packet_id in assessment.get("source_ids", []):
        lines.append(f"- {packet_id}")
    lines.append(f"- run: `{relative_to_root(root, root / 'agents' / 'runs' / run_id).as_posix()}`")
    lines.extend(["", "## Quality Findings", ""])
    if assessment.get("quality_findings"):
        lines.extend(f"- {item}" for item in assessment["quality_findings"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Recommended Next Action", "", f"- {assessment['recommended_next_action']}"])
    return "\n".join(lines).rstrip() + "\n"


def compact_text(value: str, max_length: int) -> str:
    compact = " ".join(line.strip() for line in value.splitlines() if line.strip())
    compact = repair_latin1_mojibake(compact)
    compact = clean_report_text(compact)
    if len(compact) <= max_length:
        return compact
    truncated = compact[: max_length - 3].rstrip()
    if " " in truncated:
        truncated = truncated.rsplit(" ", 1)[0].rstrip()
    return truncated + "..."


def clean_report_text(value: str) -> str:
    replacements = {
        "\u201c": '"',
        "\u201d": '"',
        "\u2018": "'",
        "\u2019": "'",
        "\u2013": " - ",
        "\u2014": " - ",
        "\u2026": "...",
        "\u00a0": " ",
    }
    for bad, good in replacements.items():
        value = value.replace(bad, good)
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"\*(.*?)\*", r"\1", value)
    return " ".join(value.split())


def strip_citations_and_markdown(value: str) -> str:
    value = re.sub(r"\[\[\d+\]\]\([^)]+\)", "", value)
    value = re.sub(r"\[[^\]]+\]\([^)]+\)", "", value)
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"\*(.*?)\*", r"\1", value)
    return clean_report_text(value)


def parse_grok_sections(text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "overview"
    sections[current] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading, remainder = grok_heading(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
            if remainder:
                sections[current].append(remainder)
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(values).strip() for key, values in sections.items()}


def grok_heading(line: str) -> tuple[str, str]:
    value = line.strip().strip(":")
    if value.startswith("###"):
        value = value.lstrip("#").strip().strip(":")
        return normalize_heading(value), ""
    if value.startswith("**") and ("**" in value[2:]):
        end = value.find("**", 2)
        heading = value[2:end].strip().strip(":")
        if 2 <= len(heading.split()) <= 12:
            return normalize_heading(heading), value[end + 2 :].strip(" :")
    return "", ""


def normalize_heading(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def first_non_empty_section(sections: dict[str, str], names: list[str], fallback: str = "") -> str:
    normalized = {normalize_heading(key): value for key, value in sections.items()}
    for name in names:
        value = normalized.get(normalize_heading(name), "")
        if value:
            return compact_text(value, 650)
    if "overview" in normalized and normalized["overview"]:
        return compact_text(normalized["overview"], 650)
    return compact_text(fallback, 650) if fallback else ""


def section_items(
    sections: dict[str, str],
    names: list[str],
    limit: int,
    fallback_paragraph: bool = False,
) -> list[str]:
    normalized = {normalize_heading(key): value for key, value in sections.items()}
    for name in names:
        value = normalized.get(normalize_heading(name), "")
        if not value:
            continue
        items = filter_investor_items(bullet_or_sentence_items(value, limit=limit + 2), limit=limit)
        if items:
            return items
        if fallback_paragraph:
            return [compact_text(value, 450)]
    return []


def bullet_or_sentence_items(value: str, limit: int) -> list[str]:
    items: list[str] = []
    for raw_line in value.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = clean_report_text(line)
        if line:
            items.append(line)
        if len(items) >= limit:
            return items
    if items:
        return items[:limit]
    sentences = re.split(r"(?<=[.!?])\s+", clean_report_text(value))
    return [sentence for sentence in sentences if len(sentence) > 25][:limit]


def filter_investor_items(items: list[str], limit: int) -> list[str]:
    result: list[str] = []
    for item in items:
        if contains_direct_trade_language(item):
            continue
        result.append(item)
        if len(result) >= limit:
            break
    return result


def first_paragraph(text: str) -> str:
    for block in text.split("\n\n"):
        cleaned = clean_report_text(block.strip())
        if cleaned and not cleaned.startswith("###"):
            return cleaned
    return ""


def extract_notable_accounts(text: str) -> list[str]:
    accounts: list[str] = []
    for match in re.finditer(r"@[\w_]{2,20}", text):
        account = match.group(0)
        if account not in accounts:
            accounts.append(account)
    return accounts[:10]


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
    return format_plain_value(value)


def format_percent(value: Any) -> str:
    formatted = format_ratio_percent(value)
    return "unknown" if formatted == "None" else formatted
