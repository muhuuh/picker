from __future__ import annotations

from dataclasses import asdict
import csv
import json
from pathlib import Path
from typing import Any

from agents import Agent

from stock_research.agent_runtime.context import ResearchRunContext, with_task_memory
from stock_research.agent_runtime.outputs import OrchestratorDecision, PortfolioBucketReview, PortfolioReviewPacket
from stock_research.agent_runtime.prompts import load_prompt, with_memory
from stock_research.agent_runtime.reports import output_to_dict
from stock_research.agent_runtime.specialists.quality_review import build_agent as build_quality_review_agent
from stock_research.agent_runtime.tools.repo_tools import repo_tools
from stock_research.repo import STOCK_TABLES, read_csv_table


FALLBACK_PROMPT = """
You are the portfolio review sub-orchestrator.

Review current holdings, monitoring names, rejected cooldowns, open human-review items, and recent run artifacts.
Do not make automatic trade decisions. Produce source-backed alerts, human-review items, and next-run tasks.
Treat candidate verification results as research inputs, not as automatic monitoring or buy decisions.
"""


def build_agent(context: ResearchRunContext | None = None) -> Agent[ResearchRunContext]:
    root = context.root if context else None
    prompt = FALLBACK_PROMPT if root is None else load_prompt(root, "agents/orchestrator/prompts/portfolio_review.md", FALLBACK_PROMPT)
    if context:
        prompt = with_memory(prompt, context.memory_context)

    quality_context = with_task_memory(context, "quality reviewer specialist") if context else None
    quality_agent = build_quality_review_agent(quality_context)
    return Agent[ResearchRunContext](
        name="Portfolio Review Orchestrator",
        instructions=prompt,
        handoff_description="Reviews portfolio/watchlist state, approvals, cooldowns, and next actions.",
        output_type=OrchestratorDecision,
        tools=[
            *repo_tools(),
            quality_agent.as_tool(
                tool_name="quality_reviewer_specialist",
                tool_description="Review portfolio review output quality, citations, stale state, and approval gates.",
            ),
        ],
    )


def build_portfolio_review_packet(context: ResearchRunContext) -> PortfolioReviewPacket:
    review_rows = load_human_review_rows(context.root / "agents" / "human_review_queue.md")
    open_review_ids = [
        row.get("ID", "")
        for row in review_rows
        if str(row.get("Status", "")).lower() in {"open", "needs_more_research"}
    ]
    approved_review_ids = [
        row.get("ID", "")
        for row in review_rows
        if str(row.get("Status", "")).lower() == "approved"
    ]
    buckets = [build_bucket_review(context, bucket, relative_path, review_rows) for bucket, relative_path in STOCK_TABLES.items()]
    return PortfolioReviewPacket(
        run_id=context.run_id,
        buckets=buckets,
        open_human_review_count=len(open_review_ids),
        approved_human_review_count=len(approved_review_ids),
        rejected_cooldown_count=count_rejected_cooldowns(context.root),
        candidate_verification_results=latest_candidate_verification_results(context.run_dir),
        latest_run_artifacts=latest_review_artifacts(context.run_dir),
        memory_item_ids=list(context.memory_item_ids),
    )


def build_portfolio_review_input(context: ResearchRunContext) -> str:
    packet = build_portfolio_review_packet(context)
    return "\n".join(
        [
            f"Review portfolio/watchlist state for run `{packet.run_id}`.",
            "",
            "Use the portfolio review packet below as the deterministic starting point.",
            "Focus on current holdings, monitoring names, rejected cooldowns, open approvals, stale records, and recent candidate verification results.",
            "Return a structured OrchestratorDecision with alerts, human review items, and next-run tasks.",
            "Do not make automatic buy/sell/position-size decisions.",
            "",
            "Portfolio review packet:",
            "```json",
            json.dumps(asdict(packet), indent=2, sort_keys=True),
            "```",
        ]
    )


def aggregate_portfolio_review(context: ResearchRunContext) -> OrchestratorDecision:
    packet = build_portfolio_review_packet(context)
    missing_files = [
        ticker
        for bucket in packet.buckets
        for ticker in bucket.missing_company_files
    ]
    stale_tickers = [
        ticker
        for bucket in packet.buckets
        for ticker in bucket.stale_tickers
    ]
    status = "ready"
    next_tasks: list[str] = []
    if stale_tickers or missing_files or packet.open_human_review_count:
        status = "partial"
    if missing_files:
        next_tasks.append("Create or repair missing company files: " + ", ".join(sorted(missing_files)) + ".")
    if stale_tickers:
        next_tasks.append("Refresh stale stock tracking rows: " + ", ".join(sorted(stale_tickers)) + ".")
    if packet.open_human_review_count:
        next_tasks.append("Review open HRQ items before applying proposals, candidate verification, or stock status moves.")
    if packet.candidate_verification_results:
        next_tasks.append("Inspect candidate verification result reports before any monitoring promotion decision.")
    summary = (
        f"Portfolio review covers {sum(bucket.row_count for bucket in packet.buckets)} tracked row(s), "
        f"{packet.open_human_review_count} open review item(s), {packet.approved_human_review_count} approved review item(s), "
        f"and {packet.rejected_cooldown_count} rejected cooldown row(s)."
    )
    return OrchestratorDecision(
        agent_id="portfolio_review_orchestrator",
        run_id=context.run_id,
        status=status,
        summary=summary,
        next_run_tasks=next_tasks,
        memory_item_ids_used=list(context.memory_item_ids),
    )


def portfolio_review_result_to_dict(decision: OrchestratorDecision, packet: PortfolioReviewPacket) -> dict[str, Any]:
    return {
        "decision": output_to_dict(decision),
        "packet": asdict(packet),
    }


def write_portfolio_review_report(context: ResearchRunContext, decision: OrchestratorDecision | None = None) -> tuple[Path, Path]:
    packet = build_portfolio_review_packet(context)
    resolved_decision = decision or aggregate_portfolio_review(context)
    target_dir = context.run_dir / "portfolio_review"
    target_dir.mkdir(parents=True, exist_ok=True)
    json_path = target_dir / "portfolio_review.json"
    md_path = target_dir / "portfolio_review.md"
    json_path.write_text(json.dumps(portfolio_review_result_to_dict(resolved_decision, packet), indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(format_portfolio_review_markdown(packet, resolved_decision), encoding="utf-8")
    return json_path, md_path


def format_portfolio_review_markdown(packet: PortfolioReviewPacket, decision: OrchestratorDecision) -> str:
    lines = [
        f"# Portfolio Review: {packet.run_id}",
        "",
        f"Status: {decision.status}",
        "",
        "## Summary",
        "",
        decision.summary,
        "",
        "## Buckets",
        "",
        "| Bucket | Rows | Tickers | Stale | Missing Company Files | Open Review IDs |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for bucket in packet.buckets:
        lines.append(
            "| "
            + " | ".join(
                escape_cell(value)
                for value in [
                    bucket.bucket,
                    bucket.row_count,
                    ", ".join(bucket.tickers) or "none",
                    ", ".join(bucket.stale_tickers) or "none",
                    ", ".join(bucket.missing_company_files) or "none",
                    ", ".join(bucket.open_review_ids) or "none",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Review Queue",
            "",
            f"- Open items: {packet.open_human_review_count}",
            f"- Approved items: {packet.approved_human_review_count}",
            f"- Rejected cooldown rows: {packet.rejected_cooldown_count}",
            "",
            "## Candidate Verification Results",
            "",
        ]
    )
    if packet.candidate_verification_results:
        lines.extend(f"- `{path}`" for path in packet.candidate_verification_results)
    else:
        lines.append("- None found for this run.")
    lines.extend(["", "## Next Run Tasks", ""])
    if decision.next_run_tasks:
        lines.extend(f"- {task}" for task in decision.next_run_tasks)
    else:
        lines.append("- None.")
    return "\n".join(lines).rstrip() + "\n"


def build_bucket_review(
    context: ResearchRunContext,
    bucket: str,
    relative_path: Path,
    review_rows: list[dict[str, str]],
) -> PortfolioBucketReview:
    table = read_csv_table(context.root / relative_path)
    tickers = [ticker_from_row(row) for row in table.rows if ticker_from_row(row)]
    stale = [ticker_from_row(row) for row in table.rows if ticker_from_row(row) and row_is_stale(row)]
    missing_files = [
        ticker_from_row(row)
        for row in table.rows
        if ticker_from_row(row) and company_file_missing(context.root, row)
    ]
    review_ids = matching_open_review_ids(bucket, tickers, review_rows)
    notes: list[str] = []
    if bucket == "rejected":
        notes.append("Rejected rows remain blocked until cooldown expires or user explicitly overrides.")
    return PortfolioBucketReview(
        bucket=bucket,
        row_count=len(table.rows),
        tickers=tickers,
        stale_tickers=stale,
        missing_company_files=missing_files,
        open_review_ids=review_ids,
        notes=notes,
    )


def ticker_from_row(row: dict[str, str]) -> str:
    return (row.get("ticker") or row.get("symbol") or row.get("stock_abr") or row.get("abr") or "").strip().upper()


def row_is_stale(row: dict[str, str]) -> bool:
    value = row.get("date_last_updated", "").strip()
    return not value


def company_file_missing(root: Path, row: dict[str, str]) -> bool:
    file_value = row.get("stock_info_file", "").strip()
    if not file_value:
        return False
    return not (root / file_value).exists()


def matching_open_review_ids(bucket: str, tickers: list[str], review_rows: list[dict[str, str]]) -> list[str]:
    ticker_set = {ticker.upper() for ticker in tickers}
    ids: list[str] = []
    for row in review_rows:
        if str(row.get("Status", "")).lower() not in {"open", "needs_more_research"}:
            continue
        text = " ".join(str(row.get(key, "")) for key in ("Item", "Decision Needed", "Related Files", "Notes"))
        bucket_path_match = f"stock_tracking/{bucket}" in text or f"stock_info_files/{bucket}" in text
        ticker_match = any(ticker and ticker in text.upper() for ticker in ticker_set)
        if bucket_path_match or ticker_match:
            ids.append(row.get("ID", ""))
    return ids


def load_human_review_rows(path: Path) -> list[dict[str, str]]:
    from stock_research.repo import load_first_table

    return load_first_table(path)


def count_rejected_cooldowns(root: Path) -> int:
    table = read_csv_table(root / STOCK_TABLES["rejected"])
    return sum(1 for row in table.rows if row.get("next_eligible_review_date", "").strip())


def latest_candidate_verification_results(run_dir: Path) -> list[str]:
    return [
        path.relative_to(run_dir.parents[2]).as_posix()
        for path in sorted((run_dir / "market_research").glob("candidate_verification_result.md"))
    ] if (run_dir / "market_research").exists() else []


def latest_review_artifacts(run_dir: Path) -> list[str]:
    candidates = [
        run_dir / "run_summary.md",
        run_dir / "quality_report.md",
        run_dir / "orchestration_report.md",
        run_dir / "agent_runtime_main_orchestrator.md",
    ]
    return [path.relative_to(run_dir.parents[2]).as_posix() for path in candidates if path.exists()]


def escape_cell(value: Any) -> str:
    return str(value).replace("|", "/").replace("\n", " ").strip()
