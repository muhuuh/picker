from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.candidate_followup import (
    CANDIDATE_REVIEW_REPORT,
    CANDIDATE_VERIFICATION_MANIFEST,
    candidate_group_id_from_evidence,
    load_candidate_groups,
    matching_human_review_rows,
)
from stock_research.evidence import EvidencePacket, read_packet
from stock_research.repo import find_repo_root


CANDIDATE_VERIFICATION_RESULT_JSON = "candidate_verification_result.json"
CANDIDATE_VERIFICATION_RESULT_MD = "candidate_verification_result.md"


@dataclass(frozen=True)
class TaskCheck:
    task_id: str
    lane: str
    provider_or_tool: str
    subject_id: str
    status: str
    artifact: str = ""
    detail: str = ""


@dataclass
class CandidateVerificationResultItem:
    review_item_id: str
    candidate_group_id: str
    candidate: str
    tickers: list[str] = field(default_factory=list)
    decision_kind: str = ""
    review_status: str = ""
    status: str = "blocked"
    provider_checks: list[TaskCheck] = field(default_factory=list)
    analysis_checks: list[TaskCheck] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateVerificationResult:
    run_id: str
    generated_at: str
    status: str
    review_ids: list[str] = field(default_factory=list)
    items: list[CandidateVerificationResultItem] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def build_candidate_verification_result(
    *,
    root: Path | None = None,
    run_id: str,
    review_id: str = "",
    current_date: date | None = None,
    write: bool = False,
) -> CandidateVerificationResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    market_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    manifest_path = market_dir / CANDIDATE_VERIFICATION_MANIFEST
    review_report_path = market_dir / CANDIDATE_REVIEW_REPORT
    findings: list[str] = []

    if not manifest_path.exists():
        return CandidateVerificationResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            findings=[f"Missing verification manifest: {manifest_path.relative_to(repo_root).as_posix()}"],
        )
    if not review_report_path.exists():
        return CandidateVerificationResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            findings=[f"Missing candidate review report: {review_report_path.relative_to(repo_root).as_posix()}"],
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    review_rows = matching_human_review_rows(repo_root, run_id, review_id)
    if review_id and not review_rows:
        return CandidateVerificationResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            findings=[f"No candidate-review human-review row found for review id: {review_id}"],
        )
    selected_rows = [row for row in review_rows if normalize_ascii(row.get("Status", "")).lower() == "approved"]
    if not selected_rows:
        return CandidateVerificationResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked" if review_id else "no_approved_items",
            review_ids=[row.get("ID", "") for row in review_rows],
            findings=["No approved candidate-review rows found."],
        )

    groups = load_candidate_groups(review_report_path)
    packets = load_evidence_packets(repo_root / "agents" / "runs" / run_id / "evidence_packets")
    items = [
        build_result_item(
            repo_root=repo_root,
            run_id=run_id,
            row=row,
            group=groups.get(candidate_group_id_from_evidence(row.get("Evidence / Run Link", "")), {}),
            manifest=manifest,
            packets=packets,
        )
        for row in selected_rows
    ]
    status = aggregate_status(items)
    if any(not item.candidate for item in items):
        findings.append("One or more approved review rows had no matching candidate group.")
        status = "blocked"
    findings.extend(aggregate_item_findings(items))

    written_paths: list[str] = []
    if write:
        market_dir.mkdir(parents=True, exist_ok=True)
        json_path = market_dir / CANDIDATE_VERIFICATION_RESULT_JSON
        md_path = market_dir / CANDIDATE_VERIFICATION_RESULT_MD
        result = CandidateVerificationResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status=status,
            review_ids=[row.get("ID", "") for row in selected_rows],
            items=items,
            findings=findings,
            written_paths=[],
        )
        json_path.write_text(json.dumps(candidate_verification_result_to_dict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        md_path.write_text(format_candidate_verification_result(result), encoding="utf-8")
        written_paths = [json_path.relative_to(repo_root).as_posix(), md_path.relative_to(repo_root).as_posix()]

    return CandidateVerificationResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=status,
        review_ids=[row.get("ID", "") for row in selected_rows],
        items=items,
        findings=findings,
        written_paths=written_paths,
    )


def build_result_item(
    *,
    repo_root: Path,
    run_id: str,
    row: dict[str, str],
    group: dict[str, str],
    manifest: dict[str, Any],
    packets: list[tuple[Path, EvidencePacket]],
) -> CandidateVerificationResultItem:
    group_id = candidate_group_id_from_evidence(row.get("Evidence / Run Link", ""))
    tickers = [value.strip().upper() for value in group.get("Tickers", "").split(",") if value.strip()]
    provider_tasks = tasks_for_tickers(manifest.get("provider_tasks", []), tickers)
    analysis_tasks = tasks_for_tickers(manifest.get("analysis_tasks", []), tickers)
    item = CandidateVerificationResultItem(
        review_item_id=row.get("ID", ""),
        candidate_group_id=group_id,
        candidate=normalize_ascii(group.get("Candidate", "")),
        tickers=tickers,
        decision_kind=normalize_ascii(group.get("Decision Kind", "")),
        review_status=normalize_ascii(row.get("Status", "")),
        provider_checks=[check_provider_task(repo_root, task, packets) for task in provider_tasks],
        analysis_checks=[check_analysis_task(repo_root, run_id, task, packets) for task in analysis_tasks],
    )
    evaluate_item(item)
    return item


def evaluate_item(item: CandidateVerificationResultItem) -> None:
    if not item.candidate:
        item.findings.append(f"Missing candidate group {item.candidate_group_id}.")
    if item.review_status.lower() != "approved":
        item.findings.append(f"Human-review item is '{item.review_status}', not approved.")
    missing_providers = [check for check in item.provider_checks if check.status == "missing"]
    failed_analysis = [check for check in item.analysis_checks if check.status in {"missing", "needs_human_review"}]
    if missing_providers:
        item.findings.append(
            "Missing provider evidence: " + ", ".join(check.provider_or_tool for check in missing_providers) + "."
        )
        item.next_actions.append("Treat missing provider evidence as a coverage gap before promotion.")
    if any(check.status == "needs_human_review" for check in item.analysis_checks):
        item.findings.append("At least one specialist review needs human review.")
        item.next_actions.append("Review the specialist report findings before any monitoring decision.")
    if any(check.provider_or_tool == "company_news_review" and check.status == "ready_for_company_update" for check in item.analysis_checks):
        item.next_actions.append("Company-news evidence is reviewable and can inform a future company file if the candidate is promoted.")
    if item.decision_kind != "monitoring_candidate":
        item.next_actions.append("This approval is for verification only; a separate monitoring decision is still required.")
    if item.findings:
        item.status = "needs_human_review"
    elif item.decision_kind == "monitoring_candidate":
        item.status = "ready_for_promotion_review"
        item.next_actions.append("Run the approval-gated promotion writer only if the user still wants monitoring.")
    else:
        item.status = "verified_for_follow_up"


def check_provider_task(repo_root: Path, task: dict[str, Any], packets: list[tuple[Path, EvidencePacket]]) -> TaskCheck:
    task_id = normalize_ascii(task.get("id", ""))
    provider = normalize_ascii(task.get("provider", ""))
    subject_id = normalize_ascii(task.get("subject_id", "")).upper()
    packet_path = find_packet_for_task(task_id, provider, subject_id, packets)
    if packet_path:
        return TaskCheck(
            task_id=task_id,
            lane="provider",
            provider_or_tool=provider,
            subject_id=subject_id,
            status="complete",
            artifact=packet_path.relative_to(repo_root).as_posix(),
        )
    return TaskCheck(
        task_id=task_id,
        lane="provider",
        provider_or_tool=provider,
        subject_id=subject_id,
        status="missing",
        detail="No matching evidence packet found.",
    )


def check_analysis_task(repo_root: Path, run_id: str, task: dict[str, Any], packets: list[tuple[Path, EvidencePacket]]) -> TaskCheck:
    task_id = normalize_ascii(task.get("id", ""))
    tool = normalize_ascii(task.get("tool", ""))
    subject_id = normalize_ascii(task.get("subject_id", "")).upper()
    report_path, report_status = analysis_report_status(repo_root, run_id, subject_id, tool)
    if report_path:
        return TaskCheck(
            task_id=task_id,
            lane="analysis",
            provider_or_tool=tool,
            subject_id=subject_id,
            status=report_status or "complete",
            artifact=report_path.relative_to(repo_root).as_posix(),
        )
    packet_path = find_packet_for_task(task_id, tool_to_provider(tool), subject_id, packets)
    if packet_path:
        return TaskCheck(
            task_id=task_id,
            lane="analysis",
            provider_or_tool=tool,
            subject_id=subject_id,
            status="complete",
            artifact=packet_path.relative_to(repo_root).as_posix(),
        )
    return TaskCheck(
        task_id=task_id,
        lane="analysis",
        provider_or_tool=tool,
        subject_id=subject_id,
        status="missing",
        detail="No matching analysis artifact found.",
    )


def analysis_report_status(repo_root: Path, run_id: str, subject_id: str, tool: str) -> tuple[Path | None, str]:
    candidates: list[Path] = []
    if tool == "company_news_review":
        candidates.append(repo_root / "agents" / "runs" / run_id / "reports" / "company_news_specialist" / f"{subject_id}_company_news_review.md")
    if tool == "financial_review":
        candidates.append(repo_root / "agents" / "runs" / run_id / "reports" / "financial_data_specialist" / f"{subject_id}_financial_review.md")
    for path in candidates:
        if not path.exists():
            continue
        status = ""
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("Status:"):
                status = normalize_ascii(line.split(":", 1)[1]).strip()
                break
        return path, status
    return None, ""


def find_packet_for_task(
    task_id: str,
    provider: str,
    subject_id: str,
    packets: list[tuple[Path, EvidencePacket]],
) -> Path | None:
    provider = provider.lower()
    subject_id = subject_id.upper()
    for path, packet in packets:
        if task_id and task_id in packet.packet_id:
            return path
    for path, packet in packets:
        packet_subject = normalize_ascii(packet.subject_id).upper()
        if packet.provider == provider and packet_subject == subject_id:
            return path
    return None


def tool_to_provider(tool: str) -> str:
    return {
        "company_news_contents_follow_up": "exa",
        "company_news_review": "company_news_specialist",
        "financial_compare": "financial_compare",
        "financial_review": "financial_data_specialist",
    }.get(tool, tool)


def tasks_for_tickers(tasks: list[dict[str, Any]], tickers: list[str]) -> list[dict[str, Any]]:
    ticker_set = {ticker.upper() for ticker in tickers}
    return [task for task in tasks if normalize_ascii(task.get("subject_id", "")).upper() in ticker_set]


def load_evidence_packets(evidence_dir: Path) -> list[tuple[Path, EvidencePacket]]:
    if not evidence_dir.exists():
        return []
    packets: list[tuple[Path, EvidencePacket]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            packets.append((path, read_packet(path)))
        except Exception:
            continue
    return packets


def aggregate_status(items: list[CandidateVerificationResultItem]) -> str:
    if not items:
        return "no_approved_items"
    if any(item.status == "blocked" for item in items):
        return "blocked"
    if any(item.status == "needs_human_review" for item in items):
        return "needs_human_review"
    if all(item.status == "ready_for_promotion_review" for item in items):
        return "ready_for_promotion_review"
    return "verified_for_follow_up"


def aggregate_item_findings(items: list[CandidateVerificationResultItem]) -> list[str]:
    findings: list[str] = []
    seen: set[str] = set()
    for item in items:
        label = item.candidate or item.review_item_id
        for finding in item.findings:
            message = f"{label}: {finding}"
            if message not in seen:
                findings.append(message)
                seen.add(message)
    return findings


def format_candidate_verification_result(result: CandidateVerificationResult) -> str:
    lines = [
        f"# Candidate Verification Result: {result.run_id}",
        "",
        f"Generated: {result.generated_at}",
        f"Status: {result.status}",
        "",
        "## Findings",
        "",
    ]
    if result.findings:
        lines.extend(f"- {finding}" for finding in result.findings)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Candidate Outcomes",
            "",
            "| Review ID | Candidate | Tickers | Decision Kind | Status | Findings | Next Actions |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if result.items:
        for item in result.items:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        item.review_item_id,
                        item.candidate,
                        ", ".join(item.tickers),
                        item.decision_kind,
                        item.status,
                        "; ".join(item.findings) or "None.",
                        "; ".join(item.next_actions) or "None.",
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  | no_approved_items | No approved candidates selected. | None. |")

    for item in result.items:
        lines.extend(
            [
                "",
                f"## {item.candidate or item.review_item_id}",
                "",
                "### Provider Checks",
                "",
                "| Task | Provider | Status | Artifact / Detail |",
                "| --- | --- | --- | --- |",
            ]
        )
        for check in item.provider_checks:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        check.task_id,
                        check.provider_or_tool,
                        check.status,
                        check.artifact or check.detail,
                    ]
                )
                + " |"
            )
        lines.extend(
            [
                "",
                "### Analysis Checks",
                "",
                "| Task | Tool | Status | Artifact / Detail |",
                "| --- | --- | --- | --- |",
            ]
        )
        for check in item.analysis_checks:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        check.task_id,
                        check.provider_or_tool,
                        check.status,
                        check.artifact or check.detail,
                    ]
                )
                + " |"
            )
    return "\n".join(lines).rstrip() + "\n"


def candidate_verification_result_to_dict(result: CandidateVerificationResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "generated_at": result.generated_at,
        "status": result.status,
        "review_ids": result.review_ids,
        "items": [asdict(item) for item in result.items],
        "findings": result.findings,
        "written_paths": result.written_paths,
    }


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()
