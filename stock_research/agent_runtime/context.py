from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from uuid import uuid4

from stock_research.memory import build_memory_context, format_memory_context_for_prompt, load_memory_state
from stock_research.repo import find_repo_root


def new_trace_id() -> str:
    return f"trace_{uuid4().hex}"


@dataclass(frozen=True)
class ResearchRunContext:
    root: Path
    run_id: str
    task: str
    manifest_path: Path | None = None
    memory_context: str = ""
    memory_item_ids: tuple[str, ...] = ()
    known_memory_item_ids: tuple[str, ...] = ()
    allowed_write_targets: tuple[Path, ...] = ()
    trace_id: str = field(default_factory=new_trace_id)
    group_id: str = ""
    dry_run: bool = True
    execute_providers: bool = False
    execute_analysis: bool = False
    execute_writes: bool = False

    @property
    def run_dir(self) -> Path:
        return self.root / "agents" / "runs" / self.run_id

    @property
    def trace_group_id(self) -> str:
        return self.group_id or self.run_id

    def can_write(self, path: Path) -> bool:
        if not self.execute_writes:
            return False
        resolved = path.resolve()
        return any(resolved == target.resolve() or target.resolve() in resolved.parents for target in self.allowed_write_targets)


def build_research_run_context(
    *,
    root: Path | None = None,
    run_id: str,
    task: str,
    manifest_path: Path | None = None,
    allowed_write_targets: tuple[Path, ...] = (),
    dry_run: bool = True,
    execute_providers: bool = False,
    execute_analysis: bool = False,
    execute_writes: bool = False,
) -> ResearchRunContext:
    repo_root = find_repo_root(root)
    memory_context, memory_item_ids, known_memory_item_ids = build_runtime_memory(repo_root, task)
    return ResearchRunContext(
        root=repo_root,
        run_id=run_id,
        task=task,
        manifest_path=manifest_path,
        memory_context=memory_context,
        memory_item_ids=memory_item_ids,
        known_memory_item_ids=known_memory_item_ids,
        allowed_write_targets=tuple(repo_root / target if not target.is_absolute() else target for target in allowed_write_targets),
        dry_run=dry_run,
        execute_providers=execute_providers,
        execute_analysis=execute_analysis,
        execute_writes=execute_writes,
    )


def with_task_memory(context: ResearchRunContext, task: str) -> ResearchRunContext:
    memory_context, memory_item_ids, known_memory_item_ids = build_runtime_memory(context.root, task)
    return replace(
        context,
        task=task,
        memory_context=memory_context,
        memory_item_ids=memory_item_ids,
        known_memory_item_ids=known_memory_item_ids,
    )


def build_runtime_memory(root: Path, task: str) -> tuple[str, tuple[str, ...], tuple[str, ...]]:
    memory_state = load_memory_state(root)
    memory_context = format_memory_context_for_prompt(memory_state, task)
    task_context = build_memory_context(memory_state, task)
    relevant_ids = tuple(
        str(item.get("id", ""))
        for item in task_context.get("active_items", [])
        if item.get("id")
    )
    known_ids = tuple(
        item.fields.get("id", "")
        for item in memory_state.items
        if item.fields.get("status") in {"active", "needs_review"} and item.fields.get("id")
    )
    return memory_context, relevant_ids, known_ids
