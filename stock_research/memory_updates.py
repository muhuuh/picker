from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import date
from pathlib import Path
from typing import Any

from .memory import (
    add_memory_item,
    generate_memory_id,
    load_memory_state,
    normalize_memory_fields,
    relative_to_root,
    validate_memory_fields,
)
from .memory_reflection import read_json_if_exists
from .repo import find_repo_root


@dataclass(frozen=True)
class MemoryUpdateDraftItem:
    proposal_id: str
    action: str
    target_file: str
    status: str
    reason: str
    fields: dict[str, str] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryUpdateDraft:
    run_id: str
    generated_at: str
    source_files: list[str]
    items: list[MemoryUpdateDraftItem] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryUpdateApplyResult:
    run_id: str
    applied: list[dict[str, str]] = field(default_factory=list)
    skipped: list[dict[str, str]] = field(default_factory=list)


def build_memory_update_draft(
    root: Path | None,
    run_id: str,
    current_date: date | None = None,
) -> MemoryUpdateDraft:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    memory = load_memory_state(repo_root)
    proposals, source_files = load_memory_update_proposals(repo_root, run_id)
    existing_lessons = {
        item.fields.get("lesson", "").strip()
        for item in memory.items
        if item.fields.get("status") in {"active", "needs_review"}
    }
    existing_ids = {item.fields.get("id", "") for item in memory.items}
    items: list[MemoryUpdateDraftItem] = []

    for proposal in proposals:
        proposal_id = str(proposal.get("proposal_id", "unknown_proposal"))
        action = str(proposal.get("action", ""))
        target_file = str(proposal.get("target_file", ""))
        fields = dict(proposal.get("fields", {}))
        issues: list[str] = []

        if action != "memory_add":
            issues.append(f"Unsupported proposal action: {action}")
        if not fields:
            issues.append("Proposal has no fields.")

        if fields:
            fields = normalize_memory_fields({str(key): str(value) for key, value in fields.items()}, today)
            if not fields.get("id"):
                fields["id"] = generate_memory_id(target_file, fields["date"], fields.get("lesson", ""), existing_ids)
                existing_ids.add(fields["id"])
            try:
                validate_memory_fields(fields)
            except ValueError as exc:
                issues.append(str(exc))
            if fields.get("lesson", "").strip() in existing_lessons:
                issues.append("A matching active/needs_review memory lesson already exists.")

        status = "ready" if not issues else "blocked"
        items.append(
            MemoryUpdateDraftItem(
                proposal_id=proposal_id,
                action=action,
                target_file=target_file,
                status=status,
                reason=str(proposal.get("reason", "")),
                fields=fields,
                issues=issues,
            )
        )

    return MemoryUpdateDraft(
        run_id=run_id,
        generated_at=today.isoformat(),
        source_files=source_files,
        items=items,
    )


def write_memory_update_draft(root: Path | None, draft: MemoryUpdateDraft) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / draft.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "memory_update_drafts.json"
    md_path = run_dir / "memory_update_drafts.md"
    json_path.write_text(json.dumps(memory_update_draft_to_dict(draft), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_memory_update_draft_markdown(draft), encoding="utf-8")
    return json_path, md_path


def apply_memory_update_draft(
    root: Path | None,
    run_id: str,
    proposal_ids: set[str] | None = None,
    apply_all: bool = False,
    current_date: date | None = None,
) -> MemoryUpdateApplyResult:
    if not apply_all and not proposal_ids:
        raise ValueError("Pass --all or at least one --proposal-id to apply memory updates.")
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    draft_path = repo_root / "agents" / "runs" / run_id / "memory_update_drafts.json"
    if draft_path.exists():
        draft = memory_update_draft_from_dict(json.loads(draft_path.read_text(encoding="utf-8")))
    else:
        draft = build_memory_update_draft(repo_root, run_id, today)

    applied: list[dict[str, str]] = []
    skipped: list[dict[str, str]] = []
    updated_items: list[MemoryUpdateDraftItem] = []
    for item in draft.items:
        if not apply_all and item.proposal_id not in proposal_ids:
            skipped.append({"proposal_id": item.proposal_id, "reason": "not selected"})
            updated_items.append(item)
            continue
        if item.status != "ready":
            skipped.append({"proposal_id": item.proposal_id, "reason": "; ".join(item.issues) or item.status})
            updated_items.append(item)
            continue
        result = add_memory_item(
            root=repo_root,
            fields=item.fields,
            current_date=today,
            memory_file=item.target_file,
        )
        applied_path = relative_to_root(repo_root, result.path).as_posix()
        applied.append(
            {
                "proposal_id": item.proposal_id,
                "item_id": result.item_id,
                "path": applied_path,
            }
        )
        updated_items.append(
            replace(
                item,
                status="applied",
                reason=f"Applied to {applied_path} as {result.item_id}.",
                issues=[],
            )
        )
    if applied:
        write_memory_update_draft(repo_root, replace(draft, items=updated_items))
    return MemoryUpdateApplyResult(run_id=run_id, applied=applied, skipped=skipped)


def load_memory_update_proposals(root: Path, run_id: str) -> tuple[list[dict[str, Any]], list[str]]:
    proposals: list[dict[str, Any]] = []
    source_files: list[str] = []
    reflection_path = root / "agents" / "runs" / run_id / "memory_reflection.json"
    recurring_path = root / "agents" / "memory" / "recurring_failures.json"
    for path in (reflection_path, recurring_path):
        data = read_json_if_exists(path)
        if not data:
            continue
        source_files.append(relative_to_root(root, path).as_posix())
        proposals.extend(list(data.get("memory_update_proposals", [])))
    return proposals, source_files


def memory_update_draft_to_dict(draft: MemoryUpdateDraft) -> dict[str, Any]:
    return {
        "run_id": draft.run_id,
        "generated_at": draft.generated_at,
        "source_files": draft.source_files,
        "items": [asdict(item) for item in draft.items],
    }


def memory_update_draft_from_dict(data: dict[str, Any]) -> MemoryUpdateDraft:
    return MemoryUpdateDraft(
        run_id=str(data.get("run_id", "")),
        generated_at=str(data.get("generated_at", "")),
        source_files=[str(value) for value in data.get("source_files", [])],
        items=[
            MemoryUpdateDraftItem(
                proposal_id=str(item.get("proposal_id", "")),
                action=str(item.get("action", "")),
                target_file=str(item.get("target_file", "")),
                status=str(item.get("status", "")),
                reason=str(item.get("reason", "")),
                fields={str(key): str(value) for key, value in item.get("fields", {}).items()},
                issues=[str(value) for value in item.get("issues", [])],
            )
            for item in data.get("items", [])
        ],
    )


def memory_update_apply_result_to_dict(result: MemoryUpdateApplyResult) -> dict[str, Any]:
    return {"run_id": result.run_id, "applied": result.applied, "skipped": result.skipped}


def format_memory_update_draft_markdown(draft: MemoryUpdateDraft) -> str:
    lines = [
        f"# Memory Update Drafts: {draft.run_id}",
        "",
        f"Generated: {draft.generated_at}",
        "",
        "## Source Files",
        "",
    ]
    if draft.source_files:
        for source_file in draft.source_files:
            lines.append(f"- `{source_file}`")
    else:
        lines.append("- No reflection or recurring-failure proposal files found.")

    lines.extend(["", "## Draft Items", ""])
    if not draft.items:
        lines.append("- No memory update proposals.")
        lines.append("")
    for item in draft.items:
        lines.append(f"### {item.proposal_id}")
        lines.append("")
        lines.append(f"- action: {item.action}")
        lines.append(f"- target_file: {item.target_file}")
        lines.append(f"- status: {item.status}")
        lines.append(f"- reason: {item.reason}")
        if item.issues:
            lines.append(f"- issues: {'; '.join(item.issues)}")
        if item.fields:
            lines.append(f"- item_id: {item.fields.get('id', '')}")
            lines.append(f"- lesson: {item.fields.get('lesson', '')}")
            lines.append(f"- evidence: {item.fields.get('evidence', '')}")
        lines.append("")
    lines.extend(
        [
            "## Apply",
            "",
            "Apply one approved proposal:",
            "",
            "```powershell",
            f"python -m stock_research memory apply-updates --run-id {draft.run_id} --proposal-id PROPOSAL_ID",
            "```",
            "",
            "Apply all ready proposals:",
            "",
            "```powershell",
            f"python -m stock_research memory apply-updates --run-id {draft.run_id} --all",
            "```",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"
