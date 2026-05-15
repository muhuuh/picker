from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

from .human_review_digest import build_human_review_digest
from .repo import find_repo_root


@dataclass(frozen=True)
class RunEndReviewSummary:
    run_id: str
    generated_at: str
    status: str
    open_item_count: int
    category_counts: dict[str, int]
    digest_path: str
    written_paths: list[str] = field(default_factory=list)


def build_run_end_review_summary(
    *,
    root: Path | None = None,
    run_id: str,
    current_date: date | None = None,
    write: bool = False,
) -> RunEndReviewSummary:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    digest = build_human_review_digest(root=repo_root, current_date=today, write=write)
    written_paths = list(digest.written_paths)
    if write:
        path = repo_root / "agents" / "runs" / run_id / "human_review_digest_summary.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(format_run_end_review_summary(run_id, today, digest), encoding="utf-8")
        written_paths.append(relative_path(repo_root, path))
    return RunEndReviewSummary(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=digest.status,
        open_item_count=digest.open_item_count,
        category_counts=dict(digest.category_counts),
        digest_path="agents/human_review_digest.md",
        written_paths=dedupe_strings(written_paths),
    )


def format_run_end_review_summary(run_id: str, current_date: date, digest) -> str:
    lines = [
        f"# Run-End Human Review Summary: {run_id}",
        "",
        f"Generated: {current_date.isoformat()}",
        f"Status: {digest.status}",
        f"Open items: {digest.open_item_count}",
        "",
        "Read `agents/human_review_digest.md` for the current decision inbox. Allowed decisions are approve, reject, needs more research, or leave open.",
        "",
        "## Open Items By Category",
        "",
    ]
    if digest.category_counts:
        for category, count in sorted(digest.category_counts.items()):
            lines.append(f"- {category}: {count}")
    else:
        lines.append("- None.")
    lines.extend(["", "## Next Action", ""])
    if digest.open_item_count:
        lines.append("- Ask Codex to summarize `agents/human_review_digest.md`, then give decisions by HRQ id.")
    else:
        lines.append("- No open human-review decisions.")
    return "\n".join(lines).rstrip() + "\n"


def run_end_review_summary_to_dict(summary: RunEndReviewSummary) -> dict:
    return asdict(summary)


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
