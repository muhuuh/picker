from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .markdown_edit import append_markdown_table_row
from .repo import load_first_table


REQUEST_TYPES = {
    "stock_research",
    "industry_research",
    "theme_tracking",
    "strategy_change",
    "alert_review",
    "manual_run",
    "stock_status_move",
    "other",
}


@dataclass(frozen=True)
class ClassifiedRequest:
    request_type: str
    tickers: list[str]
    next_run: str
    immediate_action: str
    target_hint: str


def classify_request(text: str) -> ClassifiedRequest:
    lowered = text.lower()
    tickers = sorted(set(re.findall(r"\b[A-Z]{1,5}\b", text)))
    immediate = "yes" if any(word in lowered for word in ["now", "immediate", "today", "asap"]) else "no"

    if immediate == "yes" and any(word in lowered for word in ["run", "scan"]):
        request_type = "manual_run"
    elif any(word in lowered for word in ["move", "reject", "rejected", "holding", "holdings", "monitoring"]):
        request_type = "stock_status_move"
    elif any(word in lowered for word in ["alert", "decision", "review queue", "what changed"]):
        request_type = "alert_review"
    elif any(word in lowered for word in ["strategy", "from now on", "avoid", "prefer", "criteria"]):
        request_type = "strategy_change"
    elif any(word in lowered for word in ["theme", "technology", "critical next year", "include", "track"]):
        request_type = "theme_tracking"
    elif any(word in lowered for word in ["industry", "sector", "suppliers"]):
        request_type = "industry_research"
    elif tickers or any(word in lowered for word in ["stock", "stocks", "company", "companies", "research"]):
        request_type = "stock_research"
    elif any(word in lowered for word in ["run", "scan"]):
        request_type = "manual_run"
    else:
        request_type = "other"

    if request_type == "alert_review":
        next_run = "no"
    else:
        next_run = "yes"

    return ClassifiedRequest(
        request_type=request_type,
        tickers=tickers,
        next_run=next_run,
        immediate_action=immediate,
        target_hint=target_hint(request_type),
    )


def append_human_request(
    root: Path,
    request_text: str,
    priority: str = "medium",
    status: str = "new",
    today: date | None = None,
) -> str:
    path = root / "docs" / "plans" / "human_research_requests.md"
    current_date = today or date.today()
    classification = classify_request(request_text)
    next_id = next_human_request_id(path)
    row = [
        next_id,
        current_date.isoformat(),
        request_text,
        classification.request_type,
        priority,
        status,
        ", ".join(classification.tickers),
        "",
        classification.target_hint,
        classification.next_run,
        classification.immediate_action,
        "Codex",
        "",
        "Added through deterministic intake CLI.",
    ]
    append_markdown_table_row(path, "| ID | Date Added | Request |", row)
    return next_id


def next_human_request_id(path: Path) -> str:
    rows = load_first_table(path)
    max_number = 0
    for row in rows:
        value = row.get("ID", "")
        match = re.match(r"HIR-(\d+)", value)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return f"HIR-{max_number + 1:04d}"


def target_hint(request_type: str) -> str:
    if request_type == "stock_research":
        return "stock_tracking/monitoring/, stock_info_files"
    if request_type == "industry_research":
        return "market_research/industries/, strategy/research_priorities.md"
    if request_type == "theme_tracking":
        return "market_research/themes/, strategy/research_priorities.md"
    if request_type == "strategy_change":
        return "strategy/"
    if request_type == "alert_review":
        return "agents/human_review_queue.md"
    if request_type == "manual_run":
        return "agents/runs/"
    if request_type == "stock_status_move":
        return "stock_tracking/, agents/human_review_queue.md"
    return ""
