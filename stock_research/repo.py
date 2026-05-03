from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .markdown_tables import first_markdown_table, parse_markdown_tables


STOCK_TABLES = {
    "current_holdings": Path("stock_tracking/current_holdings/current_holdings.csv"),
    "monitoring": Path("stock_tracking/monitoring/monitoring.csv"),
    "rejected": Path("stock_tracking/rejected/rejected.csv"),
}

CATEGORY_STATE_FILES = {
    "current_holdings": Path("stock_tracking/current_holdings/current_holdings_state.md"),
    "monitoring": Path("stock_tracking/monitoring/monitoring_state.md"),
    "rejected": Path("stock_tracking/rejected/rejected_state.md"),
}


@dataclass(frozen=True)
class CsvTable:
    path: Path
    fieldnames: list[str]
    rows: list[dict[str, str]]


@dataclass(frozen=True)
class RepoState:
    root: Path
    stock_tables: dict[str, CsvTable]
    category_state_files: dict[str, Path]
    stock_info_files: dict[str, list[Path]]
    human_requests: list[dict[str, str]]
    research_priorities: list[dict[str, str]]
    human_review_items: list[dict[str, str]]


def find_repo_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "AGENTS.md").exists() and (candidate / "stock_tracking").exists():
            return candidate
    raise FileNotFoundError("Could not find repo root containing AGENTS.md and stock_tracking/")


def load_repo_state(root: Path | None = None) -> RepoState:
    repo_root = find_repo_root(root)
    stock_tables = {name: read_csv_table(repo_root / rel_path) for name, rel_path in STOCK_TABLES.items()}
    category_state_files = {name: repo_root / rel_path for name, rel_path in CATEGORY_STATE_FILES.items()}
    stock_info_files = {
        name: sorted((repo_root / "stock_tracking" / "stock_info_files" / name).glob("*.md"))
        for name in STOCK_TABLES
    }

    return RepoState(
        root=repo_root,
        stock_tables=stock_tables,
        category_state_files=category_state_files,
        stock_info_files=stock_info_files,
        human_requests=load_first_table(repo_root / "docs/plans/human_research_requests.md"),
        research_priorities=load_first_table(repo_root / "strategy/research_priorities.md"),
        human_review_items=load_first_table(repo_root / "agents/human_review_queue.md"),
    )


def read_csv_table(path: Path) -> CsvTable:
    if not path.exists():
        return CsvTable(path=path, fieldnames=[], rows=[])

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [{key: value or "" for key, value in row.items() if key is not None} for row in reader]
        return CsvTable(path=path, fieldnames=list(reader.fieldnames or []), rows=rows)


def load_first_table(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    return first_markdown_table(path.read_text(encoding="utf-8"))


def load_all_tables(path: Path) -> list[list[dict[str, str]]]:
    if not path.exists():
        return []
    return parse_markdown_tables(path.read_text(encoding="utf-8"))
