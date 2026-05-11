from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .memory import relative_to_root
from .repo import find_repo_root


@dataclass(frozen=True)
class WeeklyDigest:
    run_id: str
    status: str
    ticker_count: int
    open_review_count: int
    tickers: list[dict[str, Any]]
    next_actions: list[str]


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
    status = "ready"
    if any(item.get("risk_level") == "high" or item.get("confidence") == "low" for item in tickers):
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
        "recommended_next_action": assessment.get("recommended_next_action", ""),
    }


def concise_financial_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status", "missing"),
        "latest_price": value.get("latest_price"),
        "market_cap": value.get("market_cap"),
        "pe_ratio": value.get("pe_ratio"),
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
        "remaining_content_follow_up_count": value.get("remaining_content_follow_up_count", 0),
    }


def concise_social_snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": value.get("status", "missing"),
        "sentiment": value.get("sentiment", "missing"),
        "citation_count": value.get("citation_count", 0),
        "rumor_flag": value.get("rumor_flag", False),
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
    }


def format_weekly_digest_markdown(digest: WeeklyDigest) -> str:
    lines = [
        f"# Final Research Digest: {digest.run_id}",
        "",
        f"Status: {digest.status}",
        f"Tickers assessed: {digest.ticker_count}",
        f"Open human-review items: {digest.open_review_count}",
        "",
        "This digest is a concise review surface. It is not an automatic trading instruction.",
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
                "### Expert Opinion",
                "",
                str(item["summary"]),
                "",
                "### Financial Facts",
                "",
            ]
        )
        for key, value in item["financial_snapshot"].items():
            lines.append(f"- {key}: {format_value(value)}")
        lines.extend(["", "### News / Trends / Sentiment", ""])
        news = item["news_snapshot"]
        social = item["social_snapshot"]
        filing = item["filing_snapshot"]
        lines.append(
            f"- news: {news['status']} ({news['source_count']} source(s), {news['contents_claim_count']} contents claim(s))"
        )
        lines.append(
            f"- Grok/X social signal: {social['sentiment']} ({social['citation_count']} citation(s), rumor_flag={social['rumor_flag']})"
        )
        lines.append(f"- filings: {filing['status']} ({filing['packet_count']} packet(s))")
        lines.extend(["", "### Positives", ""])
        lines.extend(f"- {value}" for value in item["top_positives"])
        lines.extend(["", "### Risks / Cautions", ""])
        lines.extend(f"- {value}" for value in item["top_negatives"])
        lines.extend(["", "### Watch Items", ""])
        lines.extend(f"- {value}" for value in item["watch_items"])
        lines.extend(["", "### Recommended Next Action", "", f"- {item['recommended_next_action']}", ""])
    lines.extend(["## Run-Level Next Actions", ""])
    if digest.next_actions:
        lines.extend(f"- {item}" for item in digest.next_actions)
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def count_open_review_items(root: Path) -> int:
    queue = root / "agents" / "human_review_queue.md"
    if not queue.exists():
        return 0
    count = 0
    for line in queue.read_text(encoding="utf-8").splitlines():
        if "| open |" in line.lower() or "| needs_more_research |" in line.lower():
            count += 1
    return count


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
    if value is None:
        return "unknown"
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)
