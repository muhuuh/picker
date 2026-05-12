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
    financial.update(enrich_financial_snapshot(root, run_id, ticker, financial))
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
    investor_insight = build_investor_insight_report(root, run_id, ticker, financial, news, social, filings, positives, negatives, watch_items)

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
        "investor_insight_report": investor_insight,
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
    insight = assessment.get("investor_insight_report") or {}
    if not insight.get("executive_read"):
        findings.append(f"{ticker} investor insight report is missing an executive read.")
    if not insight.get("non_obvious_insights"):
        findings.append(f"{ticker} investor insight report is missing non-obvious or under-discussed insights.")
    if not insight.get("valuation_snapshot", {}).get("forward_pe") and not insight.get("valuation_snapshot", {}).get("analyst_target_price"):
        findings.append(f"{ticker} investor insight report is missing forward valuation or analyst target context.")
    if not insight.get("peer_competition_context", {}).get("competitors"):
        findings.append(f"{ticker} investor insight report is missing peer/competition context.")
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


def enrich_financial_snapshot(root: Path, run_id: str, ticker: str, financial: dict[str, Any]) -> dict[str, Any]:
    alpha = read_run_json(root, run_id, "raw", "alpha_vantage", f"{ticker}_snapshot.json")
    fmp = read_run_json(root, run_id, "raw", "fmp", f"{ticker}_snapshot.json")
    overview = alpha.get("overview") if isinstance(alpha.get("overview"), dict) else {}
    quote = first_record(fmp.get("quote"))
    profile = first_record(fmp.get("profile"))
    ratios = first_record(fmp.get("ratios_ttm"))
    key_metrics = first_record(fmp.get("key_metrics_ttm"))
    target_price = to_number(overview.get("AnalystTargetPrice"))
    latest_price = numeric(financial.get("latest_price"))
    implied_upside = None
    if target_price is not None and latest_price:
        implied_upside = (target_price - latest_price) / latest_price
    return {
        "forward_pe": first_number(overview.get("ForwardPE"), ratios.get("forwardPriceToEarningsGrowthRatioTTM")),
        "peg_ratio": first_number(overview.get("PEGRatio"), ratios.get("priceToEarningsGrowthRatioTTM")),
        "analyst_target_price": target_price,
        "analyst_target_implied_upside": implied_upside,
        "analyst_rating_counts": {
            "strong_buy": to_int(overview.get("AnalystRatingStrongBuy")),
            "buy": to_int(overview.get("AnalystRatingBuy")),
            "hold": to_int(overview.get("AnalystRatingHold")),
            "sell": to_int(overview.get("AnalystRatingSell")),
            "strong_sell": to_int(overview.get("AnalystRatingStrongSell")),
        },
        "beta": first_number(overview.get("Beta"), profile.get("beta")),
        "fifty_two_week_high": first_number(overview.get("52WeekHigh"), quote.get("yearHigh")),
        "fifty_two_week_low": first_number(overview.get("52WeekLow"), quote.get("yearLow")),
        "price_to_book_ratio": first_number(overview.get("PriceToBookRatio"), ratios.get("priceToBookRatioTTM")),
        "quarterly_revenue_growth_yoy": to_number(overview.get("QuarterlyRevenueGrowthYOY")),
        "quarterly_earnings_growth_yoy": to_number(overview.get("QuarterlyEarningsGrowthYOY")),
        "operating_margin_ttm": first_number(overview.get("OperatingMarginTTM"), ratios.get("operatingProfitMarginTTM")),
        "return_on_equity_ttm": first_number(overview.get("ReturnOnEquityTTM"), key_metrics.get("returnOnEquityTTM")),
        "company_description": clean_report_text(str(overview.get("Description") or profile.get("description") or "")),
    }


def metric_value(metrics: dict[str, Any], name: str) -> Any:
    item = metrics.get(name)
    if isinstance(item, dict):
        return item.get("value")
    return None


def first_record(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value and isinstance(value[0], dict):
        return value[0]
    if isinstance(value, dict):
        return value
    return {}


def to_number(value: Any) -> float | None:
    if value in {None, "", "None"}:
        return None
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def first_number(*values: Any) -> float | None:
    for value in values:
        number = to_number(value)
        if number is not None:
            return number
    return None


def to_int(value: Any) -> int | None:
    number = to_number(value)
    return int(number) if number is not None else None


def summarize_news(review: dict[str, Any]) -> dict[str, Any]:
    material_developments = build_material_developments(review)
    return {
        "status": review.get("status", "missing"),
        "reason": review.get("status_reason", ""),
        "source_count": int(review.get("source_count") or 0),
        "contents_claim_count": int(review.get("contents_claim_count") or 0),
        "top_sources": list(review.get("top_sources") or [])[:5],
        "contents_claims": list(review.get("contents_claims") or [])[:5],
        "material_claims": list(review.get("material_claims") or [])[:6],
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
            if not key or is_duplicate_key(key, seen):
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
            if not key or is_duplicate_key(key, seen):
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
        if is_bad_truncated_excerpt(line):
            continue
        if not looks_investor_relevant(line):
            continue
        candidates.append(line)
    if candidates:
        return candidates[:6]
    sentences = re.split(r"(?<=[.!?])\s+", clean_report_text(text))
    return [sentence for sentence in sentences if looks_investor_relevant(sentence) and not is_bad_truncated_excerpt(sentence)][:6]


def is_bad_truncated_excerpt(value: str) -> bool:
    lower = value.lower()
    return bool(value.endswith("...") and any(fragment in lower for fragment in ("per diluted s", "per diluted sh", "the anthropic de", "substan")))


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


def build_investor_insight_report(
    root: Path,
    run_id: str,
    ticker: str,
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    positives: list[str],
    negatives: list[str],
    watch_items: list[str],
) -> dict[str, Any]:
    company_context = build_company_context(root, run_id, ticker, financial)
    valuation_snapshot = build_valuation_snapshot(financial)
    community = build_community_split(social)
    thesis = build_thesis_and_trends(financial, news, social, positives, negatives)
    non_obvious = build_non_obvious_insights(financial, news, social)
    table = build_summary_table(financial, news, social, filings, thesis, valuation_snapshot, non_obvious)
    return {
        "executive_read": build_executive_read(ticker, thesis, valuation_snapshot, community, non_obvious),
        "company_context": company_context,
        "thesis_and_trends": thesis,
        "community_and_expert_split": community,
        "non_obvious_insights": non_obvious,
        "valuation_snapshot": valuation_snapshot,
        "peer_competition_context": build_peer_competition_context(root, run_id, ticker, company_context),
        "decision_table": table,
        "next_research_questions": build_next_research_questions(financial, news, social, watch_items),
    }


def build_company_context(root: Path, run_id: str, ticker: str, financial: dict[str, Any]) -> dict[str, Any]:
    exa_context = read_exa_company_context(root, run_id, ticker)
    description = financial.get("company_description") or exa_context.get("description") or ""
    return {
        "what_it_does": compact_text(description, 700) if description else "Company description was not available from current provider artifacts.",
        "sector": financial.get("sector") or exa_context.get("industry") or "unknown",
        "industry": financial.get("industry") or exa_context.get("industry") or "unknown",
        "business_model_notes": extract_business_model_notes(description, exa_context.get("highlights", "")),
        "source": exa_context.get("source") or "financial provider profile",
    }


def build_valuation_snapshot(financial: dict[str, Any]) -> dict[str, Any]:
    latest = numeric(financial.get("latest_price"))
    low = numeric(financial.get("fifty_two_week_low"))
    high = numeric(financial.get("fifty_two_week_high"))
    range_position = None
    if latest is not None and low is not None and high is not None and high > low:
        range_position = (latest - low) / (high - low)
    return {
        "latest_price": financial.get("latest_price"),
        "market_cap": financial.get("market_cap"),
        "pe_ratio": financial.get("pe_ratio"),
        "forward_pe": financial.get("forward_pe"),
        "peg_ratio": financial.get("peg_ratio"),
        "price_to_sales_ttm": financial.get("price_to_sales_ttm"),
        "ev_to_ebitda_ttm": financial.get("ev_to_ebitda_ttm"),
        "analyst_target_price": financial.get("analyst_target_price"),
        "analyst_target_implied_upside": financial.get("analyst_target_implied_upside"),
        "analyst_rating_counts": financial.get("analyst_rating_counts") or {},
        "fifty_two_week_low": financial.get("fifty_two_week_low"),
        "fifty_two_week_high": financial.get("fifty_two_week_high"),
        "range_position": range_position,
        "beta": financial.get("beta"),
        "quarterly_revenue_growth_yoy": financial.get("quarterly_revenue_growth_yoy"),
        "quarterly_earnings_growth_yoy": financial.get("quarterly_earnings_growth_yoy"),
        "profit_margin": financial.get("profit_margin"),
        "operating_margin_ttm": financial.get("operating_margin_ttm"),
        "free_cash_flow_per_share_ttm": financial.get("free_cash_flow_per_share_ttm"),
    }


def build_community_split(social: dict[str, Any]) -> dict[str, Any]:
    return {
        "x_pulse": social.get("x_pulse", ""),
        "bullish_camp": list(social.get("bullish_claims") or [])[:5],
        "skeptical_camp": list(social.get("bearish_claims") or [])[:5],
        "notable_accounts_or_posts": list(social.get("notable_accounts") or [])[:8],
        "hype_noise_assessment": social.get("hype_noise", ""),
        "rumors_or_unverified": list(social.get("rumors") or [])[:4],
        "investor_implications": list(social.get("investor_implications") or [])[:5],
    }


def build_thesis_and_trends(
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    positives: list[str],
    negatives: list[str],
) -> dict[str, Any]:
    developments = [item.get("claim", "") for item in news.get("material_developments", []) if isinstance(item, dict) and item.get("claim")]
    return {
        "core_thesis": build_core_thesis(financial, news, social, positives),
        "what_changed_recently": developments[:6],
        "tailwinds": build_tailwinds(news, social, positives),
        "headwinds": build_headwinds(financial, news, social, negatives),
        "trend_evolution": build_trend_evolution(news, social),
    }


def build_core_thesis(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any], positives: list[str]) -> str:
    sector = financial.get("sector") or "the current sector"
    industry = financial.get("industry") or "its industry"
    first_positive = summarize_developments_short(news) or (strip_citations_and_markdown(positives[0]) if positives else "recent evidence is mixed")
    if social.get("bullish_claims"):
        return compact_text(f"{sector} / {industry}: {first_positive}. The social bull case centers on {strip_citations_and_markdown(str(social['bullish_claims'][0]))}.", 550)
    return compact_text(f"{sector} / {industry}: {first_positive}.", 550)


def build_tailwinds(news: dict[str, Any], social: dict[str, Any], positives: list[str]) -> list[str]:
    items: list[str] = []
    for value in positives:
        if any(word in value.lower() for word in ("growth", "aws", "ai", "margin", "sales", "revenue", "income", "backlog", "ads", "partnership")):
            items.append(value)
    items.extend(list(social.get("bullish_claims") or [])[:3])
    return unique_texts([strip_citations_and_markdown(item) for item in items], 6)


def build_headwinds(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any], negatives: list[str]) -> list[str]:
    items = [strip_citations_and_markdown(item) for item in negatives]
    for claim in news.get("contents_claims", []) + news.get("material_claims", []):
        evidence = str(claim.get("evidence", "")) if isinstance(claim, dict) else ""
        for line in extract_development_items(evidence):
            if any(word in line.lower() for word in ("cost", "constraint", "pressure", "capex", "cash flow", "volatility", "headwind")):
                items.append(line)
    if numeric(financial.get("free_cash_flow_per_share_ttm")) and numeric(financial.get("free_cash_flow_per_share_ttm")) < 0:
        items.append(f"Free cash flow per share TTM is negative ({format_financial_value('free_cash_flow_per_share_ttm', financial['free_cash_flow_per_share_ttm'])}), likely requiring a capex/cash-conversion follow-up.")
    return unique_texts(items, 6)


def build_trend_evolution(news: dict[str, Any], social: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for development in news.get("material_developments", []):
        claim = development.get("claim", "") if isinstance(development, dict) else ""
        if any(word in claim.lower() for word in ("increased", "accelerated", "growth", "guidance", "margin", "operating income")):
            items.append(f"Fundamental trend: {claim}")
    if social.get("x_pulse"):
        items.append(f"Social trend: {strip_citations_and_markdown(str(social['x_pulse']))}")
    return unique_texts(items, 5)


def build_non_obvious_insights(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for claim in news.get("contents_claims", []) + news.get("material_claims", []):
        evidence = str(claim.get("evidence", "")) if isinstance(claim, dict) else ""
        for line in extract_development_items(evidence):
            lower = line.lower()
            if any(word in lower for word in ("custom silicon", "memory", "leo", "backlog", "advertising", "ads", "transportation", "capex", "partner", "anthropic", "openai", "ai revenue run rate", "bedrock")):
                candidates.append(line)
    for implication in social.get("investor_implications", [])[:3]:
        candidates.append(f"X implication to verify: {strip_citations_and_markdown(str(implication))}")
    if numeric(financial.get("analyst_target_implied_upside")) is not None:
        candidates.append(
            f"Analyst target context implies {format_percent(financial['analyst_target_implied_upside'])} upside/downside versus the latest provider price; compare this with the X narrative before assuming consensus is already fully priced."
        )
    return unique_texts(candidates, 7)


def build_peer_competition_context(root: Path, run_id: str, ticker: str, company_context: dict[str, Any]) -> dict[str, Any]:
    exa_context = read_exa_company_context(root, run_id, ticker)
    competitors = exa_context.get("competitors") or []
    return {
        "competitors": competitors[:12],
        "positioning_note": build_positioning_note(company_context, competitors),
        "source": exa_context.get("source", ""),
    }


def build_positioning_note(company_context: dict[str, Any], competitors: list[str]) -> str:
    industry = company_context.get("industry") or "its market"
    if competitors:
        return f"Positioning should be assessed against {', '.join(competitors[:5])} in {industry}; current evidence is not yet a full peer valuation comparison."
    return f"Peer list was not reliably extracted; compare valuation and growth against the closest public peers in {industry} before making a stronger conclusion."


def build_summary_table(
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    thesis: dict[str, Any],
    valuation: dict[str, Any],
    non_obvious: list[str],
) -> list[dict[str, str]]:
    return [
        {
            "dimension": "Growth / demand",
            "current_read": compact_text(first_or_default(thesis.get("tailwinds"), "No clear growth tailwind extracted."), 160),
            "evidence": "Exa news + earnings/call excerpts",
            "follow_up": "Check whether growth is broad-based or mostly one segment.",
        },
        {
            "dimension": "Community / X sentiment",
            "current_read": compact_text(strip_citations_and_markdown(str(social.get("x_pulse", "No X pulse available."))), 160),
            "evidence": "Grok/X social signal",
            "follow_up": "Separate informed accounts from price-action chatter and spam.",
        },
        {
            "dimension": "Valuation",
            "current_read": valuation_sentence(valuation),
            "evidence": "Financial providers / Alpha Vantage / FMP",
            "follow_up": "Compare multiples and analyst target with growth durability.",
        },
        {
            "dimension": "Non-obvious angle",
            "current_read": compact_text(first_or_default(non_obvious, "No non-obvious angle extracted."), 160),
            "evidence": "Cross-read of Exa, Grok/X, and financials",
            "follow_up": "Verify with primary source or higher-quality source before thesis update.",
        },
        {
            "dimension": "Primary-source coverage",
            "current_read": f"Filings lane: {filings.get('status', 'missing')}; news sources: {news.get('source_count', 0)}.",
            "evidence": "SEC/Exa packets",
            "follow_up": "Use filings for claims that affect valuation or risk.",
        },
    ]


def build_next_research_questions(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any], watch_items: list[str]) -> list[str]:
    questions: list[str] = []
    if social.get("bullish_claims") and social.get("bearish_claims"):
        questions.append("Is the X bull case supported by reported fundamentals, or is it mainly momentum around the ticker?")
    if numeric(financial.get("analyst_target_implied_upside")) is not None:
        questions.append("Does the analyst target upside still leave enough margin after factoring in valuation, capex, and macro risk?")
    if any("ads" in str(item).lower() or "aws" in str(item).lower() for item in news.get("material_claims", [])):
        questions.append("Do AWS AI adoption, Amazon Ads growth, and capex pressure change the medium-term margin thesis enough to update the company file?")
    if social.get("rumors"):
        questions.append("Which X claims are rumor/speculation and which can be verified through company sources or high-quality reporting?")
    if financial.get("material_conflict_count"):
        questions.append("Which financial provider conflict changes the investment thesis rather than only the metadata?")
    return unique_texts(questions, 6)


def build_executive_read(ticker: str, thesis: dict[str, Any], valuation: dict[str, Any], community: dict[str, Any], non_obvious: list[str]) -> str:
    thesis_text = compact_text(strip_citations_and_markdown(str(thesis.get("core_thesis") or "Evidence is incomplete.")), 220)
    valuation_text = valuation_sentence(valuation)
    community_text = compact_text(first_sentence(strip_citations_and_markdown(str(community.get("x_pulse", "")))), 300)
    non_obvious_text = compact_text(first_or_default(non_obvious, "No strong non-obvious angle was extracted."), 220)
    return compact_text(
        f"{ticker}: {thesis_text} Valuation: {valuation_text}. X/community: {community_text}. Under-discussed check: {non_obvious_text}",
        860,
    )


def summarize_developments_short(news: dict[str, Any]) -> str:
    developments = [item.get("claim", "") for item in news.get("material_developments", []) if isinstance(item, dict)]
    if not developments:
        return ""
    revenue = metric_phrase(first_matching(developments, ("net sales", "revenue")), "revenue")
    aws = metric_phrase(first_matching(developments, ("aws",)), "aws")
    income = metric_phrase(first_matching(developments, ("operating income", "margin")), "income")
    parts = [value for value in (revenue, aws, income) if value]
    return " ".join(unique_texts(parts, 3))


def metric_phrase(value: str, kind: str) -> str:
    if not value:
        return ""
    if kind == "revenue":
        match = re.search(r"net sales increased\s+([\d.]+%)\s+to\s+\$([\d.]+)\s+billion", value, flags=re.IGNORECASE)
        if match:
            return f"net sales +{match.group(1)} to ${match.group(2)}B"
    if kind == "aws":
        match = re.search(r"aws segment sales increased\s+([\d.]+%)\s+year-over-year to\s+\$([\d.]+)\s+billion", value, flags=re.IGNORECASE)
        if match:
            return f"AWS sales +{match.group(1)} YoY to ${match.group(2)}B"
    if kind == "income":
        match = re.search(r"operating income increased to\s+\$([\d.]+)\s+billion.*compared with\s+\$([\d.]+)\s+billion", value, flags=re.IGNORECASE)
        if match:
            return f"operating income ${match.group(1)}B vs ${match.group(2)}B"
    return compact_text(value, 130)


def first_matching(values: list[str], keywords: tuple[str, ...]) -> str:
    for value in values:
        lower = value.lower()
        if any(keyword in lower for keyword in keywords):
            return value
    return ""


def first_sentence(value: str) -> str:
    cleaned = clean_report_text(value)
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    return sentences[0] if sentences and sentences[0] else cleaned


def valuation_sentence(valuation: dict[str, Any]) -> str:
    parts = [
        f"price {format_financial_value('latest_price', valuation.get('latest_price'))}",
        f"P/E {format_financial_value('pe_ratio', valuation.get('pe_ratio'))}",
    ]
    if valuation.get("forward_pe") is not None:
        parts.append(f"forward P/E {format_financial_value('pe_ratio', valuation.get('forward_pe'))}")
    if valuation.get("analyst_target_price") is not None:
        parts.append(f"analyst target {format_financial_value('latest_price', valuation.get('analyst_target_price'))}")
    if valuation.get("analyst_target_implied_upside") is not None:
        parts.append(f"target gap {format_percent(valuation.get('analyst_target_implied_upside'))}")
    return ", ".join(parts)


def read_exa_company_context(root: Path, run_id: str, ticker: str) -> dict[str, Any]:
    data = read_run_json(root, run_id, "raw", "exa", f"exa_company_search_company_{ticker.lower()}.json")
    results = ((data.get("response") or {}).get("results") or []) if isinstance(data, dict) else []
    if not results:
        return {}
    primary = results[0] if isinstance(results[0], dict) else {}
    highlight_text = "\n".join(str(item) for item in primary.get("highlights", []) if item)
    entity = first_record(primary.get("entities"))
    properties = entity.get("properties") if isinstance(entity.get("properties"), dict) else {}
    description = properties.get("description") or first_paragraph(highlight_text)
    return {
        "description": clean_report_text(str(description or "")),
        "highlights": highlight_text,
        "industry": extract_after_label(highlight_text, "Industry"),
        "competitors": extract_competitors(highlight_text),
        "source": str(primary.get("url", "")),
    }


def extract_business_model_notes(description: str, highlights: str) -> list[str]:
    text = f"{description}\n{highlights}"
    notes: list[str] = []
    for keyword in ("AWS", "advertising", "retail", "marketplace", "Prime", "AI", "fulfillment", "cloud", "subscription"):
        if keyword.lower() in text.lower():
            notes.append(keyword)
    return notes[:8]


def extract_after_label(text: str, label: str) -> str:
    match = re.search(rf"-\s*{re.escape(label)}:\s*([^\n]+)", text, flags=re.IGNORECASE)
    return clean_report_text(match.group(1)) if match else ""


def extract_competitors(text: str) -> list[str]:
    marker = re.search(r"##\s*Competitors(?P<body>.*?)(?:\n\s*##|\Z)", text, flags=re.IGNORECASE | re.DOTALL)
    body = marker.group("body") if marker else ""
    if not body:
        return []
    body = body.replace("[...]", " ")
    raw_items = re.split(r",|\n|-", body)
    competitors: list[str] = []
    for raw in raw_items:
        item = clean_report_text(raw).strip(" .:").lower()
        if not item or len(item) < 3 or len(item) > 45:
            continue
        if any(skip in item.lower() for skip in ("competitors", "categories", "products", "tech stack")):
            continue
        if item not in {value.lower() for value in competitors}:
            competitors.append(item)
        if len(competitors) >= 60:
            break
    return rank_competitors(competitors)


def rank_competitors(competitors: list[str]) -> list[str]:
    preferred = [
        "walmart",
        "alibaba group",
        "temu",
        "shein",
        "microsoft",
        "google",
        "apple",
        "target",
        "ebay",
        "rakuten",
        "costco",
        "oracle",
        "salesforce",
        "adobe",
        "meta",
        "facebook",
    ]
    noisy = {"ralali", "cafepress", "jcpenney", "walgreens", "macy's", "kmart", "snapdeal", "overstock"}
    ranked = [item for item in preferred if item in competitors]
    ranked.extend(item for item in competitors if item not in ranked and item not in noisy)
    return [title_case_company(item) for item in ranked[:12]]


def title_case_company(value: str) -> str:
    known = {
        "ebay": "eBay",
        "temu": "Temu",
        "shein": "Shein",
        "walmart": "Walmart",
        "google": "Google",
        "microsoft": "Microsoft",
        "apple": "Apple",
        "target": "Target",
        "costco": "Costco",
        "meta": "Meta",
        "facebook": "Facebook",
    }
    return known.get(value.lower(), value.title())


def first_or_default(values: Any, default: str) -> str:
    if isinstance(values, list):
        for value in values:
            if value:
                return str(value)
    return default


def unique_texts(values: list[str], limit: int) -> list[str]:
    result: list[str] = []
    keys: set[str] = set()
    for value in values:
        cleaned = clean_report_text(strip_citations_and_markdown(str(value)))
        if not cleaned:
            continue
        key = normalize_claim_key(cleaned)
        if not key or is_duplicate_key(key, keys):
            continue
        keys.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def is_duplicate_key(key: str, existing: set[str]) -> bool:
    compact = key[:140]
    for previous in existing:
        previous_compact = previous[:140]
        if compact == previous_compact or compact in previous or previous_compact in key:
            return True
    return False


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
        "## Investor Insight Report",
        "",
    ]
    insight = assessment.get("investor_insight_report") or {}
    lines.extend(format_investor_insight_markdown(insight))
    lines.extend(
        [
            "",
            "## Key Positives",
            "",
        ]
    )
    lines.extend(f"- {format_report_item(item)}" for item in assessment["positives"])
    lines.extend(["", "## Key Negatives / Risks", ""])
    lines.extend(f"- {format_report_item(item)}" for item in assessment["negatives"])
    lines.extend(["", "## Next Research Checks", ""])
    lines.extend(f"- {format_report_item(item)}" for item in assessment["watch_items"])
    lines.extend(["", "## Financial Snapshot", ""])
    lines.extend(format_financial_snapshot_lines(assessment["financial_snapshot"]))
    lines.extend(["", "## News And Developments", ""])
    news = assessment["news_snapshot"]
    developments = news.get("material_developments") or []
    if developments:
        for development in developments[:6]:
            claim_text = development.get("claim") if isinstance(development, dict) else str(development)
            source_ids = ", ".join(development.get("source_ids") or []) if isinstance(development, dict) else ""
            suffix = f" [{source_ids}]" if source_ids else ""
            lines.append(f"- {format_report_item(claim_text, 420)}{suffix}")
    else:
        lines.append("- No concrete source-backed development was extracted.")
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
        lines.extend(f"- {format_report_item(item)}" for item in social["bullish_claims"][:5])
    if social.get("bearish_claims"):
        lines.extend(["", "### Recurring Bearish / Skeptical Claims", ""])
        lines.extend(f"- {format_report_item(item)}" for item in social["bearish_claims"][:5])
    if social.get("news_reactions"):
        lines.extend(["", "### News People Are Reacting To", ""])
        lines.extend(f"- {format_report_item(item)}" for item in social["news_reactions"][:5])
    if social.get("notable_accounts"):
        lines.extend(["", "### Accounts / Posts Worth Reviewing", ""])
        lines.extend(f"- {item}" for item in social["notable_accounts"][:6])
    if social.get("hype_noise"):
        lines.extend(["", "### Hype / Noise", "", social["hype_noise"]])
    if social.get("rumors"):
        lines.extend(["", "### Rumors Or Unverified Claims", ""])
        lines.extend(f"- {format_report_item(item)}" for item in social["rumors"][:4])
    if social.get("investor_implications"):
        lines.extend(["", "### Investor Implications From X", ""])
        lines.extend(f"- {format_report_item(item)}" for item in social["investor_implications"][:5])
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


def format_investor_insight_markdown(insight: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    lines.extend(["### Executive Read", "", insight.get("executive_read") or "No executive read generated.", ""])
    context = insight.get("company_context") or {}
    lines.extend(
        [
            "### Company / Industry Context",
            "",
            f"- What it does: {context.get('what_it_does') or 'unknown'}",
            f"- Sector / industry: {context.get('sector') or 'unknown'} / {context.get('industry') or 'unknown'}",
        ]
    )
    notes = context.get("business_model_notes") or []
    if notes:
        lines.append(f"- Business model signals: {', '.join(notes)}")
    peer = insight.get("peer_competition_context") or {}
    competitors = peer.get("competitors") or []
    if competitors:
        lines.append(f"- Peer/competition set to check: {', '.join(competitors[:10])}")
    if peer.get("positioning_note"):
        lines.append(f"- Positioning note: {peer['positioning_note']}")

    thesis = insight.get("thesis_and_trends") or {}
    lines.extend(["", "### Thesis, Trends, And What Changed", ""])
    lines.append(f"- Core thesis: {thesis.get('core_thesis') or 'No core thesis generated.'}")
    append_list_section(lines, "What changed recently", thesis.get("what_changed_recently") or [])
    append_list_section(lines, "Tailwinds", thesis.get("tailwinds") or [])
    append_list_section(lines, "Headwinds / debate points", thesis.get("headwinds") or [])
    append_list_section(lines, "Trend evolution", thesis.get("trend_evolution") or [])

    community = insight.get("community_and_expert_split") or {}
    lines.extend(["", "### Expert / Community Split From X", ""])
    lines.append(f"- X pulse: {community.get('x_pulse') or 'No X pulse available.'}")
    append_list_section(lines, "Bullish camp", community.get("bullish_camp") or [])
    append_list_section(lines, "Skeptical camp", community.get("skeptical_camp") or [])
    if community.get("notable_accounts_or_posts"):
        lines.append(f"- Accounts/posts worth reviewing: {', '.join(community['notable_accounts_or_posts'][:8])}")
    if community.get("hype_noise_assessment"):
        lines.append(f"- Hype/noise: {community['hype_noise_assessment']}")
    append_list_section(lines, "Rumors / unverified claims", community.get("rumors_or_unverified") or [])

    append_list_section(lines, "Non-obvious / under-discussed insights to verify", insight.get("non_obvious_insights") or [], heading_level="###")

    valuation = insight.get("valuation_snapshot") or {}
    lines.extend(["", "### Valuation And Analyst Snapshot", ""])
    valuation_rows = [
        ("Latest price", "latest_price"),
        ("Market cap", "market_cap"),
        ("P/E", "pe_ratio"),
        ("Forward P/E", "forward_pe"),
        ("PEG", "peg_ratio"),
        ("P/S TTM", "price_to_sales_ttm"),
        ("EV/EBITDA TTM", "ev_to_ebitda_ttm"),
        ("Analyst target", "analyst_target_price"),
        ("Target gap", "analyst_target_implied_upside"),
        ("52-week low/high", "fifty_two_week_low"),
        ("Beta", "beta"),
        ("Quarterly revenue growth YoY", "quarterly_revenue_growth_yoy"),
        ("Quarterly earnings growth YoY", "quarterly_earnings_growth_yoy"),
        ("Profit margin", "profit_margin"),
        ("Operating margin TTM", "operating_margin_ttm"),
        ("FCF/share TTM", "free_cash_flow_per_share_ttm"),
    ]
    for label, key in valuation_rows:
        if key == "fifty_two_week_low":
            low = format_financial_value("latest_price", valuation.get("fifty_two_week_low"))
            high = format_financial_value("latest_price", valuation.get("fifty_two_week_high"))
            lines.append(f"- {label}: {low} / {high}")
        elif key == "analyst_target_implied_upside":
            lines.append(f"- {label}: {format_percent(valuation.get(key)) if valuation.get(key) is not None else 'unknown'}")
        elif key in {"quarterly_revenue_growth_yoy", "quarterly_earnings_growth_yoy", "profit_margin", "operating_margin_ttm"}:
            lines.append(f"- {label}: {format_percent(valuation.get(key)) if valuation.get(key) is not None else 'unknown'}")
        else:
            lines.append(f"- {label}: {format_financial_value(key, valuation.get(key))}")
    ratings = valuation.get("analyst_rating_counts") or {}
    if ratings:
        rating_text = ", ".join(f"{key.replace('_', ' ')} {value}" for key, value in ratings.items() if value is not None)
        if rating_text:
            lines.append(f"- Analyst rating count: {rating_text}")

    table = insight.get("decision_table") or []
    if table:
        lines.extend(["", "### Decision Table", "", "| Dimension | Current read | Evidence | Follow-up |", "| --- | --- | --- | --- |"])
        for row in table:
            lines.append(
                "| "
                + " | ".join(
                    escape_table_cell(str(row.get(column, ""))) for column in ("dimension", "current_read", "evidence", "follow_up")
                )
                + " |"
            )
    append_list_section(lines, "Next research questions", insight.get("next_research_questions") or [], heading_level="###")
    return lines


def format_financial_snapshot_lines(financial: dict[str, Any]) -> list[str]:
    ordered_keys = [
        "status",
        "reason",
        "latest_price",
        "market_cap",
        "pe_ratio",
        "forward_pe",
        "peg_ratio",
        "analyst_target_price",
        "analyst_target_implied_upside",
        "price_to_sales_ttm",
        "ev_to_ebitda_ttm",
        "revenue_ttm",
        "profit_margin",
        "operating_margin_ttm",
        "free_cash_flow_per_share_ttm",
        "currency",
        "sector",
        "industry",
        "fifty_two_week_low",
        "fifty_two_week_high",
        "quarterly_revenue_growth_yoy",
        "quarterly_earnings_growth_yoy",
        "material_conflict_count",
        "taxonomy_conflict_count",
    ]
    lines: list[str] = []
    for key in ordered_keys:
        if key not in financial:
            continue
        value = financial.get(key)
        if key == "reason":
            lines.append(f"- {key}: {value or 'none'}")
        elif key in {"quarterly_revenue_growth_yoy", "quarterly_earnings_growth_yoy", "operating_margin_ttm", "analyst_target_implied_upside"}:
            lines.append(f"- {key}: {format_percent(value) if value is not None else 'unknown'}")
        else:
            lines.append(f"- {key}: {format_financial_value(key, value)}")
    ratings = financial.get("analyst_rating_counts") or {}
    rating_text = ", ".join(f"{key.replace('_', ' ')} {value}" for key, value in ratings.items() if value is not None)
    if rating_text:
        lines.append(f"- analyst_rating_counts: {rating_text}")
    return lines


def append_list_section(lines: list[str], title: str, items: list[str], heading_level: str = "") -> None:
    if not items:
        return
    if heading_level:
        lines.extend(["", f"{heading_level} {title}", ""])
    else:
        lines.append(f"- {title}:")
    lines.extend(f"  - {format_report_item(item)}" if not heading_level else f"- {format_report_item(item)}" for item in items)


def format_report_item(value: Any, max_length: int = 360) -> str:
    return compact_text(strip_citations_and_markdown(str(value)), max_length)


def escape_table_cell(value: str) -> str:
    return clean_report_text(value).replace("|", "/")


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
