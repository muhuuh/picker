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
    context: str = ""


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
        notes=truncate(notes, 260),
        context=build_review_context(category, item, decision, notes, evidence),
    )


def classify_review_category(item: str, decision: str, evidence: str, notes: str) -> str:
    text = f"{item} {decision} {evidence} {notes}".lower()
    if "candidate_review.md" in text or "discovery candidate" in text or "discovery lead" in text:
        if "possible monitoring" in text or "approve adding this candidate to monitoring" in text or "monitoring_candidate" in text:
            return "candidate_monitoring_review"
        if "grok-only" in text or "grok/x discovery lead" in text or "grok/x discovery basket" in text:
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
    if category == "candidate_monitoring_review":
        return "Approve adding to monitoring, request more research, or reject/ignore."
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


def build_review_context(category: str, item: str, decision: str, notes: str, evidence: str) -> str:
    base = strip_dead_source_id_tail(notes or decision or item)
    if category == "candidate_monitoring_review":
        prefix = "Read the linked candidate group and market report first; approval means this source-backed lead may enter the monitoring approval path."
    elif category == "candidate_verification_grok":
        prefix = "This is a social/X lead only; approval means run verification, not add to monitoring."
    elif category == "candidate_verification":
        prefix = "This lead needs company/news/financial verification before any monitoring decision."
    elif category == "company_file_update":
        prefix = "This is a proposed company-file change; multiple rows for one ticker can be separate update proposals."
    elif category == "strategy_or_workflow":
        prefix = "This changes strategy or process; approve only if the workflow should remember it."
    else:
        prefix = "Review the linked evidence before deciding."
    return truncate(f"{prefix} {base}", 520)


def strip_dead_source_id_tail(value: str) -> str:
    cleaned = re.sub(r"\s*Source IDs?:\s*[^.]+\.?", "", value or "", flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


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
        lines.append("- approve: allow the next gated follow-up step described in the row")
        lines.append("- reject: close or ignore the item")
        lines.append("- needs_more_research: keep open and request more evidence")
        lines.append("- leave open: make no change")
        lines.append("")
        lines.append("Monitoring candidates are not automatically added to monitoring. Grok/X verification items are earlier-stage social leads and only approve deeper verification.")
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
                category_help(category),
                "",
                "| Priority | ID | Target | Verification | Suggested action | Why this is here / where to read | Evidence |",
                "| --- | --- | --- | --- | --- | --- | --- |",
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
                        item.context,
                        format_evidence_link(item.evidence_link),
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
        "candidate_monitoring_review": 3,
        "candidate_verification_grok": 4,
        "candidate_verification": 5,
        "strategy_or_workflow": 6,
        "general_review": 7,
    }.get(category, 9)


def category_label(category: str) -> str:
    return {
        "investment_action": "Investment Actions",
        "company_file_update": "Company File Updates",
        "candidate_cooldown_review": "Candidate Cooldown Reviews",
        "candidate_monitoring_review": "Monitoring Candidate Reviews",
        "candidate_verification_grok": "Grok/X Candidate Verification",
        "candidate_verification": "Candidate Verification",
        "strategy_or_workflow": "Strategy / Workflow",
        "general_review": "General Review",
    }.get(category, category.replace("_", " ").title())


def category_help(category: str) -> str:
    return {
        "company_file_update": "Proposed edits to existing company files. Duplicate tickers can be valid when separate proposals touch different parts of the file.",
        "candidate_monitoring_review": "Source-backed discovery candidates that may be worth adding to monitoring after you review the linked evidence.",
        "candidate_verification_grok": "Early social/X leads from Grok. Approving these only starts verification; it does not add them to monitoring.",
        "candidate_verification": "Leads that need more company/news/financial verification before any monitoring decision.",
        "strategy_or_workflow": "Strategy or process changes that affect future runs.",
    }.get(category, "Review the linked evidence and choose approve, reject, needs_more_research, or leave open.")


def display_value(value: str) -> str:
    return value.replace("_", " ")


def format_evidence_link(value: str) -> str:
    if not value:
        return "not linked"
    label = "open evidence"
    return f"[{label}]({value})"


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()


def truncate(value: str, limit: int) -> str:
    cleaned = normalize_ascii(value)
    if len(cleaned) <= limit:
        return cleaned
    shortened = cleaned[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return f"{shortened}." if shortened and shortened[-1] not in ".!?" else shortened
