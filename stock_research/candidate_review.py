from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.outputs import CandidateLead
from stock_research.agent_runtime.proposal_review import (
    ensure_human_review_queue,
    increment_human_review_id,
    next_human_review_id,
    normalize_ascii,
)
from stock_research.manifest import slugify
from stock_research.markdown_edit import append_markdown_table_row
from stock_research.repo import find_repo_root, load_first_table


@dataclass
class CandidateReviewGroup:
    group_id: str
    canonical_name: str
    primary_ticker: str = ""
    tickers: list[str] = field(default_factory=list)
    company_names: list[str] = field(default_factory=list)
    source_channels: list[str] = field(default_factory=list)
    source_ids: list[str] = field(default_factory=list)
    verification_status: str = "unverified"
    hype_level: str = "unknown"
    sentiment: str = "unknown"
    rejected_cooldown_status: str = "not_rejected"
    next_action: str = "verify"
    review_priority: str = "medium"
    decision_kind: str = "verify_before_monitoring"
    rumor_flag: bool = False
    why_surfaced: str = ""
    notes: str = ""
    lead_count: int = 0


@dataclass(frozen=True)
class CandidateReviewResult:
    run_id: str
    generated_at: str
    status: str
    source_files: list[str] = field(default_factory=list)
    groups: list[CandidateReviewGroup] = field(default_factory=list)
    review_items: list[dict[str, Any]] = field(default_factory=list)
    quality_findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def build_candidate_review(
    *,
    root: Path | None = None,
    run_id: str,
    subject_id: str = "",
    current_date: date | None = None,
    write: bool = False,
    queue_review: bool = False,
) -> CandidateReviewResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    candidate_files = find_candidate_lead_files(repo_root, run_id, subject_id)
    leads = load_candidate_leads(candidate_files)
    groups = group_candidate_leads(leads)
    quality_findings = evaluate_candidate_review_groups(groups)
    review_items = build_candidate_review_items(groups)
    status = candidate_review_status(groups, review_items, quality_findings)
    written_paths: list[str] = []

    if write:
        report_path = write_candidate_review_markdown(
            repo_root=repo_root,
            run_id=run_id,
            generated_at=today,
            status=status,
            candidate_files=candidate_files,
            groups=groups,
            review_items=review_items,
            quality_findings=quality_findings,
            subject_id=subject_id,
        )
        written_paths.append(report_path.relative_to(repo_root).as_posix())
        if queue_review:
            queue_path = append_candidate_reviews_to_human_review_queue(
                repo_root=repo_root,
                run_id=run_id,
                generated_at=today,
                groups=groups,
                review_items=review_items,
                report_path=report_path,
            )
            written_paths.append(queue_path.relative_to(repo_root).as_posix())

    return CandidateReviewResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=status,
        source_files=[path.relative_to(repo_root).as_posix() for path in candidate_files],
        groups=groups,
        review_items=review_items,
        quality_findings=quality_findings,
        written_paths=dedupe_strings(written_paths),
    )


def find_candidate_lead_files(repo_root: Path, run_id: str, subject_id: str = "") -> list[Path]:
    market_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    if not market_dir.exists():
        raise FileNotFoundError(f"Missing market_research directory: {market_dir}")
    if subject_id:
        path = market_dir / f"{slugify(subject_id)}_candidate_leads.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing candidate leads file: {path}")
        return [path]
    files = sorted(market_dir.glob("*_candidate_leads.json"))
    if not files:
        raise FileNotFoundError(f"No candidate lead files found under: {market_dir}")
    return files


def load_candidate_leads(paths: list[Path]) -> list[CandidateLead]:
    leads: list[CandidateLead] = []
    for path in paths:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Candidate lead artifact must contain a list: {path}")
        for item in data:
            if not isinstance(item, dict):
                continue
            valid_keys = CandidateLead.__dataclass_fields__.keys()
            payload = {key: item.get(key) for key in valid_keys if key in item}
            for key in ("source_channels", "source_ids"):
                if payload.get(key) is None:
                    payload[key] = []
            leads.append(CandidateLead(**payload))
    return leads


def group_candidate_leads(leads: list[CandidateLead]) -> list[CandidateReviewGroup]:
    buckets: dict[str, list[CandidateLead]] = {}
    for lead in leads:
        key = candidate_group_key(lead)
        buckets.setdefault(key, []).append(lead)

    groups: list[CandidateReviewGroup] = []
    for index, bucket in enumerate(sorted(buckets.values(), key=group_sort_key), start=1):
        group = aggregate_candidate_group(f"CRG-{index:04d}", bucket)
        groups.append(group)
    return groups


def candidate_group_key(lead: CandidateLead) -> str:
    company_key = normalize_company_key(lead.company_name)
    if company_key:
        return f"company:{company_key}"
    ticker_root = normalize_ticker_root(lead.ticker)
    if ticker_root:
        return f"ticker:{ticker_root}"
    return f"unknown:{normalize_company_key(lead.why_surfaced) or 'candidate'}"


def aggregate_candidate_group(group_id: str, leads: list[CandidateLead]) -> CandidateReviewGroup:
    tickers = sorted({lead.ticker.strip().upper() for lead in leads if lead.ticker.strip()})
    company_names = sorted({lead.company_name.strip() for lead in leads if lead.company_name.strip()})
    channels = sorted({channel for lead in leads for channel in lead.source_channels if channel})
    source_ids = sorted({source_id for lead in leads for source_id in lead.source_ids if source_id})
    verification_status = group_verification_status(channels, [lead.verification_status for lead in leads])
    cooldown_status = group_cooldown_status([lead.rejected_cooldown_status for lead in leads])
    hype_level = group_hype_level([lead.hype_level for lead in leads])
    sentiment = group_sentiment([lead.sentiment for lead in leads])
    rumor_flag = any(lead.rumor_flag for lead in leads)
    next_action = group_next_action(verification_status, cooldown_status)
    canonical_name = company_names[0] if company_names else (tickers[0] if tickers else "unknown candidate")
    group = CandidateReviewGroup(
        group_id=group_id,
        canonical_name=canonical_name,
        primary_ticker=tickers[0] if tickers else "",
        tickers=tickers,
        company_names=company_names,
        source_channels=channels,
        source_ids=source_ids,
        verification_status=verification_status,
        hype_level=hype_level,
        sentiment=sentiment,
        rejected_cooldown_status=cooldown_status,
        next_action=next_action,
        review_priority=group_review_priority(verification_status, cooldown_status, hype_level, rumor_flag),
        decision_kind=group_decision_kind(verification_status, cooldown_status),
        rumor_flag=rumor_flag,
        why_surfaced=choose_longest([lead.why_surfaced for lead in leads]),
        notes=group_notes(verification_status, cooldown_status, rumor_flag),
        lead_count=len(leads),
    )
    return group


def build_candidate_review_items(groups: list[CandidateReviewGroup]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group in groups:
        if group.next_action == "ignore" and group.rejected_cooldown_status != "cooldown_active":
            continue
        items.append(
            {
                "review_item_id": group.group_id,
                "title": review_title(group),
                "question": review_question(group),
                "priority": group.review_priority,
                "source_ids": group.source_ids,
                "related_candidate": candidate_label(group),
                "decision_kind": group.decision_kind,
                "reason": review_reason(group),
            }
        )
    return items


def evaluate_candidate_review_groups(groups: list[CandidateReviewGroup]) -> list[str]:
    findings: list[str] = []
    for group in groups:
        label = candidate_label(group)
        if not group.source_ids:
            findings.append(f"{label}: grouped candidate is missing source_ids.")
        if group.verification_status == "grok_only" and group.decision_kind == "monitoring_candidate":
            findings.append(f"{label}: Grok-only lead cannot become a monitoring candidate.")
        if group.rejected_cooldown_status == "cooldown_active" and group.decision_kind != "cooldown_override":
            findings.append(f"{label}: active rejected cooldown must route to cooldown override review.")
    return findings


def candidate_review_status(
    groups: list[CandidateReviewGroup],
    review_items: list[dict[str, Any]],
    quality_findings: list[str],
) -> str:
    if quality_findings:
        return "needs_review"
    if review_items:
        return "ready_for_human_review"
    if groups:
        return "no_review_items"
    return "no_candidates"


def write_candidate_review_markdown(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    status: str,
    candidate_files: list[Path],
    groups: list[CandidateReviewGroup],
    review_items: list[dict[str, Any]],
    quality_findings: list[str],
    subject_id: str = "",
) -> Path:
    target_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    target_dir.mkdir(parents=True, exist_ok=True)
    name = f"{slugify(subject_id)}_candidate_review.md" if subject_id else "candidate_review.md"
    path = target_dir / name
    path.write_text(
        format_candidate_review_markdown(
            repo_root=repo_root,
            run_id=run_id,
            generated_at=generated_at,
            status=status,
            candidate_files=candidate_files,
            groups=groups,
            review_items=review_items,
            quality_findings=quality_findings,
        ),
        encoding="utf-8",
    )
    return path


def format_candidate_review_markdown(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    status: str,
    candidate_files: list[Path],
    groups: list[CandidateReviewGroup],
    review_items: list[dict[str, Any]],
    quality_findings: list[str],
) -> str:
    lines = [
        f"# Candidate Review: {run_id}",
        "",
        f"Generated: {generated_at.isoformat()}",
        f"Status: {status}",
        "",
        "## Purpose",
        "",
        "This file groups market-discovery candidate leads into reviewable decisions. It does not add stocks to monitoring.",
        "",
        "## Source Files",
        "",
    ]
    lines.extend(f"- {path.relative_to(repo_root).as_posix()}" for path in candidate_files)
    lines.extend(["", "## Quality Findings", ""])
    if quality_findings:
        lines.extend(f"- {finding}" for finding in quality_findings)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Candidate Groups",
            "",
            "| Group ID | Candidate | Tickers | Channels | Verification | Hype | Cooldown | Decision Kind | Priority | Why surfaced |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if groups:
        for group in groups:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        group.group_id,
                        group.canonical_name,
                        ", ".join(group.tickers),
                        ", ".join(group.source_channels),
                        group.verification_status,
                        group.hype_level,
                        group.rejected_cooldown_status,
                        group.decision_kind,
                        group.review_priority,
                        truncate(group.why_surfaced, 180),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  |  |  |  |  |  | No candidate leads found. |")
    lines.extend(
        [
            "",
            "## Human Review Bridge",
            "",
            "| Review Item ID | Candidate | Decision Kind | Priority | Question | Reason |",
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
                        item["related_candidate"],
                        item["decision_kind"],
                        item["priority"],
                        item["question"],
                        item["reason"],
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  | No human review items generated. |  |")
    return "\n".join(lines).rstrip() + "\n"


def append_candidate_reviews_to_human_review_queue(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    groups: list[CandidateReviewGroup],
    review_items: list[dict[str, Any]],
    report_path: Path,
) -> Path:
    path = repo_root / "agents" / "human_review_queue.md"
    ensure_human_review_queue(path)
    existing_evidence = {row.get("Evidence / Run Link", "") for row in load_first_table(path)}
    group_by_id = {group.group_id: group for group in groups}
    next_id = next_human_review_id(path)
    for item in review_items:
        group = group_by_id.get(str(item["review_item_id"]))
        evidence = f"{report_path.relative_to(repo_root).as_posix()}#{item['review_item_id']}"
        if evidence in existing_evidence:
            continue
        related_files = f"agents/runs/{run_id}/market_research"
        row = [
            next_id,
            generated_at.isoformat(),
            item["title"],
            item["question"],
            item["priority"],
            "open",
            related_files,
            evidence,
            review_notes(group, item),
        ]
        append_markdown_table_row(path, "| ID | Date Added | Item |", [normalize_ascii(str(value)) for value in row])
        existing_evidence.add(evidence)
        next_id = increment_human_review_id(next_id)
    return path


def candidate_review_to_dict(result: CandidateReviewResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "generated_at": result.generated_at,
        "status": result.status,
        "source_files": result.source_files,
        "groups": [asdict(group) for group in result.groups],
        "review_items": result.review_items,
        "quality_findings": result.quality_findings,
        "written_paths": result.written_paths,
    }


def normalize_company_key(value: str) -> str:
    cleaned = value.lower()
    cleaned = re.sub(r"\b(inc|incorporated|corp|corporation|plc|ltd|limited|ag|sa|se|nv|spa|co|company)\b", "", cleaned)
    return re.sub(r"[^a-z0-9]+", "", cleaned)


def normalize_ticker_root(value: str) -> str:
    ticker = value.strip().upper()
    if not ticker:
        return ""
    return ticker.split(".", 1)[0]


def group_sort_key(leads: list[CandidateLead]) -> tuple[int, str]:
    best_action = min(action_rank(lead.next_action) for lead in leads) if leads else 9
    label = normalize_company_key(leads[0].company_name) or normalize_ticker_root(leads[0].ticker)
    return best_action, label


def group_verification_status(channels: list[str], lead_statuses: list[str]) -> str:
    channel_set = set(channels)
    if "grok" in channel_set and "exa" in channel_set:
        return "verified"
    if "grok" in channel_set and any(channel != "grok" for channel in channel_set):
        return "partially_verified"
    if channel_set == {"grok"}:
        return "grok_only"
    if channel_set == {"exa"}:
        return "exa_only"
    for status in ("verified", "partially_verified", "exa_only", "grok_only"):
        if status in lead_statuses:
            return status
    return "unverified"


def group_cooldown_status(statuses: list[str]) -> str:
    if "cooldown_active" in statuses:
        return "cooldown_active"
    if "rejected_missing_cooldown_date" in statuses:
        return "rejected_missing_cooldown_date"
    if "cooldown_elapsed" in statuses:
        return "cooldown_elapsed"
    return "not_rejected"


def group_hype_level(values: list[str]) -> str:
    for level in ("high", "medium", "low"):
        if level in values:
            return level
    return "unknown"


def group_sentiment(values: list[str]) -> str:
    cleaned = {value for value in values if value and value != "unknown"}
    if not cleaned:
        return "unknown"
    if len(cleaned) == 1:
        return next(iter(cleaned))
    return "mixed"


def group_next_action(verification_status: str, cooldown_status: str) -> str:
    if cooldown_status == "cooldown_active":
        return "ignore"
    if verification_status in {"verified", "partially_verified"}:
        return "human_review"
    return "verify"


def group_decision_kind(verification_status: str, cooldown_status: str) -> str:
    if cooldown_status == "cooldown_active":
        return "cooldown_override"
    if verification_status in {"verified", "partially_verified"}:
        return "monitoring_candidate"
    if verification_status == "grok_only":
        return "verify_grok_lead"
    return "verify_before_monitoring"


def group_review_priority(verification_status: str, cooldown_status: str, hype_level: str, rumor_flag: bool) -> str:
    if cooldown_status == "cooldown_active":
        return "high"
    if verification_status in {"verified", "partially_verified"}:
        return "high" if hype_level == "high" else "medium"
    if verification_status == "grok_only" and hype_level == "high":
        return "medium" if rumor_flag else "high"
    return "medium"


def group_notes(verification_status: str, cooldown_status: str, rumor_flag: bool) -> str:
    notes = []
    if verification_status == "grok_only":
        notes.append("Grok-only social lead; verify before considering monitoring.")
    if cooldown_status == "cooldown_active":
        notes.append("Rejected cooldown active; requires explicit override.")
    if rumor_flag:
        notes.append("Rumor/speculation language present.")
    return " ".join(notes)


def review_title(group: CandidateReviewGroup) -> str:
    label = candidate_label(group)
    if group.decision_kind == "cooldown_override":
        return f"Review rejected-cooldown override for discovery candidate {label}."
    if group.decision_kind == "monitoring_candidate":
        return f"Review verified discovery candidate {label} for possible monitoring."
    if group.decision_kind == "verify_grok_lead":
        return f"Review Grok/X discovery lead {label} for follow-up verification."
    return f"Review discovery candidate {label} for verification before monitoring."


def review_question(group: CandidateReviewGroup) -> str:
    if group.decision_kind == "cooldown_override":
        return "Approve an explicit rejected-cooldown override, or keep this candidate blocked."
    if group.decision_kind == "monitoring_candidate":
        return "Approve adding this candidate to monitoring, or request more research first."
    if group.decision_kind == "verify_grok_lead":
        return "Approve Exa/filing/financial verification of this Grok-only lead, or ignore it."
    return "Approve follow-up company and financial verification before considering monitoring."


def review_reason(group: CandidateReviewGroup) -> str:
    return (
        f"Candidate surfaced from {', '.join(group.source_channels) or 'unknown sources'} "
        f"with verification={group.verification_status}, hype={group.hype_level}, "
        f"cooldown={group.rejected_cooldown_status}."
    )


def review_notes(group: CandidateReviewGroup | None, item: dict[str, Any]) -> str:
    if not group:
        return str(item.get("reason", ""))
    tickers = ", ".join(group.tickers) if group.tickers else "no ticker"
    return f"{item['reason']} Tickers: {tickers}. Source IDs: {', '.join(group.source_ids)}."


def candidate_label(group: CandidateReviewGroup) -> str:
    ticker_part = f" ({', '.join(group.tickers)})" if group.tickers else ""
    return f"{group.canonical_name}{ticker_part}"


def choose_longest(values: list[str]) -> str:
    return max((value.strip() for value in values if value.strip()), key=len, default="")


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()


def truncate(value: str, length: int) -> str:
    if len(value) <= length:
        return value
    return value[: length - 3].rstrip() + "..."


def action_rank(action: str) -> int:
    return {"human_review": 0, "verify": 1, "ignore": 2, "reject": 3, "add_to_monitoring": 4}.get(action, 9)


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
