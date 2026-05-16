from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .memory import relative_to_root
from .repo import find_repo_root
from .report_formatting import compact_complete_text, format_financial_value, format_plain_value


@dataclass(frozen=True)
class WeeklyDigest:
    run_id: str
    status: str
    ticker_count: int
    open_review_count: int
    tickers: list[dict[str, Any]]
    next_actions: list[str]
    quality_findings: list[str]


def build_weekly_digest(root: Path | None, run_id: str) -> WeeklyDigest:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / run_id
    tickers = []
    for path in sorted((run_dir / "raw" / "opportunity_assessment").glob("*_opportunity_assessment.json")):
        data = read_json(path)
        if data:
            tickers.append(build_ticker_digest(repo_root, run_id, data))
    open_review_count = count_open_review_items(repo_root)
    next_actions = build_next_actions(tickers, open_review_count, run_dir)
    quality_findings = validate_weekly_digest_tickers(repo_root, tickers)
    status = "ready"
    if quality_findings:
        status = "needs_review"
    if not tickers:
        status = "partial"
        next_actions.append("Run opportunity_assessment analysis tasks so the digest can include per-ticker expert opinions.")
    return WeeklyDigest(
        run_id=run_id,
        status=status,
        ticker_count=len(tickers),
        open_review_count=open_review_count,
        tickers=tickers,
        next_actions=unique(next_actions),
        quality_findings=quality_findings,
    )


def build_ticker_digest(root: Path, run_id: str, assessment: dict[str, Any]) -> dict[str, Any]:
    ticker = str(assessment.get("ticker", "")).upper()
    return {
        "ticker": ticker,
        "status": assessment.get("status", ""),
        "opportunity_view": assessment.get("opportunity_view", ""),
        "opportunity_score": assessment.get("opportunity_score", ""),
        "risk_level": assessment.get("risk_level", ""),
        "confidence": assessment.get("confidence", ""),
        "thesis_freshness": assessment.get("thesis_freshness", ""),
        "summary": assessment.get("summary", ""),
        "top_positives": list(assessment.get("positives") or [])[:3],
        "top_negatives": list(assessment.get("negatives") or [])[:3],
        "watch_items": list(assessment.get("watch_items") or [])[:4],
        "financial_snapshot": concise_financial_snapshot(assessment.get("financial_snapshot") or {}),
        "news_snapshot": concise_news_snapshot(assessment.get("news_snapshot") or {}),
        "social_snapshot": concise_social_snapshot(assessment.get("social_snapshot") or {}),
        "filing_snapshot": concise_filing_snapshot(assessment.get("filing_snapshot") or {}),
        "report_path": relative_to_root(
            root,
            root / "agents" / "runs" / run_id / "reports" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.md",
        ).as_posix(),
        "evidence_links": build_ticker_evidence_links(root, run_id, ticker),
        "recommended_next_action": assessment.get("recommended_next_action", ""),
    }


def build_ticker_evidence_links(root: Path, run_id: str, ticker: str) -> dict[str, str]:
    run_dir = root / "agents" / "runs" / run_id
    candidates = {
        "opportunity_report": run_dir / "reports" / "opportunity_assessment" / f"{ticker}_opportunity_assessment.md",
        "financial_review": run_dir / "reports" / "financial_data_specialist" / f"{ticker}_financial_review.md",
        "company_news_review": run_dir / "reports" / "company_news_specialist" / f"{ticker}_company_news_review.md",
        "company_research": run_dir / "company_research" / f"{ticker}_company_research.md",
    }
    return {key: relative_to_root(root, path).as_posix() for key, path in candidates.items() if path.exists()}


def concise_financial_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status", "missing"),
        "latest_price": value.get("latest_price"),
        "market_cap": value.get("market_cap"),
        "pe_ratio": value.get("pe_ratio"),
        "forward_pe": value.get("forward_pe"),
        "analyst_target_price": value.get("analyst_target_price"),
        "analyst_target_implied_upside": value.get("analyst_target_implied_upside"),
        "price_to_sales_ttm": value.get("price_to_sales_ttm"),
        "profit_margin": value.get("profit_margin"),
        "free_cash_flow_per_share_ttm": value.get("free_cash_flow_per_share_ttm"),
        "currency": value.get("currency"),
        "conflict_count": value.get("conflict_count", 0),
    }


def concise_news_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status", "missing"),
        "source_count": value.get("source_count", 0),
        "contents_claim_count": value.get("contents_claim_count", 0),
        "material_developments": list(value.get("material_developments") or [])[:4],
        "remaining_content_follow_up_count": value.get("remaining_content_follow_up_count", 0),
    }


def concise_social_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status", "missing"),
        "sentiment": value.get("sentiment", "missing"),
        "citation_count": value.get("citation_count", 0),
        "rumor_flag": value.get("rumor_flag", False),
        "x_pulse": value.get("x_pulse", ""),
        "bullish_claims": list(value.get("bullish_claims") or [])[:3],
        "bearish_claims": list(value.get("bearish_claims") or [])[:3],
        "news_reactions": list(value.get("news_reactions") or [])[:3],
        "notable_accounts": list(value.get("notable_accounts") or [])[:5],
        "hype_noise": value.get("hype_noise", ""),
        "investor_implications": list(value.get("investor_implications") or [])[:3],
    }


def concise_filing_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status", "missing"),
        "packet_count": value.get("packet_count", 0),
        "unknown_count": value.get("unknown_count", 0),
    }


def write_weekly_digest(root: Path | None, digest: WeeklyDigest) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / digest.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "final_digest.json"
    md_path = run_dir / "final_digest.md"
    json_path.write_text(json.dumps(weekly_digest_to_dict(digest), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_weekly_digest_markdown(digest), encoding="utf-8")
    return json_path, md_path


def weekly_digest_to_dict(digest: WeeklyDigest) -> dict[str, Any]:
    return {
        "run_id": digest.run_id,
        "status": digest.status,
        "ticker_count": digest.ticker_count,
        "open_review_count": digest.open_review_count,
        "tickers": digest.tickers,
        "next_actions": digest.next_actions,
        "quality_findings": digest.quality_findings,
    }


def format_weekly_digest_markdown(digest: WeeklyDigest) -> str:
    lines = [
        f"# Final Research Digest: {digest.run_id}",
        "",
        f"Status: {digest.status}",
        f"Tickers assessed: {digest.ticker_count}",
        f"Open human-review items: {digest.open_review_count}",
        "",
    ]
    if not digest.tickers:
        lines.extend(["## Company Assessments", "", "- No opportunity assessments were available."])
    for item in digest.tickers:
        lines.extend(
            [
                f"## {item['ticker']}",
                "",
                f"- opportunity_view: {item['opportunity_view']}",
                f"- opportunity_score: {item['opportunity_score']}/100",
                f"- risk_level: {item['risk_level']}",
                f"- confidence: {item['confidence']}",
                f"- thesis_freshness: {item['thesis_freshness']}",
                f"- report: `{item['report_path']}`",
                "",
                "### Evidence Links",
                "",
            ]
        )
        evidence_links = item.get("evidence_links") or {}
        if evidence_links:
            for label, path in evidence_links.items():
                lines.append(f"- {label}: `{path}`")
        else:
            lines.append("- No direct evidence links available.")
        lines.extend(
            [
                "",
                "### Expert Opinion",
                "",
                digest_text(str(item["summary"]), 900),
                "",
                "### Financial Facts",
                "",
            ]
        )
        for key, value in item["financial_snapshot"].items():
            lines.append(f"- {key}: {format_financial_value(key, value)}")
        lines.extend(["", "### News / Trends / Sentiment", ""])
        news = item["news_snapshot"]
        social = item["social_snapshot"]
        filing = item["filing_snapshot"]
        if news.get("material_developments"):
            lines.append("- Source-backed developments:")
            for development in news["material_developments"][:3]:
                claim_text = development.get("claim") if isinstance(development, dict) else str(development)
                lines.append(f"  - {digest_text(claim_text, 700)}")
        else:
            lines.append("- Source-backed developments: none extracted.")
        lines.append(f"- Grok/X pulse: {digest_text(social.get('x_pulse') or social['sentiment'], 700)}")
        if social.get("bullish_claims"):
            lines.append("- X bull case:")
            lines.extend(f"  - {digest_text(value, 700)}" for value in social["bullish_claims"][:2])
        if social.get("bearish_claims"):
            lines.append("- X bear/skeptic case:")
            lines.extend(f"  - {digest_text(value, 700)}" for value in social["bearish_claims"][:2])
        if social.get("notable_accounts"):
            lines.append(f"- Accounts/posts to review: {', '.join(social['notable_accounts'][:5])}")
        if social.get("hype_noise"):
            lines.append(f"- Hype/noise: {digest_text(social['hype_noise'], 700)}")
        lines.append(f"- Filing coverage: {filing['status']} ({filing['packet_count']} packet(s))")
        lines.extend(["", "### Positives", ""])
        lines.extend(f"- {digest_text(value, 700)}" for value in item["top_positives"])
        lines.extend(["", "### Risks / Cautions", ""])
        lines.extend(f"- {digest_text(value, 700)}" for value in item["top_negatives"])
        lines.extend(["", "### Next Research Checks", ""])
        user_checks = [value for value in item["watch_items"] if not str(value).startswith("Extract remaining high-value Exa")]
        lines.extend(f"- {digest_text(value, 700)}" for value in (user_checks or ["No high-priority human research check surfaced in this digest."]))
        lines.extend(["", "### Recommended Next Action", "", f"- {item['recommended_next_action']}", ""])
    lines.extend(["## Run-Level Next Actions", ""])
    if digest.next_actions:
        lines.extend(f"- {item}" for item in digest.next_actions)
    else:
        lines.append("- None.")
    if digest.quality_findings:
        lines.extend(["", "## Digest Quality Findings", ""])
        lines.extend(f"- {item}" for item in digest.quality_findings)
    return "\n".join(lines).rstrip() + "\n"


def validate_weekly_digest_tickers(root: Path, tickers: list[dict[str, Any]]) -> list[str]:
    findings: list[str] = []
    for item in tickers:
        ticker = str(item.get("ticker", "unknown"))
        report_path = str(item.get("report_path", ""))
        if not report_path or not (root / report_path).exists():
            findings.append(f"{ticker} digest is missing an existing opportunity report path.")
        evidence_links = item.get("evidence_links") or {}
        required_links = {"opportunity_report", "financial_review", "company_news_review"}
        missing_links = sorted(required_links - set(evidence_links))
        if missing_links:
            findings.append(f"{ticker} digest is missing evidence links: {', '.join(missing_links)}.")
        for label, path in evidence_links.items():
            if not (root / str(path)).exists():
                findings.append(f"{ticker} digest evidence link does not exist for {label}: {path}")
        if item.get("financial_snapshot", {}).get("status") == "missing":
            findings.append(f"{ticker} digest is missing financial review status.")
        if item.get("news_snapshot", {}).get("status") == "missing":
            findings.append(f"{ticker} digest is missing company-news review status.")
        social = item.get("social_snapshot", {})
        if social.get("status") == "available" and not str(social.get("sentiment", "")).endswith("_social_signal"):
            findings.append(f"{ticker} Grok/X sentiment must be labeled as a social signal.")
        if social.get("status") == "available" and not social.get("x_pulse"):
            findings.append(f"{ticker} digest is missing an actionable Grok/X pulse narrative.")
        if social.get("status") == "available" and not (social.get("bullish_claims") or social.get("bearish_claims")):
            findings.append(f"{ticker} digest is missing concrete Grok/X bullish or bearish claims.")
        if item.get("news_snapshot", {}).get("status") != "missing" and not item.get("news_snapshot", {}).get("material_developments"):
            findings.append(f"{ticker} digest is missing concrete source-backed news developments.")
        if contains_direct_trade_language(str(item.get("summary", ""))):
            findings.append(f"{ticker} digest summary contains direct trade language.")
        if contains_direct_trade_language(str(item.get("recommended_next_action", ""))):
            findings.append(f"{ticker} recommended next action contains direct trade language.")
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


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def count_open_review_items(root: Path) -> int:
    from .human_review_digest import build_human_review_digest

    return build_human_review_digest(root=root).open_item_count


def build_next_actions(tickers: list[dict[str, Any]], open_review_count: int, run_dir: Path) -> list[str]:
    actions: list[str] = []
    if open_review_count:
        actions.append("Review `agents/human_review_digest.md` for pending approval/reject/more-research decisions.")
    for item in tickers:
        if item.get("risk_level") == "high":
            actions.append(f"Resolve high-risk review gates for {item['ticker']} before updating the thesis.")
        if item.get("confidence") == "low":
            actions.append(f"Gather missing evidence lanes for {item['ticker']} before relying on the assessment.")
    if (run_dir / "agent_runtime_main_orchestrator.md").exists():
        data = read_json(run_dir / "agent_runtime_main_orchestrator.json")
        if data.get("status") == "blocked":
            actions.append("Main SDK orchestrator was blocked; use this deterministic digest until the model runtime is available.")
    return actions


def unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def format_value(value: Any) -> str:
    return format_plain_value(value)


def digest_text(value: Any, limit: int) -> str:
    text = re.sub(r"\[\[\d+\]\]\([^)]+\)", "", str(value))
    text = re.sub(r"(?<!\w)\[(\d+)\](?!\w)", "", text)
    return compact_complete_text(text, limit)
