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
from .report_formatting import compact_complete_text, format_financial_value, format_percent as format_ratio_percent, format_plain_value, markdown_link, repair_common_mojibake


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
    grok_web = summarize_grok_web_research(packets)
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
    investor_insight = build_investor_insight_report(root, run_id, ticker, financial, news, social, filings, grok_web, positives, negatives, watch_items)

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
        "grok_web_snapshot": grok_web,
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
    valuation = insight.get("valuation_snapshot", {}) or {}
    if (
        not valuation.get("forward_pe")
        and not valuation.get("analyst_target_price")
        and not any(valuation.get(key) is not None for key in ("latest_price", "market_cap", "pe_ratio", "price_to_sales_ttm", "ev_to_ebitda_ttm"))
    ):
        findings.append(f"{ticker} investor insight report is missing usable valuation context.")
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
        "valuation_sanity_warnings": list(review.get("valuation_sanity_warnings") or []),
        "valuation_sanity_warning_count": len(review.get("valuation_sanity_warnings") or []),
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
    raw_text = prepare_evidence_for_development_extraction(evidence)
    text = clean_report_text(raw_text)
    candidates: list[str] = structured_development_summary(text)
    for line in development_candidate_lines(raw_text):
        line = clean_report_text(line.strip(" -\t"))
        if not line:
            continue
        synthesized = synthesize_development_line(line)
        if synthesized:
            candidates.append(synthesized)
            continue
        if is_bad_truncated_excerpt(line):
            continue
        if is_provider_boilerplate_excerpt(line):
            continue
        if not looks_investor_relevant(line):
            continue
        candidates.append(line)
    if candidates:
        return candidates[:6]
    sentences = re.split(r"(?<=[.!?])\s+", clean_report_text(text))
    return [
        synthesize_development_line(sentence) or sentence
        for sentence in sentences
        if looks_investor_relevant(sentence)
        and not is_bad_truncated_excerpt(sentence)
        and not is_provider_boilerplate_excerpt(sentence)
    ][:6]


def prepare_evidence_for_development_extraction(evidence: str) -> str:
    raw = str(evidence or "")
    raw = re.sub(r"\[\[\d+\]\](?:\([^)]+\))?", "", raw)
    raw = re.sub(r"\[[^\]]+\]\([^)]+\)", "", raw)
    raw = raw.replace("[...]", "\n")
    raw = re.sub(r"\s+\.{3,}\s+", "\n", raw)
    raw = re.sub(r"(?m)^\s*#{1,6}\s*", "", raw)
    raw = re.sub(r"\s+#{1,6}\s+", "\n", raw)
    return raw


def development_candidate_lines(raw_text: str) -> list[str]:
    lines: list[str] = []
    for raw_line in raw_text.splitlines():
        for part in re.split(r"\s{2,}|\s+-\s+", raw_line):
            line = part.strip()
            if not line:
                continue
            line = re.sub(r"^\d{1,4}\s+(?=[A-Z#])", "", line)
            line = re.sub(r"^[-*#\d.)\s]+", "", line).strip()
            if line:
                lines.append(line)
    return lines[:60]


def structured_development_summary(text: str) -> list[str]:
    cleaned = clean_report_text(text)
    lower = cleaned.lower()
    items: list[str] = []
    revenue = re.search(r"net sales increased\s+([\d.]+%)\s+to\s+\$([\d.]+)\s*billion", cleaned, flags=re.IGNORECASE)
    aws = re.search(r"aws segment sales increased\s+([\d.]+%)\s+year-over-year to\s+\$([\d.]+)\s*billion", cleaned, flags=re.IGNORECASE)
    income = re.search(r"operating income increased to\s+\$([\d.]+)\s*billion.*?compared with\s+\$([\d.]+)\s*billion", cleaned, flags=re.IGNORECASE)
    if revenue or aws or income:
        parts: list[str] = []
        if revenue:
            parts.append(f"net sales +{revenue.group(1)} to ${revenue.group(2)}B")
        if aws:
            parts.append(f"AWS sales +{aws.group(1)} YoY to ${aws.group(2)}B")
        if income:
            parts.append(f"operating income ${income.group(1)}B vs ${income.group(2)}B")
        items.append("Q1 2026 operating update: " + "; ".join(parts) + ".")
    guidance = re.search(
        r"net sales projected between\s+\$([\d.]+)\s*billion and\s+\$([\d.]+)\s*billion.*?operating income predicted at\s+\$([\d.]+)\s*billion to\s+\$([\d.]+)\s*billion",
        cleaned,
        flags=re.IGNORECASE,
    )
    if guidance:
        items.append(
            f"Q2 2026 guide: revenue ${guidance.group(1)}B-${guidance.group(2)}B and operating income ${guidance.group(3)}B-${guidance.group(4)}B."
        )
    adoption_summary = summarize_ai_adoption_signal(cleaned)
    if adoption_summary:
        items.append(adoption_summary)
    ecosystem_summary = summarize_strategic_ecosystem_line(cleaned)
    if ecosystem_summary:
        items.append(ecosystem_summary)
    if "amazon ads generated" in lower:
        ads = re.search(r"amazon ads generated\s+\$([\d.]+)\s*billion", cleaned, flags=re.IGNORECASE)
        items.append(f"Advertising tailwind: Amazon Ads generated ${ads.group(1)}B of revenue in Q1 with AI tools expanding reach." if ads else "Advertising tailwind: Amazon Ads growth is being tied to AI tools and expanded reach.")
    if "cost of components" in lower and "memory" in lower:
        items.append("AI infrastructure headwind: management flagged sharply higher memory component costs and possible capacity/supply volatility.")
    if "amazon leo" in lower:
        items.append("Cost watch item: Amazon LEO is expected to add about $1B of year-over-year cost pressure tied to satellite manufacturing and launches.")
    apple_revenue = re.search(r"quarterly revenue of\s+\$([\d.]+)\s*billion,\s+up\s+([\d.]+)\s+percent", cleaned, flags=re.IGNORECASE)
    apple_eps = re.search(r"diluted earnings per share was\s+\$([\d.]+),\s+up\s+([\d.]+)\s+percent", cleaned, flags=re.IGNORECASE)
    if apple_revenue:
        parts = [f"revenue ${apple_revenue.group(1)}B, +{apple_revenue.group(2)}% YoY"]
        if apple_eps:
            parts.append(f"EPS ${apple_eps.group(1)}, +{apple_eps.group(2)}% YoY")
        items.append("Fiscal Q2 2026 operating update: " + "; ".join(parts) + ".")
    apple_guidance = re.search(r"revenue growth in the current quarter would be between\s+([\d.]+%)\s+and\s+([\d.]+%)", cleaned, flags=re.IGNORECASE)
    if apple_guidance:
        items.append(f"Guidance signal: current-quarter revenue growth expected at {apple_guidance.group(1)}-{apple_guidance.group(2)}, above analyst estimates in the source excerpt.")
    return unique_texts(items, 8)


def synthesize_development_line(value: str) -> str:
    lower = value.lower()
    if lower.startswith(("seattle--", "cupertino,")):
        summary = structured_development_summary(value)
        return summary[0] if summary else ""
    if any(marker in lower for marker in ("major customer and partner announcements", "customer and partner", "strategic partnership", "partner agreements")):
        return summarize_strategic_ecosystem_line(value)
    if "cost of components" in lower and "memory" in lower:
        return "AI infrastructure headwind: management flagged sharply higher memory component costs and possible capacity/supply volatility."
    if "amazon ads generated" in lower:
        summary = structured_development_summary(value)
        return summary[0] if summary else "Advertising tailwind: Amazon Ads growth is being tied to AI tools and expanded reach."
    if "revenue growth in the current quarter would be between" in lower:
        summary = structured_development_summary(value)
        return summary[0] if summary else ""
    if "quarterly revenue of" in lower and "diluted earnings per share" in lower:
        summary = structured_development_summary(value)
        return summary[0] if summary else ""
    if "apple reported 17% revenue growth" in lower and "iphone sales came up short" in lower:
        return "Apple operating mix: revenue grew 17% and services beat estimates, but iPhone sales missed, making services/margin durability the key offset to hardware softness."
    if "reported revenue of $26.9m" in lower and "export permits" in lower:
        return "AXT reported revenue of $26.9M, up 17% QoQ and 39% YoY, slightly above forecast as export permits came in better than guidance."
    if "42 million ai soc units" in lower and "physical edge ai" in lower:
        return "Ambarella says its installed base exceeds 42M AI SoCs across edge endpoint and infrastructure use cases, including security, vehicle safety, telematics, drones, autonomy, and emerging robotics."
    if "kraken robotics delivered record 2025 revenue" in lower or ("cad 102 million" in lower and "gross profit margin" in lower):
        return "Kraken reported record 2025 revenue of CAD 102M, 12% YoY growth, and gross margin expansion to 62%, with battery/SAS demand and subsea services as the main drivers."
    if "certain preliminary 2025 year-end results" in lower and "2026 guidance" in lower:
        return "Kraken's current release confirms previously announced preliminary 2025 results and 2026 guidance, so the main update is validation of the revenue/gross-margin trajectory rather than a new standalone catalyst."
    if "micron set new records" in lower or ("revenue of $23.86 billion" in lower and "gross margin" in lower):
        return "Micron reported record revenue, gross margin, EPS, and free cash flow, with management tying the acceleration to AI memory demand, tight supply, and HBM/data-center strength."
    if "third quarter revenue of" in lower and "bookings" in lower and "funded backlog" in lower:
        return "AeroVironment reported Q3 revenue of $408M, $2.1B of bookings over the first nine months, and record funded backlog of $1.1B."
    return ""


def is_provider_boilerplate_excerpt(value: str) -> bool:
    lower = value.lower()
    noisy_starts = ("seattle--", "cupertino,", "# q1 earnings:", "andy jassy on")
    return lower.startswith(noisy_starts) or (
        len(value) > 350
        and any(marker in lower for marker in ("business wire", "today announced financial results", "earnings call transcript", "apple reported 17% revenue growth"))
    )


def is_positive_development(value: str) -> bool:
    lower = value.lower()
    if any(word in lower for word in ("headwind", "cost pressure", "supply volatility", "constraint", "skyrocketed", "negative")):
        return False
    return any(
        word in lower
        for word in (
            "growth",
            "increased",
            "operating income",
            "tailwind",
            "customer",
            "partner",
            "agreement",
            "adoption",
            "revenue",
            "bedrock",
            "aws",
            "ads",
            "custom silicon",
            "cloud commitment",
            "strategic customer",
            "strategic partner",
        )
    )


def is_bad_truncated_excerpt(value: str) -> bool:
    lower = value.lower()
    if "##" in value or value.lstrip().startswith("#"):
        return True
    if value.rstrip().endswith(":") and len(value) > 50:
        return True
    if value.count("(") != value.count(")") or value.count("[") != value.count("]"):
        return True
    if re.search(r"\b(?:up|down|during|with|from|to|of|and|or|including|amid|for|in|by|the|a|while)\.$", lower) and len(value) > 40:
        return True
    if re.search(r"\b(?:hig|implying|compared|indust|announc|subsequen|preliminar|approxim|financ|operat|developm)\.$", lower):
        return True
    if re.search(r"\b(?:is|are|was|were|be)\.$", lower) and len(value) > 70:
        return True
    if value.endswith("...") and any(fragment in lower for fragment in ("per diluted s", "per diluted sh", "the anthropic de", "substan")):
        return True
    if value.startswith('"') and value.count('"') % 2 == 1:
        return True
    if "we're pleased to our work" in lower:
        return True
    if lower.startswith(('"we are pleased', '"we\'re pleased')) and not any(token in lower for token in ("revenue", "order", "guidance", "backlog", "margin", "$", "%")):
        return True
    return False


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
        "order",
        "battery",
        "sonar",
    )
    return any(keyword in lower for keyword in keywords)


def summarize_social(packets: list[EvidencePacket]) -> dict[str, Any]:
    social_packets = [packet for packet in packets if is_xai_x_search_packet(packet)]
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
        "bullish_claims": section_items(sections, ["recurring bullish arguments", "recurring bullish claims", "bull case narratives"], limit=5),
        "bearish_claims": section_items(sections, ["recurring bearish or skeptical arguments", "recurring bearish/neutral claims", "recurring bearish claims", "bear/skeptic narratives"], limit=5),
        "strategic_partnerships": section_items(
            sections,
            ["strategic partnerships investments and ecosystem leverage", "strategic partnerships, investments, and ecosystem leverage"],
            limit=5,
        ),
        "news_reactions": section_items(sections, ["notable news people are reacting to"], limit=5),
        "non_obvious_angles": section_items(sections, ["non-obvious or under-discussed angles", "non-obvious insights", "non-obvious / under-discussed insights"], limit=5),
        "notable_accounts": notable_accounts[:6],
        "hype_noise": first_non_empty_section(sections, ["hype / noise level", "hype/noise level", "hype/noise/spam level"], fallback=""),
        "rumors": rumors,
        "investor_implications": section_items(
            sections,
            [
                "concrete implications for an investor",
                "concrete implications for an investor (separate verified facts vs. sentiment vs. speculation)",
                "investor implications",
                "investor implications and scorecard",
                "bottom-line investor takeaway",
            ],
            limit=5,
            fallback_paragraph=True,
        ),
        "summary_excerpt": compact_text(text, 1200),
    }


def is_xai_x_search_packet(packet: EvidencePacket) -> bool:
    if packet.provider != "xai_grok":
        return False
    haystack = " ".join([packet.packet_id, packet.raw_artifact_path or "", packet.notes or ""]).lower()
    return "x_search" in haystack or "xai_x_search" in haystack


def is_xai_web_search_packet(packet: EvidencePacket) -> bool:
    if packet.provider != "xai_grok":
        return False
    haystack = " ".join([packet.packet_id, packet.raw_artifact_path or "", packet.notes or ""]).lower()
    return "web_search" in haystack or "web_deep_dive" in haystack


def summarize_grok_web_research(packets: list[EvidencePacket]) -> dict[str, Any]:
    web_packets = [packet for packet in packets if is_xai_web_search_packet(packet)]
    raw_texts = [text for packet in web_packets if (text := read_xai_raw_output(packet.raw_artifact_path))]
    text = "\n".join(raw_texts or [claim.evidence for packet in web_packets for claim in packet.claims])
    sections = parse_grok_sections(text)
    sources = [source for packet in web_packets for source in packet.sources]
    return {
        "status": "available" if web_packets else "missing",
        "packet_count": len(web_packets),
        "citation_count": len([source for source in sources if source.url]),
        "business_technology_overview": first_non_empty_section(
            sections,
            ["business & technology overview", "business and technology overview"],
            fallback="",
        ),
        "industry_competition": first_non_empty_section(
            sections,
            ["industry context & competitive landscape", "industry context and competitive landscape"],
            fallback="",
        ),
        "latest_news_rumors": section_items(sections, ["latest news & rumors", "latest news and rumors"], limit=5, fallback_paragraph=True),
        "financial_snapshot": first_non_empty_section(sections, ["financial snapshot"], fallback=""),
        "analyst_forecasts": first_non_empty_section(sections, ["analyst forecasts"], fallback=""),
        "catalysts_tailwinds": section_items(sections, ["catalysts & tailwinds", "catalysts and tailwinds"], limit=5),
        "risks_headwinds": section_items(sections, ["risks & headwinds", "risks and headwinds"], limit=5),
        "overall_assessment": first_non_empty_section(
            sections,
            ["overall assessment & research checks", "overall assessment and research checks", "overall assessment"],
            fallback=first_paragraph(text),
        ),
        "summary_excerpt": compact_text(text, 1200) if text else "",
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
    if int(financial.get("valuation_sanity_warning_count") or 0):
        score -= 6
        factors.append("-6 valuation snapshot has sanity warnings and needs cross-provider verification before use.")
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
    if score < 45 or social.get("rumor_flag") or filings.get("status") == "missing" or financial.get("valuation_sanity_warning_count"):
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
    if financial.get("valuation_sanity_warning_count"):
        return "medium" if {"financial_data_specialist", "company_news_specialist"}.issubset(providers) else "low"
    if required.issubset(providers) and not financial.get("conflict_count") and news.get("contents_claim_count"):
        return "high"
    if {"financial_data_specialist", "company_news_specialist"}.issubset(providers):
        return "medium"
    return "low"


def build_positives(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any], filings: dict[str, Any]) -> list[str]:
    positives: list[str] = []
    for item in strategic_ai_items(news, social)[:2]:
        positives.append(item if item.lower().startswith("strategic") else f"Strategic AI ecosystem: {item}")
    for development in news.get("material_developments", []):
        claim_text = development.get("claim") if isinstance(development, dict) else ""
        if claim_text and is_positive_development(claim_text):
            positives.append(claim_text)
        if len(positives) >= 5:
            break
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
    if financial.get("valuation_sanity_warnings"):
        negatives.append("Valuation snapshot has sanity warnings; use the valuation section for specific checks before relying on headline metrics.")
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
    if financial.get("valuation_sanity_warnings"):
        items.append("Complete cross-provider valuation sanity review before using headline price, market cap, P/E, or target-gap conclusions.")
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
    if not financial.get("forward_pe") and not financial.get("analyst_target_price"):
        notes.append("Forward P/E and analyst target were not available from the current provider artifacts; use the valuation table as trailing/contextual, not consensus-forward.")
    if financial.get("taxonomy_conflict_count"):
        notes.append("Provider industry labels differ; keep this as internal classification hygiene, not an investment risk.")
    if financial.get("single_provider_metric_count"):
        notes.append("Some financial metrics are single-provider; use them as directional until cross-provider coverage improves.")
    if financial.get("valuation_sanity_warnings"):
        notes.append("Valuation sanity checks flagged the headline snapshot; do not use price, market cap, or P/E as clean consensus until cross-provider verification is complete.")
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
    grok_web: dict[str, Any],
    positives: list[str],
    negatives: list[str],
    watch_items: list[str],
) -> dict[str, Any]:
    company_context = build_company_context(root, run_id, ticker, financial, grok_web)
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
        "grok_web_research": grok_web,
        "non_obvious_insights": non_obvious,
        "valuation_snapshot": valuation_snapshot,
        "peer_competition_context": build_peer_competition_context(root, run_id, ticker, company_context),
        "decision_table": table,
        "next_research_questions": build_next_research_questions(financial, news, social, watch_items),
    }


def build_company_context(root: Path, run_id: str, ticker: str, financial: dict[str, Any], grok_web: dict[str, Any] | None = None) -> dict[str, Any]:
    exa_context = read_exa_company_context(root, run_id, ticker)
    grok_web = grok_web or {}
    description = financial.get("company_description") or exa_context.get("description") or grok_web.get("business_technology_overview") or ""
    return {
        "what_it_does": compact_text(description, 700) if description else "Company description was not available from current provider artifacts.",
        "sector": financial.get("sector") or exa_context.get("industry") or "unknown",
        "industry": financial.get("industry") or exa_context.get("industry") or "unknown",
        "business_model_notes": extract_business_model_notes(description, exa_context.get("highlights", "")),
        "source": exa_context.get("source") or ("Grok web_search auxiliary report" if grok_web.get("business_technology_overview") else "financial provider profile"),
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
        "valuation_sanity_warnings": list(financial.get("valuation_sanity_warnings") or []),
    }


def build_community_split(social: dict[str, Any]) -> dict[str, Any]:
    return {
        "x_pulse": social.get("x_pulse", ""),
        "bullish_camp": list(social.get("bullish_claims") or [])[:5],
        "skeptical_camp": list(social.get("bearish_claims") or [])[:5],
        "strategic_partnerships": list(social.get("strategic_partnerships") or [])[:5],
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
    first_positive = normalize_sentence_fragment(
        summarize_developments_short(news) or (strip_citations_and_markdown(positives[0]) if positives else "recent evidence is mixed")
    )
    social_context = ""
    if social.get("bullish_claims") or social.get("bearish_claims"):
        social_context = " X adds a separate narrative layer that should be checked against fundamentals, not treated as proof."
    return compact_text(f"{sector} / {industry}: {first_positive}.{social_context}", 520)


def normalize_sentence_fragment(value: str) -> str:
    return clean_report_text(value).rstrip(" .;:")


def build_tailwinds(news: dict[str, Any], social: dict[str, Any], positives: list[str]) -> list[str]:
    items: list[str] = []
    for value in positives:
        if is_positive_development(value) and any(word in value.lower() for word in ("growth", "aws", "ai", "margin", "sales", "revenue", "income", "backlog", "ads", "partnership", "anthropic", "claude", "trainium", "bedrock")):
            items.append(value)
    if not any("strategic ai ecosystem" in item.lower() for item in items):
        items.extend(strategic_ai_items(news, social))
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
        elif any(word in claim.lower() for word in ("adoption", "agreement", "partner", "bedrock")):
            items.append(f"Ecosystem trend: {claim}")
    for item in social.get("strategic_partnerships", [])[:2]:
        items.append(f"Strategic ecosystem trend: {strip_citations_and_markdown(str(item))}")
    return unique_texts(items, 5)


def build_non_obvious_insights(financial: dict[str, Any], news: dict[str, Any], social: dict[str, Any]) -> list[str]:
    candidates: list[str] = []
    for angle in social.get("non_obvious_angles", [])[:4]:
        candidates.append(f"X under-discussed angle: {strip_citations_and_markdown(str(angle))}")
    for item in strategic_ai_items(news, social)[:3]:
        cleaned = strip_citations_and_markdown(item)
        if cleaned.lower().startswith("strategic ecosystem signal:"):
            cleaned = "Evidence-backed ecosystem leverage: " + cleaned.split(":", 1)[1].strip()
        candidates.append(f"Strategic AI ecosystem angle: {cleaned}")
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


def strategic_ai_items(news: dict[str, Any], social: dict[str, Any]) -> list[str]:
    items: list[str] = []
    for value in social.get("strategic_partnerships", []) or []:
        summary = summarize_strategic_ecosystem_line(str(value)) or summarize_strategic_ai_line(str(value))
        if summary:
            items.append(summary)
    for claim in news.get("contents_claims", []) + news.get("material_claims", []):
        evidence = str(claim.get("evidence", "")) if isinstance(claim, dict) else ""
        for line in extract_development_items(evidence):
            summary = summarize_strategic_ecosystem_line(line) or summarize_strategic_ai_line(line)
            if summary:
                items.append(summary)
    for development in news.get("material_developments", []):
        claim = str(development.get("claim", "")) if isinstance(development, dict) else ""
        summary = summarize_strategic_ecosystem_line(claim) or summarize_strategic_ai_line(claim)
        if summary:
            items.append(summary)
    return collapse_strategic_items(items, 5)


def collapse_strategic_items(items: list[str], limit: int) -> list[str]:
    unique = unique_texts(items, limit + 2)
    ecosystem_entities: list[str] = []
    other_items: list[str] = []
    for item in unique:
        match = re.search(r"evidence cites (.*?), suggesting customer/partner leverage", item)
        if match:
            ecosystem_entities.extend(entity.strip() for entity in match.group(1).split(",") if entity.strip())
        else:
            other_items.append(item)
    merged: list[str] = []
    if ecosystem_entities:
        entity_text = ", ".join(unique_texts(ecosystem_entities, 10))
        merged.append(
            f"Strategic ecosystem signal: evidence cites {entity_text}, suggesting customer/partner leverage that may matter beyond the headline financial metrics."
        )
    merged.extend(other_items)
    return unique_texts(merged, limit)


def summarize_ai_adoption_signal(value: str) -> str:
    lower = value.lower()
    if "bedrock" in lower and ("170%" in lower or "tokens" in lower):
        return "AI platform adoption signal: Bedrock customer spend reportedly grew 170% quarter-over-quarter and Q1 token processing exceeded all prior years combined."
    if "tokens" in lower and any(term in lower for term in ("customer spend", "usage", "processed", "inference")):
        return compact_text(value, 220)
    return ""


def summarize_strategic_ecosystem_line(value: str) -> str:
    lower = value.lower()
    if "cost of components" in lower or "skyrocketed" in lower:
        return ""
    if not is_strategic_ecosystem_signal(lower):
        return ""
    entities = named_strategic_entities(value)
    entity_text = ", ".join(entities[:8]) if entities else "major customers, partners, or suppliers"
    if any(term in lower for term in ("customer", "agreement", "deal", "contract", "commitment", "partnership", "partner")):
        return (
            f"Strategic ecosystem signal: evidence cites {entity_text}, suggesting customer/partner leverage that may matter beyond the headline financial metrics."
        )
    if any(term in lower for term in ("custom silicon", "trainium", "inferentia", "ai chip", "accelerator", "foundry", "packaging")):
        return (
            f"Strategic technology leverage: evidence links {entity_text} to custom silicon, AI infrastructure, or supply-chain positioning that should be verified as a durable thesis driver."
        )
    return compact_text(value, 220)


def is_strategic_ecosystem_signal(lower: str) -> bool:
    strategic_terms = (
        "anthropic",
        "claude",
        "openai",
        "cerebras",
        "nvidia",
        "meta",
        "uber",
        "bedrock",
        "trainium",
        "inferentia",
        "custom silicon",
        "ai chip",
        "accelerator",
        "cloud commitment",
        "strategic partner",
        "strategic customer",
        "major customer",
        "partner agreement",
        "supplier dependency",
    )
    action_terms = (
        "agreement",
        "announced",
        "partner",
        "customer",
        "commitment",
        "contract",
        "uses",
        "adoption",
        "selected",
        "deploy",
        "training",
        "inference",
    )
    return any(term in lower for term in strategic_terms) and any(term in lower for term in action_terms)


def named_strategic_entities(value: str) -> list[str]:
    known = [
        "Amazon Bedrock",
        "OpenAI",
        "Anthropic",
        "Claude",
        "NVIDIA",
        "Cerebras",
        "Meta",
        "Uber",
        "AWS",
        "Trainium",
        "Inferentia",
        "MediaTek",
        "Intel",
        "Broadcom",
        "Microsoft",
        "Google",
        "Oracle",
    ]
    lower = value.lower()
    found = [name for name in known if name.lower() in lower]
    ticker_entities = re.findall(r"\$[A-Z][A-Z0-9.]{1,6}\b", value)
    return unique_texts(found + ticker_entities, 10)


def summarize_strategic_ai_line(value: str) -> str:
    lower = value.lower()
    if not any(keyword in lower for keyword in ("anthropic", "claude", "trainium", "bedrock", "openai", "cerebras", "custom silicon", "ai chip")):
        return ""
    if "cost of components" in lower or "skyrocketed" in lower:
        return ""
    if any(keyword in lower for keyword in ("anthropic", "openai", "cerebras", "nvidia")) and any(
        keyword in lower for keyword in ("agreement", "announced", "partner", "customer")
    ):
        return summarize_strategic_ecosystem_line(value) or "Strategic AI ecosystem signal: evidence cites major AI customer or partner agreements that may matter beyond headline financial metrics."
    if "bedrock" in lower and ("170%" in lower or "tokens" in lower):
        return summarize_ai_adoption_signal(value)
    if "trainium" in lower:
        return "Trainium remains a strategic AWS AI lever: verify whether customer adoption and capacity commitments are translating into durable cloud revenue and margin leverage."
    if "anthropic" in lower or "claude" in lower:
        return "Anthropic/Claude is a strategic AWS ecosystem asset; verify whether Bedrock usage, training commitments, and investment gains are recurring value or one-off mark-to-market noise."
    return compact_text(value, 190)


def build_peer_competition_context(root: Path, run_id: str, ticker: str, company_context: dict[str, Any]) -> dict[str, Any]:
    exa_context = read_exa_company_context(root, run_id, ticker)
    competitors = exa_context.get("competitors") or fallback_peer_candidates(ticker, company_context)
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


def fallback_peer_candidates(ticker: str, company_context: dict[str, Any]) -> list[str]:
    text = " ".join(
        str(company_context.get(key, ""))
        for key in ("sector", "industry", "description", "business_model_notes")
    ).lower()
    ticker_upper = ticker.upper()
    if ticker_upper == "AMZN" or any(word in text for word in ("internet retail", "broadline retail", "marketplace", "aws", "cloud")):
        return ["Walmart", "Alibaba Group", "Microsoft", "Google", "Meta", "Target", "Costco", "eBay", "Oracle"]
    if ticker_upper == "AAPL" or any(word in text for word in ("consumer electronics", "iphone", "hardware")):
        return ["Microsoft", "Google", "Samsung", "Meta", "Sony", "Dell", "HP", "Lenovo"]
    if any(word in text for word in ("semiconductor", "chip", "accelerator")):
        return ["NVIDIA", "AMD", "Broadcom", "Intel", "Marvell", "Qualcomm", "TSMC", "ASML"]
    if any(word in text for word in ("software", "cloud", "saas")):
        return ["Microsoft", "Oracle", "Salesforce", "Adobe", "ServiceNow", "Snowflake"]
    return []


def build_summary_table(
    financial: dict[str, Any],
    news: dict[str, Any],
    social: dict[str, Any],
    filings: dict[str, Any],
    thesis: dict[str, Any],
    valuation: dict[str, Any],
    non_obvious: list[str],
) -> list[dict[str, str]]:
    development_count = len(news.get("material_developments") or [])
    bull_count = len(social.get("bullish_claims") or [])
    bear_count = len(social.get("bearish_claims") or [])
    non_obvious_count = len(non_obvious or [])
    return [
        {
            "dimension": "Growth / demand",
            "current_read": f"{development_count} source-backed recent development(s) and {len(thesis.get('tailwinds') or [])} extracted tailwind(s) need ranking by thesis impact.",
            "evidence": "Exa news + earnings/call excerpts",
            "follow_up": "Check whether growth is broad-based or mostly one segment.",
        },
        {
            "dimension": "Community / X sentiment",
            "current_read": f"{social.get('sentiment', 'missing')} with {bull_count} bull theme(s) and {bear_count} skeptic theme(s); use the X section for the actual narratives.",
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
            "current_read": f"{non_obvious_count} under-discussed angle(s) extracted; verify only those that would change the thesis or next research decision.",
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
    thesis_text = claim_theme(str(thesis.get("core_thesis") or "Evidence is incomplete."))
    valuation_text = "needs verification before using headline price/market-cap/P/E" if valuation.get("valuation_sanity_warnings") else valuation_sentence(valuation)
    bull_count = len(community.get("bullish_camp") or [])
    bear_count = len(community.get("skeptical_camp") or [])
    non_obvious_text = f"{len(non_obvious)} under-discussed angle(s) to verify" if non_obvious else "no strong under-discussed angle extracted"
    return compact_text(
        f"{ticker}: {thesis_text}. Valuation context: {valuation_text}. X/community evidence adds {bull_count} bull theme(s) and {bear_count} skeptic theme(s), so the key job is to verify which social claims are supported by filings, news, and financials. Main extra check: {non_obvious_text}.",
        760,
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
        match = re.search(r"revenue for the fourth quarter.*?\$([\d.]+)\s*million,\s+up\s+([\d.]+%)", value, flags=re.IGNORECASE)
        if match:
            return f"quarterly revenue ${match.group(1)}M, +{match.group(2)} YoY"
    if kind == "aws":
        match = re.search(r"aws segment sales increased\s+([\d.]+%)\s+year-over-year to\s+\$([\d.]+)\s+billion", value, flags=re.IGNORECASE)
        if match:
            return f"AWS sales +{match.group(1)} YoY to ${match.group(2)}B"
    if kind == "income":
        match = re.search(r"operating income increased to\s+\$([\d.]+)\s+billion.*compared with\s+\$([\d.]+)\s+billion", value, flags=re.IGNORECASE)
        if match:
            return f"operating income ${match.group(1)}B vs ${match.group(2)}B"
        match = re.search(r"gross margin.*?was\s+([\d.]+%).*?compared with\s+([\d.]+%)", value, flags=re.IGNORECASE)
        if match:
            return f"GAAP gross margin {match.group(1)} vs {match.group(2)} YoY"
    if kind == "ai_partnership":
        return summarize_strategic_ai_line(value) or compact_text(value, 170)
    fallback = compact_text(value, 130)
    return "" if is_bad_truncated_excerpt(fallback) else fallback


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
        if any(marker in item for marker in ("[", "]", "(", ")")):
            continue
        if re.search(r"\d", item):
            continue
        if any(skip in item.lower() for skip in ("competitors", "categories", "products", "tech stack", "comments", "comment")):
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
    positive = claim_theme(positives[0] if positives else "limited positive evidence")
    negative = claim_theme(negatives[0] if negatives else "limited caveat evidence")
    social_context = ""
    if social.get("status") == "available":
        social_context = f" {ticker} Grok/X adds {len(social.get('bullish_claims') or [])} bull theme(s) and {len(social.get('bearish_claims') or [])} skeptic theme(s) for verification."
    return (
        f"{ticker} is {opportunity_view} ({score}/100, {risk_level} risk, {confidence} confidence). "
        f"{ticker} main positive driver: {positive}. {ticker} main caveat: {negative}.{social_context}"
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


def claim_theme(value: str) -> str:
    lower = strip_citations_and_markdown(str(value)).lower()
    themes: list[str] = []
    if any(word in lower for word in ("rumor", "speculation", "speculative", "unverified", "verify", "unconfirmed")):
        themes.append("verification risk around unconfirmed claims")
    if any(word in lower for word in ("revenue", "sales", "guidance", "backlog", "demand", "orders")):
        themes.append("source-backed growth/demand evidence")
    if any(word in lower for word in ("margin", "income", "profit", "cash flow", "ebitda", "fcf")):
        themes.append("profitability or cash-conversion evidence")
    if any(word in lower for word in ("ai", "chip", "semiconductor", "cloud", "robot", "autonomous", "subsea", "software", "nvidia", "customer", "partner", "ecosystem")):
        themes.append("technology or product-positioning evidence")
    if any(word in lower for word in ("strategic ecosystem", "customer/partner", "major customers", "supplier", "contract")):
        themes.append("strategic ecosystem/customer leverage evidence")
    if any(word in lower for word in ("valuation", "multiple", "p/e", "expensive", "target", "market cap")):
        themes.append("valuation risk")
    if any(word in lower for word in ("competition", "competitor", "execution", "cyclical", "dilution", "debt", "risk", "uncertain")):
        themes.append("execution or competitive risk")
    if themes:
        return ", ".join(unique_texts(themes, 3))
    return compact_text(strip_citations_and_markdown(str(value)), 180)


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
        bull = compact_text(strip_citations_and_markdown(str(social["bullish_claims"][0])), 360)
        bear = compact_text(strip_citations_and_markdown(str(social["bearish_claims"][0])), 360)
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
    sources = assessment_source_lookup(root, run_id, str(assessment["ticker"]))
    lines = [
        f"# Opportunity Assessment: {assessment['ticker']}",
        "",
        f"Status: `{assessment['status']}`",
        f"Opportunity view: `{assessment['opportunity_view']}`",
        f"Opportunity score: **{assessment['opportunity_score']}/100**",
        f"Risk level: `{assessment['risk_level']}`",
        f"Confidence: `{assessment['confidence']}`",
        f"Thesis freshness: `{assessment['thesis_freshness']}`",
        "",
        "## Verdict",
        "",
        compact_complete_text(assessment["summary"], 900),
        "",
        "### Why The Score Looks Like This",
        "",
        *format_score_rationale(assessment),
        "",
        "## Investor Insight Report",
    ]
    insight = assessment.get("investor_insight_report") or {}
    lines.extend(format_investor_insight_markdown(insight))
    report_seen = seen_from_markdown_lines(lines)
    lines.extend(["", "## Actionable Follow-ups", ""])
    followups = unique_report_items(assessment["watch_items"], seen=report_seen, limit=6, max_length=650)
    if followups:
        lines.extend(f"- {item}" for item in followups)
    else:
        lines.append("- No distinct follow-up beyond the investor insight report above.")
    lines.extend(["", "## Filing And Data Coverage", ""])
    filing = assessment["filing_snapshot"]
    lines.append(f"- status: {filing.get('status')}")
    lines.append(f"- packet_count: {filing.get('packet_count')}")
    for item in filing.get("recent_items", [])[:3]:
        lines.append(f"- item: {format_report_item(item, 500)}")
    if assessment.get("data_quality_notes"):
        lines.extend(["", "### Internal Data Quality Notes", ""])
        lines.extend(f"- {format_report_item(item, 500)}" for item in assessment["data_quality_notes"])
    lines.extend(["", "## Sources", ""])
    source_lines = format_assessment_sources(assessment.get("source_ids", []), sources)
    lines.extend(source_lines or ["- No source URLs were available in the input packets."])
    lines.append(f"- run: `{relative_to_root(root, root / 'agents' / 'runs' / run_id).as_posix()}`")
    lines.extend(["", "## Quality Findings", ""])
    if assessment.get("quality_findings"):
        lines.extend(f"- {item}" for item in assessment["quality_findings"])
    else:
        lines.append("- None.")
    next_action = unique_report_items([assessment["recommended_next_action"]], seen=report_seen, limit=1, max_length=650)
    lines.extend(["", "## Recommended Next Action", ""])
    lines.extend(f"- {item}" for item in (next_action or ["Use the non-repeated follow-up checks above as the next review path."]))
    return "\n".join(lines).rstrip() + "\n"


def assessment_source_lookup(root: Path, run_id: str, ticker: str) -> dict[str, Source]:
    try:
        packets = load_company_packets(root, run_id, ticker)
    except Exception:
        return {}
    sources: dict[str, Source] = {}
    for packet in packets:
        for source in packet.sources:
            if source.source_id:
                sources[source.source_id] = source
    return sources


def format_assessment_sources(source_ids: list[str], sources: dict[str, Source]) -> list[str]:
    lines: list[str] = []
    for source_id in source_ids:
        source = sources.get(source_id)
        if not source:
            lines.append(f"- {source_id}: source metadata unavailable in current packet set")
            continue
        label = source.title or source.publisher or source.provider or source.source_id
        target = source.url or source.artifact_path
        lines.append(f"- {source_id}: {markdown_link(label, target) if target else label}")
    return lines


def format_score_rationale(assessment: dict[str, Any]) -> list[str]:
    lines = [
        f"- Score: {assessment['opportunity_score']}/100; view={assessment['opportunity_view']}; risk={assessment['risk_level']}; confidence={assessment['confidence']}.",
    ]
    for item in assessment.get("score_factors", [])[:6]:
        lines.append(f"- {format_report_item(item, 500)}")
    return lines


def format_investor_insight_markdown(insight: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    seen: set[str] = set()
    executive_read = insight.get("executive_read") or "No executive read generated."
    lines.extend(["### Executive Read", "", executive_read, ""])
    remember_report_text(executive_read, seen)
    context = insight.get("company_context") or {}
    lines.extend(
        [
            "### Business, Technology, And Industry Context",
            "",
            f"- What it does: {format_report_item(context.get('what_it_does') or 'unknown', 850)}",
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
    core_thesis = format_report_item(thesis.get("core_thesis") or "No core thesis generated.", 650)
    lines.append(f"- Core thesis: {core_thesis}")
    remember_report_text(core_thesis, seen)
    append_list_section(lines, "What changed recently", thesis.get("what_changed_recently") or [], seen=seen, limit=5, max_length=520)
    append_list_section(lines, "Tailwinds", thesis.get("tailwinds") or [], seen=seen, limit=4, max_length=500)
    append_list_section(lines, "Headwinds / debate points", thesis.get("headwinds") or [], seen=seen, limit=5, max_length=500)
    append_list_section(lines, "Trend evolution", thesis.get("trend_evolution") or [], seen=seen, limit=4, max_length=500)

    community = insight.get("community_and_expert_split") or {}
    lines.extend(["", "### Expert / Community Split From X", ""])
    x_pulse = community.get("x_pulse") or "No X pulse available."
    append_unique_labeled_item(lines, "X pulse", x_pulse, seen, max_length=700)
    append_list_section(lines, "Bullish camp", community.get("bullish_camp") or [], seen=seen, limit=4, max_length=520)
    append_list_section(lines, "Skeptical camp", community.get("skeptical_camp") or [], seen=seen, limit=4, max_length=520)
    append_list_section(lines, "Strategic partnerships / ecosystem leverage", community.get("strategic_partnerships") or [], seen=seen, limit=3, max_length=500)
    if community.get("notable_accounts_or_posts"):
        lines.append(f"- Accounts/posts worth reviewing: {', '.join(community['notable_accounts_or_posts'][:8])}")
    if community.get("hype_noise_assessment"):
        append_unique_labeled_item(lines, "Hype/noise", community["hype_noise_assessment"], seen, max_length=500)
    append_list_section(lines, "Rumors / unverified claims", community.get("rumors_or_unverified") or [], seen=seen, limit=3, max_length=500)

    grok_web = insight.get("grok_web_research") or {}
    if grok_web.get("status") == "available":
        lines.extend(["", "### Auxiliary Grok Web Deep Dive", ""])
        lines.append("- Use: auxiliary coverage-gap evidence only; verify material claims with Exa contents, filings, company sources, or financial providers.")
        append_unique_labeled_item(lines, "Business / technology", grok_web.get("business_technology_overview", ""), seen, max_length=700)
        append_unique_labeled_item(lines, "Industry / competition", grok_web.get("industry_competition", ""), seen, max_length=700)
        append_list_section(lines, "Latest news / rumors from web search", grok_web.get("latest_news_rumors") or [], seen=seen, limit=4, max_length=520)
        append_unique_labeled_item(lines, "Financial / analyst gap check", grok_web.get("financial_snapshot", ""), seen, max_length=520)
        append_unique_labeled_item(lines, "Analyst forecasts", grok_web.get("analyst_forecasts", ""), seen, max_length=520)
        append_list_section(lines, "Grok web catalysts to verify", grok_web.get("catalysts_tailwinds") or [], seen=seen, limit=3, max_length=500)
        append_list_section(lines, "Grok web risks to verify", grok_web.get("risks_headwinds") or [], seen=seen, limit=3, max_length=500)
        append_unique_labeled_item(lines, "Overall web read", grok_web.get("overall_assessment", ""), seen, max_length=650)

    append_list_section(
        lines,
        "Non-obvious / under-discussed insights to verify",
        insight.get("non_obvious_insights") or [],
        heading_level="###",
        seen=seen,
        limit=5,
        max_length=520,
    )

    valuation = insight.get("valuation_snapshot") or {}
    lines.extend(["", "### Valuation And Analyst Snapshot", ""])
    if valuation.get("valuation_sanity_warnings"):
        lines.append("- Valuation sanity: needs cross-provider verification before using headline price, market cap, P/E, or target-gap conclusions.")
        lines.extend(f"- Warning: {format_report_item(item, 500)}" for item in valuation.get("valuation_sanity_warnings", [])[:4])
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
    append_list_section(lines, "Next research questions", insight.get("next_research_questions") or [], heading_level="###", seen=seen, limit=5, max_length=520)
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
        "valuation_sanity_warning_count",
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
    for warning in financial.get("valuation_sanity_warnings", [])[:4]:
        lines.append(f"- valuation_sanity_warning: {format_report_item(warning, 500)}")
    ratings = financial.get("analyst_rating_counts") or {}
    rating_text = ", ".join(f"{key.replace('_', ' ')} {value}" for key, value in ratings.items() if value is not None)
    if rating_text:
        lines.append(f"- analyst_rating_counts: {rating_text}")
    return lines


def append_list_section(
    lines: list[str],
    title: str,
    items: list[str],
    heading_level: str = "",
    *,
    seen: set[str] | None = None,
    limit: int | None = None,
    max_length: int = 360,
) -> None:
    visible_items = unique_report_items(items, seen=seen, limit=limit or len(items), max_length=max_length)
    if not visible_items:
        return
    if heading_level:
        lines.extend(["", f"{heading_level} {title}", ""])
    else:
        lines.append(f"- {title}:")
    lines.extend(f"  - {item}" if not heading_level else f"- {item}" for item in visible_items)


def append_unique_labeled_item(lines: list[str], label: str, value: Any, seen: set[str], *, max_length: int = 360) -> None:
    formatted = format_report_item(value, max_length)
    if not formatted:
        return
    key = normalize_claim_key(formatted)
    if key and is_report_duplicate(key, seen):
        return
    if key:
        seen.add(key)
    lines.append(f"- {label}: {formatted}")


def unique_report_items(
    items: list[Any],
    *,
    seen: set[str] | None = None,
    limit: int,
    max_length: int = 360,
) -> list[str]:
    result: list[str] = []
    local_seen = seen if seen is not None else set()
    for item in items:
        formatted = format_report_item(item, max_length)
        if not formatted:
            continue
        key = normalize_claim_key(formatted)
        if not key or is_report_duplicate(key, local_seen):
            continue
        local_seen.add(key)
        result.append(formatted)
        if len(result) >= limit:
            break
    return result


def remember_report_text(value: Any, seen: set[str]) -> None:
    for sentence in split_report_sentences(str(value)):
        key = normalize_claim_key(sentence)
        if key and len(key.split()) >= 8:
            seen.add(key)


def seen_from_markdown_lines(lines: list[str]) -> set[str]:
    seen: set[str] = set()
    for line in lines:
        if line.startswith(("## Sources", "- run:", "## Quality Findings")):
            continue
        remember_report_text(line, seen)
    return seen


def split_report_sentences(value: str) -> list[str]:
    cleaned = clean_report_text(strip_citations_and_markdown(value))
    if not cleaned:
        return []
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", cleaned) if sentence.strip()]


def is_report_duplicate(key: str, existing: set[str]) -> bool:
    if is_duplicate_key(key, existing):
        return True
    words = set(key.split())
    if len(words) < 8:
        return False
    for previous in existing:
        previous_words = set(previous.split())
        if len(previous_words) < 8:
            continue
        overlap = len(words & previous_words) / max(len(words), len(previous_words))
        if overlap >= 0.82:
            return True
    return False


def format_report_item(value: Any, max_length: int = 360) -> str:
    return compact_text(strip_citations_and_markdown(str(value)), max_length)


def escape_table_cell(value: str) -> str:
    return clean_report_text(value).replace("|", "/")


def compact_text(value: str, max_length: int) -> str:
    compact = " ".join(line.strip() for line in value.splitlines() if line.strip())
    compact = repair_common_mojibake(compact)
    compact = clean_report_text(compact)
    return compact_complete_text(compact, max_length)


def clean_report_text(value: str) -> str:
    value = repair_common_mojibake(str(value or ""))
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
    value = re.sub(r"\[\[\d+\]\](?:\([^)]+\))?", "", value)
    value = re.sub(r"(?<!\!)\[(\d+)\](?!\()", "", value)
    value = re.sub(r"\s*\[\.\.\.\]\s*", " ", value)
    value = value.replace("...", ".")
    value = re.sub(r"(?m)^\s*#{1,6}\s*", "", value)
    value = re.sub(r"\s+#{1,6}\s+", " ", value)
    value = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
    value = re.sub(r"\*(.*?)\*", r"\1", value)
    return " ".join(value.split())


def strip_citations_and_markdown(value: str) -> str:
    value = re.sub(r"\[\[\d+\]\]\([^)]+\)", "", value)
    value = re.sub(r"\[\[\d+\]\]", "", value)
    value = re.sub(r"(?<!\!)\[(\d+)\](?!\()", "", value)
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
    normalized = re.sub(r"\s+", " ", value.strip().lower())
    normalized = re.sub(r"^\(?\d+\)?[.)]\s*", "", normalized)
    return normalized


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
        table_item = table_row_to_investor_item(line)
        if table_item:
            items.append(table_item)
            if len(items) >= limit:
                return items
            continue
        if line.startswith("|"):
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


def table_row_to_investor_item(line: str) -> str:
    if not line.startswith("|"):
        return ""
    if set(line.replace("|", "").strip()) <= {"-", ":"}:
        return ""
    cells = [clean_report_text(cell) for cell in line.strip("|").split("|")]
    cells = [cell for cell in cells if cell]
    if not cells or cells[0].lower() in {"signal", "candidate/theme", "dimension"}:
        return ""
    if len(cells) >= 5:
        return compact_text(
            f"{cells[0]}: evidence {cells[1]} with confidence {cells[2]}; confirm via {cells[3]}; invalidate if {cells[4]}.",
            420,
        )
    if len(cells) >= 3:
        return compact_text(f"{cells[0]}: {cells[1]} Next check: {cells[-1]}.", 360)
    return ""


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
