from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.markdown_edit import append_markdown_table_row
from stock_research.repo import find_repo_root, load_first_table


PROPOSAL_REPORT = "orchestrator_update_proposals.md"
APPLICATION_REPORT = "applied_update_proposals.md"


@dataclass(frozen=True)
class ProposalApplyResult:
    run_id: str
    proposal_id: str
    generated_at: str
    status: str
    target_file: str = ""
    update_type: str = ""
    summary: str = ""
    review_item_id: str = ""
    review_status: str = ""
    findings: list[str] = field(default_factory=list)
    planned_changes: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def apply_approved_proposal(
    *,
    root: Path | None = None,
    run_id: str,
    proposal_id: str,
    current_date: date | None = None,
    write: bool = False,
) -> ProposalApplyResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    proposal_id = normalize_ascii(proposal_id.strip())
    proposal_path = repo_root / "agents" / "runs" / run_id / PROPOSAL_REPORT
    if not proposal_path.exists():
        return blocked_result(run_id, proposal_id, today, [f"Missing proposal report: {proposal_path.relative_to(repo_root).as_posix()}"])

    proposal = find_proposal(proposal_path, proposal_id)
    if proposal is None:
        return blocked_result(run_id, proposal_id, today, [f"Proposal id not found: {proposal_id}"])

    target_file = normalize_ascii(proposal.get("Target File", ""))
    update_type = normalize_ascii(proposal.get("Update Type", ""))
    summary = normalize_ascii(proposal.get("Summary", ""))
    confidence = normalize_ascii(proposal.get("Confidence", "medium") or "medium")
    source_ids = normalize_ascii(proposal.get("Source IDs", ""))
    target_path, target_findings = resolve_target_path(repo_root, target_file)
    if target_findings:
        return ProposalApplyResult(
            run_id=run_id,
            proposal_id=proposal_id,
            generated_at=today.isoformat(),
            status="blocked",
            target_file=target_file,
            update_type=update_type,
            summary=summary,
            findings=target_findings,
        )

    review_path = repo_root / "agents" / "human_review_queue.md"
    review_item = find_matching_review_item(review_path, proposal_path, repo_root, proposal_id)
    if review_item is None:
        return ProposalApplyResult(
            run_id=run_id,
            proposal_id=proposal_id,
            generated_at=today.isoformat(),
            status="blocked",
            target_file=target_file,
            update_type=update_type,
            summary=summary,
            findings=["No matching human-review queue row exists for this proposal."],
        )

    review_status = normalize_ascii(review_item.get("Status", "")).lower()
    if review_status != "approved":
        return ProposalApplyResult(
            run_id=run_id,
            proposal_id=proposal_id,
            generated_at=today.isoformat(),
            status="blocked",
            target_file=target_file,
            update_type=update_type,
            summary=summary,
            review_item_id=review_item.get("ID", ""),
            review_status=review_status,
            findings=[f"Human-review item {review_item.get('ID', '')} is '{review_status or 'unknown'}', not 'approved'."],
        )

    if proposal_already_applied(target_path, proposal_id):
        return ProposalApplyResult(
            run_id=run_id,
            proposal_id=proposal_id,
            generated_at=today.isoformat(),
            status="already_applied",
            target_file=target_file,
            update_type=update_type,
            summary=summary,
            review_item_id=review_item.get("ID", ""),
            review_status=review_status,
            planned_changes=[],
        )

    planned_changes = planned_company_file_changes(update_type)
    written_paths: list[str] = []
    if write:
        apply_company_file_update(
            path=target_path,
            run_id=run_id,
            proposal_id=proposal_id,
            generated_at=today,
            update_type=update_type,
            summary=summary,
            confidence=confidence,
            source_ids=source_ids,
        )
        application_path = append_application_report(
            repo_root=repo_root,
            run_id=run_id,
            generated_at=today,
            proposal_id=proposal_id,
            target_file=target_file,
            update_type=update_type,
            confidence=confidence,
            review_item_id=review_item.get("ID", ""),
            summary=summary,
        )
        written_paths.extend([target_file, application_path.relative_to(repo_root).as_posix()])

    return ProposalApplyResult(
        run_id=run_id,
        proposal_id=proposal_id,
        generated_at=today.isoformat(),
        status="applied" if write else "ready_to_apply",
        target_file=target_file,
        update_type=update_type,
        summary=summary,
        review_item_id=review_item.get("ID", ""),
        review_status=review_status,
        planned_changes=planned_changes,
        written_paths=dedupe(written_paths),
    )


def find_proposal(proposal_path: Path, proposal_id: str) -> dict[str, str] | None:
    for row in load_first_table(proposal_path):
        if normalize_ascii(row.get("Proposal ID", "")) == proposal_id:
            return row
    return None


def find_matching_review_item(review_path: Path, proposal_path: Path, repo_root: Path, proposal_id: str) -> dict[str, str] | None:
    expected = f"{proposal_path.relative_to(repo_root).as_posix()}#{proposal_id}"
    for row in load_first_table(review_path):
        if normalize_ascii(row.get("Evidence / Run Link", "")) == expected:
            return row
    return None


def resolve_target_path(repo_root: Path, target_file: str) -> tuple[Path, list[str]]:
    if not target_file:
        return repo_root, ["Proposal target file is empty."]
    candidate = (repo_root / target_file).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError:
        return candidate, [f"Proposal target escapes repo root: {target_file}"]
    expected_root = (repo_root / "stock_tracking" / "stock_info_files").resolve()
    try:
        candidate.relative_to(expected_root)
    except ValueError:
        return candidate, [f"Proposal target is outside stock_info_files: {target_file}"]
    if not candidate.exists():
        return candidate, [f"Proposal target file does not exist: {target_file}"]
    if candidate.suffix.lower() != ".md":
        return candidate, [f"Proposal target is not a markdown file: {target_file}"]
    return candidate, []


def proposal_already_applied(path: Path, proposal_id: str) -> bool:
    return proposal_id in path.read_text(encoding="utf-8")


def planned_company_file_changes(update_type: str) -> list[str]:
    changes = ["update Last updated", "append Source Log row", "append Change Log row"]
    lowered = update_type.lower()
    if "news" in lowered or "development" in lowered:
        changes.append("append Developments row")
    elif "financial" in lowered:
        changes.append("append Financials bullet")
    else:
        changes.append("append Approved Proposal Updates bullet")
    return changes


def apply_company_file_update(
    *,
    path: Path,
    run_id: str,
    proposal_id: str,
    generated_at: date,
    update_type: str,
    summary: str,
    confidence: str,
    source_ids: str,
) -> None:
    proposal_ref = f"`agents/runs/{run_id}/{PROPOSAL_REPORT}#{proposal_id}`"
    text = path.read_text(encoding="utf-8")
    text = update_last_updated(text, generated_at)
    lowered = update_type.lower()
    if "news" in lowered or "development" in lowered:
        path.write_text(text, encoding="utf-8")
        ensure_table(
            path,
            "## Developments",
            "| Date | Development | Source | Impact | Confidence |",
            "| --- | --- | --- | --- | --- |",
        )
        append_markdown_table_row(
            path,
            "| Date | Development | Source |",
            [
                generated_at.isoformat(),
                f"{proposal_id}: {summary}",
                proposal_ref,
                "reviewed update proposal",
                confidence,
            ],
        )
    else:
        if "financial" in lowered:
            text = append_bullet_to_section(
                text,
                "## Financials",
                f"- {generated_at.isoformat()} ({proposal_id}): {summary} Sources: {proposal_ref}; source IDs: {source_ids or 'not specified'}.",
            )
        else:
            text = append_bullet_to_section(
                text,
                "## Approved Proposal Updates",
                f"- {generated_at.isoformat()} ({proposal_id}, {update_type}): {summary} Sources: {proposal_ref}; source IDs: {source_ids or 'not specified'}.",
            )
        path.write_text(text, encoding="utf-8")

    ensure_table(
        path,
        "## Source Log",
        "| Date accessed | Source | URL / artifact | Notes |",
        "| --- | --- | --- | --- |",
    )
    append_markdown_table_row(
        path,
        "| Date accessed | Source | URL / artifact |",
        [
            generated_at.isoformat(),
            f"SDK approved proposal {proposal_id}",
            proposal_ref,
            f"Update type: {update_type}; source IDs: {source_ids or 'not specified'}",
        ],
    )
    ensure_table(
        path,
        "## Change Log",
        "| Date | Updated by | Summary | Sources |",
        "| --- | --- | --- | --- |",
    )
    append_markdown_table_row(
        path,
        "| Date | Updated by | Summary |",
        [
            generated_at.isoformat(),
            "Codex approved proposal writer",
            f"Applied {proposal_id}: {summary}",
            proposal_ref,
        ],
    )


def update_last_updated(text: str, generated_at: date) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith("Last updated:"):
            lines[index] = f"Last updated: {generated_at.isoformat()}"
            return "\n".join(lines) + ("\n" if text.endswith("\n") else "")
    if lines and lines[0].startswith("# "):
        lines.insert(1, "")
        lines.insert(2, f"Last updated: {generated_at.isoformat()}")
        return "\n".join(lines) + "\n"
    return f"Last updated: {generated_at.isoformat()}\n\n{text}"


def ensure_table(path: Path, heading: str, header: str, separator: str) -> None:
    text = path.read_text(encoding="utf-8")
    if header in text:
        return
    lines = text.splitlines()
    heading_index = next((index for index, line in enumerate(lines) if line.strip() == heading), None)
    if heading_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([heading, "", header, separator])
    else:
        insert_index = heading_index + 1
        while insert_index < len(lines) and lines[insert_index].strip() == "":
            insert_index += 1
        lines[insert_index:insert_index] = ["", header, separator, ""]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def append_bullet_to_section(text: str, heading: str, bullet: str) -> str:
    lines = text.splitlines()
    heading_index = next((index for index, line in enumerate(lines) if line.strip() == heading), None)
    if heading_index is None:
        if lines and lines[-1].strip():
            lines.append("")
        lines.extend([heading, "", bullet])
        return "\n".join(lines) + "\n"

    insert_index = len(lines)
    for index in range(heading_index + 1, len(lines)):
        if lines[index].startswith("## "):
            insert_index = index
            break
    while insert_index > heading_index + 1 and lines[insert_index - 1].strip() == "":
        insert_index -= 1
    lines.insert(insert_index, bullet)
    return "\n".join(lines) + "\n"


def append_application_report(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    proposal_id: str,
    target_file: str,
    update_type: str,
    confidence: str,
    review_item_id: str,
    summary: str,
) -> Path:
    path = repo_root / "agents" / "runs" / run_id / APPLICATION_REPORT
    if not path.exists():
        path.write_text(
            "\n".join(
                [
                    f"# Applied Update Proposals: {run_id}",
                    "",
                    "## Applied Proposals",
                    "",
                    "| Date | Proposal ID | Human Review ID | Target File | Update Type | Confidence | Summary |",
                    "| --- | --- | --- | --- | --- | --- | --- |",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    existing = [
        row.get("Proposal ID", "")
        for row in load_first_table(path)
    ]
    if proposal_id not in existing:
        append_markdown_table_row(
            path,
            "| Date | Proposal ID | Human Review ID |",
            [
                generated_at.isoformat(),
                proposal_id,
                review_item_id,
                target_file,
                update_type,
                confidence,
                summary,
            ],
        )
    return path


def blocked_result(run_id: str, proposal_id: str, generated_at: date, findings: list[str]) -> ProposalApplyResult:
    return ProposalApplyResult(
        run_id=run_id,
        proposal_id=proposal_id,
        generated_at=generated_at.isoformat(),
        status="blocked",
        findings=findings,
    )


def proposal_apply_result_to_dict(result: ProposalApplyResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "proposal_id": result.proposal_id,
        "generated_at": result.generated_at,
        "status": result.status,
        "target_file": result.target_file,
        "update_type": result.update_type,
        "summary": result.summary,
        "review_item_id": result.review_item_id,
        "review_status": result.review_status,
        "findings": result.findings,
        "planned_changes": result.planned_changes,
        "written_paths": result.written_paths,
    }


def dedupe(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
