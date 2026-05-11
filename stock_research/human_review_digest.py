from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.repo import find_repo_root, load_first_table


HUMAN_REVIEW_DIGEST_PATH = Path("agents/human_review_digest.md")
OPEN_REVIEW_STATUSES = {"open", "needs_more_research"}


@dataclass
class HumanReviewDigestItem:
    review_id: str
    date_added: str
    category: str
    priority: str
    status: str
    target: str
    decision_needed: str
    suggested_action: str
    verification_status: str = "not_specified"
    evidence_link: str = ""
    notes: str = ""


@dataclass(frozen=True)
class HumanReviewDigest:
    generated_at: str
    status_filter: list[str]
    status: str
    open_item_count: int
    priority_counts: dict[str, int] = field(default_factory=dict)
    category_counts: dict[str, int] = field(default_factory=dict)
    items: list[HumanReviewDigestItem] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def build_human_review_digest(
    *,
    root: Path | None = None,
    statuses: set[str] | None = None,
    current_date: date | None = None,
    write: bool = False,
) -> HumanReviewDigest:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    status_filter = {value.lower() for value in (statuses or OPEN_REVIEW_STATUSES)}
    rows = load_first_table(repo_root / "agents" / "human_review_queue.md")
    items = [
        build_digest_item(row)
        for row in rows
        if normalize_ascii(row.get("Status", "")).lower() in status_filter
    ]
    items.sort(key=digest_sort_key)
    priority_counts = count_by(items, "priority")
    category_counts = count_by(items, "category")
    status = "needs_user_review" if items else "clear"
    written_paths: list[str] = []
    digest = HumanReviewDigest(
        generated_at=today.isoformat(),
        status_filter=sorted(status_filter),
        status=status,
        open_item_count=len(items),
        priority_counts=priority_counts,
        category_counts=category_counts,
        items=items,
        written_paths=[],
    )
    if write:
        target = repo_root / HUMAN_REVIEW_DIGEST_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(format_human_review_digest(digest), encoding="utf-8")
        written_paths.append(target.relative_to(repo_root).as_posix())
        digest = HumanReviewDigest(
            generated_at=digest.generated_at,
            status_filter=digest.status_filter,
            status=digest.status,
            open_item_count=digest.open_item_count,
            priority_counts=digest.priority_counts,
            category_counts=digest.category_counts,
            items=digest.items,
            written_paths=written_paths,
        )
    return digest


def build_digest_item(row: dict[str, str]) -> HumanReviewDigestItem:
    item = normalize_ascii(row.get("Item", ""))
    decision = normalize_ascii(row.get("Decision Needed", ""))
    notes = normalize_ascii(row.get("Notes", ""))
    evidence = normalize_ascii(row.get("Evidence / Run Link", ""))
    category = classify_review_category(item, decision, evidence, notes)
    return HumanReviewDigestItem(
        review_id=normalize_ascii(row.get("ID", "")),
        date_added=normalize_ascii(row.get("Date Added", "")),
        category=category,
        priority=normalize_ascii(row.get("Priority", "")).lower() or "medium",
        status=normalize_ascii(row.get("Status", "")).lower(),
        target=extract_target(item=item, decision=decision, notes=notes, evidence=evidence),
        decision_needed=truncate(decision or item, 110),
        suggested_action=suggest_action(category, item, decision, notes),
        verification_status=extract_verification(notes),
        evidence_link=evidence,
        notes=truncate(notes, 140),
    )


def classify_review_category(item: str, decision: str, evidence: str, notes: str) -> str:
    text = f"{item} {decision} {evidence} {notes}".lower()
    if "candidate_review.md" in text or "discovery candidate" in text or "discovery lead" in text:
        if "grok" in text:
            return "candidate_verification_grok"
        if "cooldown_active" in text or "cooldown override" in text:
            return "candidate_cooldown_review"
        return "candidate_verification"
    if "orchestrator_update_proposals.md" in text or "file update proposal" in text:
        return "company_file_update"
    if "strategy" in text or "workflow" in text or "intake layer" in text:
        return "strategy_or_workflow"
    if "buy" in text or "sell" in text or "position" in text:
        return "investment_action"
    return "general_review"


def extract_target(*, item: str, decision: str, notes: str, evidence: str) -> str:
    for source in (item, notes, decision):
        match = re.search(r"\(([A-Z][A-Z0-9.-]{0,9})\)", source)
        if match:
            return match.group(1)
    ticker_match = re.search(r"Tickers:\s*([^\.]+)", notes)
    if ticker_match:
        return ticker_match.group(1).strip()
    path_match = re.search(r"stock_tracking/stock_info_files/[^ ]+/([A-Z0-9_.-]+)\.md", f"{item} {evidence}")
    if path_match:
        return path_match.group(1).replace("_", ".")
    if "intake layer" in item.lower():
        return "human-to-system intake"
    words = [word.strip(".,:;") for word in item.split()]
    for word in words:
        if word.isupper() and 2 <= len(word) <= 8:
            return word
    return "not specified"


def extract_verification(notes: str) -> str:
    match = re.search(r"verification=([a-zA-Z0-9_-]+)", notes)
    if match:
        return match.group(1)
    if "source-validated" in notes.lower():
        return "source_validated"
    return "not_specified"


def suggest_action(category: str, item: str, decision: str, notes: str) -> str:
    text = f"{item} {decision} {notes}".lower()
    if category == "candidate_verification_grok":
        return "Approve follow-up verification, reject/ignore, or leave open. Do not promote yet."
    if category == "candidate_verification":
        return "Approve follow-up verification or reject/ignore before any monitoring decision."
    if category == "candidate_cooldown_review":
        return "Approve explicit cooldown override or keep the candidate blocked."
    if category == "company_file_update":
        return "Approve, reject, or request more research; approved proposals can then be applied."
    if category == "strategy_or_workflow":
        return "Approve, reject, or refine the workflow/strategy change."
    if "buy" in text or "sell" in text or "position" in text:
        return "Review as research only; no automatic trade action."
    return "Approve, reject, or request more research."


def format_human_review_digest(digest: HumanReviewDigest) -> str:
    lines = [
        "# Human Review Digest",
        "",
        f"Generated: {digest.generated_at}",
        f"Status: {digest.status}",
        f"Open items summarized: {digest.open_item_count}",
        "",
        "## Summary",
        "",
    ]
    if digest.open_item_count == 0:
        lines.append("- No open review items.")
    else:
        for category, count in sorted(digest.category_counts.items(), key=lambda item: category_sort_key(item[0])):
            lines.append(f"- {category_label(category)}: {count}")
        lines.append("")
        lines.append("## Decision Options")
        lines.append("")
        lines.append("- approve: allow the next gated follow-up step")
        lines.append("- reject: close or ignore the item")
        lines.append("- needs_more_research: keep open and request more evidence")
        lines.append("- leave open: make no change")
        lines.append("")
        lines.append("## Priority Counts")
        lines.append("")
        for priority, count in sorted(digest.priority_counts.items(), key=lambda item: priority_rank(item[0])):
            lines.append(f"- {priority}: {count}")

    for category in sorted({item.category for item in digest.items}, key=category_sort_key):
        category_items = [item for item in digest.items if item.category == category]
        lines.extend(
            [
                "",
                f"## {category_label(category)}",
                "",
                "| Priority | ID | Target | Verification | Suggested action | Evidence |",
                "| --- | --- | --- | --- | --- | --- |",
            ]
        )
        for item in category_items:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        item.priority,
                        item.review_id,
                        item.target,
                        display_value(item.verification_status),
                        item.suggested_action,
                        item.evidence_link or "not linked",
                    ]
                )
                + " |"
            )

    if digest.open_item_count:
        lines.extend(
            [
                "",
                "## Suggested Codex Prompt",
                "",
                "Tell Codex which HRQ ids to approve, reject, leave open, or mark as needing more research. Example:",
                "",
                "`Approve HRQ-XXXX and HRQ-YYYY for follow-up verification; reject HRQ-ZZZZ; leave the rest open.`",
                "",
                "Codex should record explicit decisions with `python -m stock_research human-review decide --set HRQ-XXXX=approved --write` before running any approved follow-up command.",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def human_review_digest_to_dict(digest: HumanReviewDigest) -> dict[str, Any]:
    return {
        "generated_at": digest.generated_at,
        "status_filter": digest.status_filter,
        "status": digest.status,
        "open_item_count": digest.open_item_count,
        "priority_counts": digest.priority_counts,
        "category_counts": digest.category_counts,
        "items": [asdict(item) for item in digest.items],
        "written_paths": digest.written_paths,
    }


def count_by(items: list[HumanReviewDigestItem], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        value = getattr(item, field_name)
        counts[value] = counts.get(value, 0) + 1
    return counts


def digest_sort_key(item: HumanReviewDigestItem) -> tuple[int, int, str]:
    return category_sort_key(item.category), priority_rank(item.priority), item.review_id


def priority_rank(priority: str) -> int:
    return {"urgent": 0, "high": 1, "medium": 2, "low": 3}.get(priority.lower(), 9)


def category_sort_key(category: str) -> int:
    return {
        "investment_action": 0,
        "company_file_update": 1,
        "candidate_cooldown_review": 2,
        "candidate_verification_grok": 3,
        "candidate_verification": 4,
        "strategy_or_workflow": 5,
        "general_review": 6,
    }.get(category, 9)


def category_label(category: str) -> str:
    return {
        "investment_action": "Investment Actions",
        "company_file_update": "Company File Updates",
        "candidate_cooldown_review": "Candidate Cooldown Reviews",
        "candidate_verification_grok": "Grok/X Candidate Verification",
        "candidate_verification": "Candidate Verification",
        "strategy_or_workflow": "Strategy / Workflow",
        "general_review": "General Review",
    }.get(category, category.replace("_", " ").title())


def display_value(value: str) -> str:
    return value.replace("_", " ")


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()


def truncate(value: str, limit: int) -> str:
    cleaned = normalize_ascii(value)
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."
