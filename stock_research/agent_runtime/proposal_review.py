from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.context import build_research_run_context
from stock_research.agent_runtime.reports import evaluate_runtime_output_quality, output_to_dict, output_status
from stock_research.markdown_edit import append_markdown_table_row
from stock_research.repo import find_repo_root, load_first_table


@dataclass(frozen=True)
class ProposalReviewResult:
    run_id: str
    generated_at: str
    status: str
    proposals: list[dict[str, Any]] = field(default_factory=list)
    review_items: list[dict[str, Any]] = field(default_factory=list)
    quality_findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def build_proposal_review(
    *,
    root: Path | None = None,
    run_id: str,
    agent_id: str = "main_orchestrator",
    current_date: date | None = None,
    write: bool = False,
    queue_review: bool = False,
) -> ProposalReviewResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    context = build_research_run_context(root=repo_root, run_id=run_id, task="main orchestrator")
    output_path = context.run_dir / f"agent_runtime_{agent_id}.json"
    if not output_path.exists():
        raise FileNotFoundError(f"Missing runtime output: {output_path}")

    output = json.loads(output_path.read_text(encoding="utf-8"))
    quality_findings = evaluate_runtime_output_quality(output, context)
    runtime_status = output_status(output)
    proposals = collect_file_update_proposals(output)
    review_items = collect_human_review_items(output)
    status = proposal_review_status(runtime_status, quality_findings, proposals, review_items)
    written_paths: list[str] = []

    if write:
        report_path = write_proposal_review_markdown(
            repo_root=repo_root,
            run_id=run_id,
            generated_at=today,
            status=status,
            proposals=proposals,
            review_items=review_items,
            quality_findings=quality_findings,
        )
        written_paths.append(report_path.relative_to(repo_root).as_posix())
        if queue_review:
            human_review_path = append_proposals_to_human_review_queue(
                repo_root=repo_root,
                run_id=run_id,
                generated_at=today,
                proposals=proposals,
                review_items=review_items,
                report_path=report_path,
            )
            written_paths.append(human_review_path.relative_to(repo_root).as_posix())

    return ProposalReviewResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=status,
        proposals=proposals,
        review_items=review_items,
        quality_findings=quality_findings,
        written_paths=dedupe(written_paths),
    )


def collect_file_update_proposals(output: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for index, proposal in enumerate(output.get("file_update_proposals") or [], start=1):
        if not isinstance(proposal, dict):
            continue
        target_file = normalize_ascii(str(proposal.get("target_file", "")).strip())
        update_type = normalize_ascii(str(proposal.get("update_type", "")).strip())
        summary = normalize_ascii(str(proposal.get("summary", "")).strip())
        key = (target_file, update_type, summary)
        if key in seen:
            continue
        seen.add(key)
        proposals.append(
            {
                "proposal_id": f"ORP-{index:04d}",
                "target_file": target_file,
                "update_type": update_type,
                "summary": summary,
                "confidence": normalize_ascii(str(proposal.get("confidence", "medium"))),
                "source_ids": [str(source_id) for source_id in proposal.get("source_ids") or []],
                "needs_human_review": bool(proposal.get("needs_human_review", True)),
            }
        )
    return proposals


def collect_human_review_items(output: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for index, item in enumerate(output.get("human_review_items") or [], start=1):
        if not isinstance(item, dict):
            continue
        items.append(
            {
                "review_item_id": f"ORI-{index:04d}",
                "title": normalize_ascii(str(item.get("title", "")).strip()),
                "question": normalize_ascii(str(item.get("question", "")).strip()),
                "reason": normalize_ascii(str(item.get("reason", "")).strip()),
                "priority": normalize_ascii(str(item.get("priority", "medium")).strip() or "medium"),
                "source_ids": [str(source_id) for source_id in item.get("source_ids") or []],
            }
        )
    return items


def proposal_review_status(
    runtime_status: str,
    quality_findings: list[str],
    proposals: list[dict[str, Any]],
    review_items: list[dict[str, Any]],
) -> str:
    if quality_findings or runtime_status != "ready":
        return "needs_review"
    if proposals or review_items:
        return "ready_for_human_review"
    return "no_proposals"


def write_proposal_review_markdown(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    status: str,
    proposals: list[dict[str, Any]],
    review_items: list[dict[str, Any]],
    quality_findings: list[str],
) -> Path:
    run_dir = repo_root / "agents" / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / "orchestrator_update_proposals.md"
    lines = [
        f"# Orchestrator Update Proposals: {run_id}",
        "",
        f"Generated: {generated_at.isoformat()}",
        f"Status: {status}",
        "",
        "## Purpose",
        "",
        "This file converts SDK orchestrator output into reviewable proposals. It does not apply edits to stock files.",
        "",
        "## Quality Findings",
        "",
    ]
    if quality_findings:
        for finding in quality_findings:
            lines.append(f"- {finding}")
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## File Update Proposals",
            "",
            "| Proposal ID | Target File | Update Type | Confidence | Needs Human Review | Source IDs | Summary |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if proposals:
        for proposal in proposals:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        proposal["proposal_id"],
                        proposal["target_file"],
                        proposal["update_type"],
                        proposal["confidence"],
                        "yes" if proposal["needs_human_review"] else "no",
                        ", ".join(proposal["source_ids"]),
                        proposal["summary"],
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  |  |  | No file update proposals. |")
    lines.extend(
        [
            "",
            "## Human Review Items",
            "",
            "| Review Item ID | Title | Question | Priority | Source IDs | Reason |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if review_items:
        for item in review_items:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        item["review_item_id"],
                        item["title"],
                        item["question"],
                        item["priority"],
                        ", ".join(item["source_ids"]),
                        item["reason"],
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  |  | No explicit human review items. |")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return path


def append_proposals_to_human_review_queue(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    proposals: list[dict[str, Any]],
    review_items: list[dict[str, Any]],
    report_path: Path,
) -> Path:
    path = repo_root / "agents" / "human_review_queue.md"
    ensure_human_review_queue(path)
    existing_evidence = {row.get("Evidence / Run Link", "") for row in load_first_table(path)}
    next_id = next_human_review_id(path)

    for proposal in proposals:
        evidence = f"{report_path.relative_to(repo_root).as_posix()}#{proposal['proposal_id']}"
        if evidence in existing_evidence:
            continue
        row = [
            next_id,
            generated_at.isoformat(),
            f"Review SDK file update proposal {proposal['proposal_id']} for {proposal['target_file']}.",
            "Approve, reject, or request more research before any company-file writer applies this update.",
            "medium" if proposal["confidence"] != "low" else "low",
            "open",
            proposal["target_file"],
            evidence,
            proposal["summary"],
        ]
        append_markdown_table_row(path, "| ID | Date Added | Item |", [normalize_ascii(value) for value in row])
        existing_evidence.add(evidence)
        next_id = increment_human_review_id(next_id)

    for item in review_items:
        evidence = f"{report_path.relative_to(repo_root).as_posix()}#{item['review_item_id']}"
        if evidence in existing_evidence:
            continue
        row = [
            next_id,
            generated_at.isoformat(),
            item["title"] or f"Review SDK item {item['review_item_id']}.",
            item["question"] or "Review the orchestrator item and decide next action.",
            item["priority"],
            "open",
            "agents/runs/" + run_id,
            evidence,
            item["reason"],
        ]
        append_markdown_table_row(path, "| ID | Date Added | Item |", [normalize_ascii(value) for value in row])
        existing_evidence.add(evidence)
        next_id = increment_human_review_id(next_id)

    return path


def ensure_human_review_queue(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "## Review Items",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def next_human_review_id(path: Path) -> str:
    max_number = 0
    for row in load_first_table(path):
        value = row.get("ID", "")
        if value.startswith("HRQ-"):
            try:
                max_number = max(max_number, int(value.removeprefix("HRQ-")))
            except ValueError:
                continue
    return f"HRQ-{max_number + 1:04d}"


def increment_human_review_id(value: str) -> str:
    try:
        return f"HRQ-{int(value.removeprefix('HRQ-')) + 1:04d}"
    except ValueError:
        return "HRQ-0001"


def proposal_review_to_dict(result: ProposalReviewResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "generated_at": result.generated_at,
        "status": result.status,
        "proposals": result.proposals,
        "review_items": result.review_items,
        "quality_findings": result.quality_findings,
        "written_paths": result.written_paths,
    }


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()


def normalize_ascii(value: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u00a0": " ",
    }
    for old, new in replacements.items():
        value = value.replace(old, new)
    return value


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
