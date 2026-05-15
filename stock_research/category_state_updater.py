from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .agent_runtime.proposal_writer import update_last_updated
from .repo import find_repo_root, load_repo_state
from .validation import parse_date


@dataclass(frozen=True)
class CategoryStateUpdateItem:
    category: str
    target_file: str
    status: str
    summary: str
    source: str


@dataclass(frozen=True)
class CategoryStateUpdateResult:
    generated_at: str
    run_id: str
    status: str
    mode: str
    items: list[CategoryStateUpdateItem]
    written_paths: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


def update_category_state_files(
    *,
    root: Path | None = None,
    run_id: str = "",
    current_date: date | None = None,
    write: bool = False,
) -> CategoryStateUpdateResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    state = load_repo_state(repo_root)
    update_id = f"CATSTATE-{run_id or today.isoformat()}"
    items: list[CategoryStateUpdateItem] = []
    written_paths: list[str] = []
    findings: list[str] = []

    for category in ("current_holdings", "monitoring", "rejected"):
        target = state.category_state_files[category]
        table = state.stock_tables[category]
        if not target.exists():
            findings.append(f"Missing category state file: {relative_path(repo_root, target)}")
            items.append(
                CategoryStateUpdateItem(
                    category=category,
                    target_file=relative_path(repo_root, target),
                    status="blocked",
                    summary="Missing category state file.",
                    source=source_for_run(repo_root, run_id),
                )
            )
            continue
        text = target.read_text(encoding="utf-8")
        if update_id in text:
            items.append(
                CategoryStateUpdateItem(
                    category=category,
                    target_file=relative_path(repo_root, target),
                    status="already_applied",
                    summary="This category state update was already applied.",
                    source=source_for_run(repo_root, run_id),
                )
            )
            continue
        summary = summarize_category(category, table.rows, today)
        source = source_for_run(repo_root, run_id)
        if write:
            new_text = update_last_updated(text, today)
            new_text = ensure_automated_table(new_text)
            new_text = append_automated_row(new_text, today, update_id, category, summary, source)
            target.write_text(new_text, encoding="utf-8")
            written_paths.append(relative_path(repo_root, target))
        items.append(
            CategoryStateUpdateItem(
                category=category,
                target_file=relative_path(repo_root, target),
                status="updated" if write else "ready_to_update",
                summary=summary,
                source=source,
            )
        )

    statuses = {item.status for item in items}
    if "blocked" in statuses:
        status = "blocked"
    elif statuses <= {"updated", "already_applied"}:
        status = "complete"
    elif statuses <= {"ready_to_update", "already_applied"}:
        status = "ready_to_update"
    else:
        status = "partial"
    return CategoryStateUpdateResult(
        generated_at=today.isoformat(),
        run_id=run_id,
        status=status,
        mode="write" if write else "dry_run",
        items=items,
        written_paths=dedupe_strings(written_paths),
        findings=findings,
    )


def summarize_category(category: str, rows: list[dict[str, str]], today: date) -> str:
    tickers = [str(row.get("ticker", "")).strip().upper() for row in rows if str(row.get("ticker", "")).strip()]
    if category == "current_holdings":
        return f"{len(tickers)} current holding(s): {', '.join(tickers) if tickers else 'none'}."
    if category == "monitoring":
        return f"{len(tickers)} monitored stock(s): {', '.join(tickers) if tickers else 'none'}."
    cooldown_active = 0
    eligible = 0
    for row in rows:
        next_eligible = parse_date(str(row.get("next_eligible_review_date", "")))
        if next_eligible and next_eligible > today:
            cooldown_active += 1
        elif next_eligible:
            eligible += 1
    return (
        f"{len(tickers)} rejected stock(s): {cooldown_active} still in cooldown, "
        f"{eligible} eligible for reconsideration."
    )


def source_for_run(repo_root: Path, run_id: str) -> str:
    if not run_id:
        return "manual category-state update"
    final_digest = repo_root / "agents" / "runs" / run_id / "final_digest.md"
    if final_digest.exists():
        return f"[agents/runs/{run_id}/final_digest.md](agents/runs/{run_id}/final_digest.md)"
    run_summary = repo_root / "agents" / "runs" / run_id / "run_summary.md"
    if run_summary.exists():
        return f"[agents/runs/{run_id}/run_summary.md](agents/runs/{run_id}/run_summary.md)"
    return f"`{run_id}`"


def ensure_automated_table(text: str) -> str:
    heading = "## Automated State Updates"
    header = "| Date | Update ID | Category | Summary | Source |"
    separator = "| --- | --- | --- | --- | --- |"
    if heading not in text:
        return text.rstrip() + f"\n\n{heading}\n\n{header}\n{separator}\n"
    section_start = text.index(heading)
    next_section = text.find("\n## ", section_start + len(heading))
    section = text[section_start:] if next_section == -1 else text[section_start:next_section]
    if header in section:
        return text
    insert_at = section_start + len(heading)
    return text[:insert_at] + f"\n\n{header}\n{separator}\n" + text[insert_at:]


def append_automated_row(text: str, current_date: date, update_id: str, category: str, summary: str, source: str) -> str:
    heading = "## Automated State Updates"
    section_start = text.index(heading)
    next_section = text.find("\n## ", section_start + len(heading))
    section_end = len(text) if next_section == -1 else next_section
    row = "| " + " | ".join(clean_cell(value) for value in [current_date.isoformat(), update_id, category, summary, source]) + " |"
    section = text[section_start:section_end]
    if row in section:
        return text
    return text[:section_end].rstrip() + "\n" + row + "\n\n" + text[section_end:].lstrip("\n")


def clean_cell(value: str) -> str:
    return " ".join(str(value).replace("|", "/").split())


def relative_path(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def dedupe_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def category_state_update_result_to_dict(result: CategoryStateUpdateResult) -> dict:
    return asdict(result)
