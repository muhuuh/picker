from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.human_review_digest import build_human_review_digest
from stock_research.repo import find_repo_root


HUMAN_REVIEW_QUEUE_PATH = Path("agents/human_review_queue.md")
VALID_HUMAN_REVIEW_STATUSES = {"open", "approved", "rejected", "needs_more_research", "superseded"}


@dataclass(frozen=True)
class HumanReviewDecision:
    review_id: str
    status: str
    note: str = ""
    actor: str = "user"


@dataclass
class HumanReviewDecisionItem:
    review_id: str
    old_status: str = ""
    new_status: str = ""
    status: str = "blocked"
    item: str = ""
    evidence_link: str = ""
    findings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class HumanReviewDecisionResult:
    generated_at: str
    status: str
    requested_count: int
    applied_count: int
    blocked_count: int
    items: list[HumanReviewDecisionItem] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


@dataclass
class MarkdownTable:
    lines: list[str]
    table_start: int
    table_end: int
    headers: list[str]
    rows: list[dict[str, str]]


def apply_human_review_decisions(
    *,
    root: Path | None = None,
    decisions: list[HumanReviewDecision],
    current_date: date | None = None,
    write: bool = False,
    refresh_digest: bool = True,
) -> HumanReviewDecisionResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    queue_path = repo_root / HUMAN_REVIEW_QUEUE_PATH
    if not queue_path.exists():
        return HumanReviewDecisionResult(
            generated_at=today.isoformat(),
            status="blocked",
            requested_count=len(decisions),
            applied_count=0,
            blocked_count=len(decisions) or 1,
            items=[
                HumanReviewDecisionItem(
                    review_id="",
                    status="blocked",
                    findings=[f"Missing human-review queue: {HUMAN_REVIEW_QUEUE_PATH.as_posix()}"],
                )
            ],
        )

    requested = normalize_decisions(decisions)
    table = read_first_table(queue_path)
    row_by_id = {normalize_ascii(row.get("ID", "")).upper(): row for row in table.rows}
    decision_items: list[HumanReviewDecisionItem] = []
    blocked = False
    seen_review_ids: set[str] = set()

    for decision in requested:
        review_id = decision.review_id.upper()
        item = HumanReviewDecisionItem(review_id=review_id, new_status=decision.status)
        if review_id in seen_review_ids:
            item.findings.append(f"Duplicate decision for {review_id}; provide each HRQ id only once.")
        seen_review_ids.add(review_id)
        if decision.status not in VALID_HUMAN_REVIEW_STATUSES:
            item.findings.append(
                f"Invalid status '{decision.status}'. Valid statuses: {', '.join(sorted(VALID_HUMAN_REVIEW_STATUSES))}."
            )
        row = row_by_id.get(review_id)
        if not row:
            item.findings.append(f"No human-review row found for id {review_id}.")
        if item.findings:
            item.status = "blocked"
            blocked = True
            decision_items.append(item)
            continue

        old_status = normalize_ascii(row.get("Status", "")).lower()
        item.old_status = old_status
        item.item = normalize_ascii(row.get("Item", ""))
        item.evidence_link = normalize_ascii(row.get("Evidence / Run Link", ""))
        item.status = "ready_to_apply"
        decision_items.append(item)

    if blocked:
        return HumanReviewDecisionResult(
            generated_at=today.isoformat(),
            status="blocked",
            requested_count=len(requested),
            applied_count=0,
            blocked_count=sum(1 for item in decision_items if item.status == "blocked"),
            items=decision_items,
        )

    written_paths: list[str] = []
    if write and requested:
        for decision in requested:
            row = row_by_id[decision.review_id.upper()]
            row["Status"] = decision.status
            row["Notes"] = append_decision_note(
                row.get("Notes", ""),
                today=today,
                status=decision.status,
                note=decision.note,
                actor=decision.actor,
            )
        for item in decision_items:
            item.status = "applied"
        queue_path.write_text(render_first_table(table), encoding="utf-8")
        written_paths.append(HUMAN_REVIEW_QUEUE_PATH.as_posix())
        if refresh_digest:
            digest = build_human_review_digest(root=repo_root, current_date=today, write=True)
            written_paths.extend(path for path in digest.written_paths if path not in written_paths)

    status = "applied" if write else "ready_to_apply"
    if not requested:
        status = "no_decisions"
    return HumanReviewDecisionResult(
        generated_at=today.isoformat(),
        status=status,
        requested_count=len(requested),
        applied_count=0 if not write else len(requested),
        blocked_count=0,
        items=decision_items,
        written_paths=written_paths,
    )


def normalize_decisions(decisions: list[HumanReviewDecision]) -> list[HumanReviewDecision]:
    normalized: list[HumanReviewDecision] = []
    for decision in decisions:
        review_id = normalize_ascii(decision.review_id).upper()
        status = normalize_ascii(decision.status).lower()
        normalized.append(
            HumanReviewDecision(
                review_id=review_id,
                status=status,
                note=normalize_ascii(decision.note),
                actor=normalize_ascii(decision.actor) or "user",
            )
        )
    return normalized


def append_decision_note(existing: str, *, today: date, status: str, note: str, actor: str) -> str:
    clean_existing = normalize_ascii(existing)
    clean_note = normalize_ascii(note)
    clean_actor = normalize_ascii(actor) or "user"
    entry = f"Decision update {today.isoformat()} by {clean_actor}: {status}."
    if clean_note:
        entry = f"{entry} {clean_note}"
    if not clean_existing:
        return entry
    return f"{clean_existing} {entry}"


def read_first_table(path: Path) -> MarkdownTable:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    for index in range(0, max(len(lines) - 1, 0)):
        current = lines[index].strip()
        next_line = lines[index + 1].strip()
        if is_table_row(current) and is_separator_row(next_line):
            headers = split_row(current)
            table_end = index + 2
            rows: list[dict[str, str]] = []
            while table_end < len(lines) and is_table_row(lines[table_end].strip()):
                values = split_row(lines[table_end].strip())
                rows.append({header: values[pos] if pos < len(values) else "" for pos, header in enumerate(headers)})
                table_end += 1
            return MarkdownTable(lines=lines, table_start=index, table_end=table_end, headers=headers, rows=rows)
    raise ValueError(f"No markdown table found in {path}")


def render_first_table(table: MarkdownTable) -> str:
    rendered = [
        "| " + " | ".join(escape_cell(header) for header in table.headers) + " |",
        "| " + " | ".join("---" for _ in table.headers) + " |",
    ]
    for row in table.rows:
        rendered.append("| " + " | ".join(escape_cell(row.get(header, "")) for header in table.headers) + " |")
    lines = table.lines[: table.table_start] + rendered + table.lines[table.table_end :]
    return "\n".join(lines).rstrip() + "\n"


def parse_cli_decision(value: str, *, note: str = "", actor: str = "user") -> HumanReviewDecision:
    if "=" not in value:
        raise ValueError(f"Decision must be REVIEW_ID=STATUS, got: {value}")
    review_id, status = value.split("=", 1)
    return HumanReviewDecision(review_id=review_id.strip(), status=status.strip(), note=note, actor=actor)


def human_review_decision_result_to_dict(result: HumanReviewDecisionResult) -> dict[str, Any]:
    return {
        "generated_at": result.generated_at,
        "status": result.status,
        "requested_count": result.requested_count,
        "applied_count": result.applied_count,
        "blocked_count": result.blocked_count,
        "items": [asdict(item) for item in result.items],
        "written_paths": result.written_paths,
    }


def is_table_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|")


def is_separator_row(line: str) -> bool:
    if not is_table_row(line):
        return False
    cells = split_row(line)
    return bool(cells) and all(set(cell.replace(":", "").strip()) <= {"-"} and "-" in cell for cell in cells)


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()
