from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from .repo import RepoState
from .validation import parse_date


ACTIVE_HUMAN_REQUEST_STATUSES = {"new", "triaged", "queued_for_weekly_run", "in_progress"}


def build_weekly_manifest(state: RepoState, today: date | None = None) -> dict[str, Any]:
    current_date = today or date.today()
    run_date = next_saturday(current_date)
    human_requests = active_human_requests(state.human_requests)
    priorities = active_research_priorities(state.research_priorities)

    manifest = {
        "manifest_version": 1,
        "manifest_id": f"weekly_{run_date.isoformat()}",
        "generated_at": datetime.combine(current_date, datetime.min.time()).isoformat(),
        "run_type": "weekly",
        "run_date": run_date.isoformat(),
        "scope": ["US", "Europe"],
        "inputs": {
            "stock_tables": {
                name: {
                    "path": table.path.relative_to(state.root).as_posix(),
                    "rows": len([row for row in table.rows if any(value.strip() for value in row.values())]),
                }
                for name, table in state.stock_tables.items()
            },
            "human_requests": human_requests,
            "research_priorities": priorities,
            "human_review_items": open_review_items(state.human_review_items),
        },
        "tracked_tickers": tracked_tickers(state),
        "cooldown": rejected_cooldown_summary(state, current_date),
        "tasks": build_tasks(human_requests, priorities),
        "outputs": {
            "run_summary": f"agents/runs/{run_date.isoformat()}_weekly/run_summary.md",
            "quality_report": f"agents/runs/{run_date.isoformat()}_weekly/quality_report.md",
            "manifest": f"agents/runs/{run_date.isoformat()}_weekly/manifest.json",
        },
    }
    return manifest


def write_manifest(state: RepoState, manifest: dict[str, Any], output: Path | None = None) -> Path:
    target = output
    if target is None:
        run_date = manifest["run_date"]
        target = state.root / "agents" / "runs" / f"{run_date}_weekly" / "manifest.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target


def next_saturday(value: date) -> date:
    days_until_saturday = (5 - value.weekday()) % 7
    return value + timedelta(days=days_until_saturday)


def active_human_requests(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    active = []
    for row in rows:
        status = row.get("Status", "").strip().lower()
        next_run = row.get("Next Run", "").strip().lower()
        if status in ACTIVE_HUMAN_REQUEST_STATUSES and next_run not in {"no", "false", "n"}:
            active.append(row)
    return active


def active_research_priorities(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("Status", "").strip().lower() in {"active", "watch", "watching"}]


def open_review_items(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [row for row in rows if row.get("Status", "").strip().lower() in {"open", "needs_more_research"}]


def tracked_tickers(state: RepoState) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, table in state.stock_tables.items():
        result[name] = [row.get("ticker", "").strip() for row in table.rows if row.get("ticker", "").strip()]
    return result


def rejected_cooldown_summary(state: RepoState, today: date) -> dict[str, list[dict[str, str]]]:
    in_cooldown: list[dict[str, str]] = []
    eligible: list[dict[str, str]] = []
    missing_dates: list[dict[str, str]] = []

    for row in state.stock_tables["rejected"].rows:
        ticker = row.get("ticker", "").strip()
        if not ticker:
            continue
        eligible_at = parse_date(row.get("next_eligible_review_date", ""))
        item = {
            "ticker": ticker,
            "company_name": row.get("company_name", ""),
            "next_eligible_review_date": row.get("next_eligible_review_date", ""),
        }
        if not eligible_at:
            missing_dates.append(item)
        elif eligible_at > today:
            in_cooldown.append(item)
        else:
            eligible.append(item)

    return {"in_cooldown": in_cooldown, "eligible": eligible, "missing_dates": missing_dates}


def build_tasks(human_requests: list[dict[str, str]], priorities: list[dict[str, str]]) -> list[dict[str, str]]:
    tasks = [
        {"id": "validate_repo_state", "kind": "deterministic", "reason": "Always validate repo state before research."},
        {"id": "scan_current_holdings", "kind": "research", "reason": "Weekly tracked-stock alert coverage."},
        {"id": "scan_monitoring", "kind": "research", "reason": "Weekly watchlist alert coverage."},
        {"id": "check_rejected_cooldowns", "kind": "deterministic", "reason": "Rejected stocks can resurface after 6 weeks."},
    ]
    if human_requests:
        tasks.append(
            {
                "id": "process_human_input_queue",
                "kind": "deterministic",
                "reason": f"{len(human_requests)} human request(s) are active for this run.",
            }
        )
    if priorities:
        tasks.append(
            {
                "id": "scan_research_priorities",
                "kind": "research",
                "reason": f"{len(priorities)} active research priority item(s).",
            }
        )
    return tasks
