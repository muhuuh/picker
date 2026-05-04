from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .repo import find_repo_root


MEMORY_DIR = Path("agents/memory")

REQUIRED_MEMORY_FILES = (
    "README.md",
    "memory_index.md",
    "orchestrator_lessons.md",
    "source_quality.md",
    "specialist_playbooks.md",
    "evaluation_metrics.md",
    "deprecated_memory.md",
)

ITEM_MEMORY_FILES = (
    "orchestrator_lessons.md",
    "source_quality.md",
    "evaluation_metrics.md",
    "deprecated_memory.md",
)

REQUIRED_ITEM_FIELDS = (
    "id",
    "date",
    "type",
    "scope",
    "status",
    "confidence",
    "trigger/source",
    "lesson",
    "use_when",
    "do_not_use_when",
    "evidence",
    "owner",
    "next_review",
)

TASK_MEMORY_MAP = {
    "orchestration": ("orchestrator_lessons.md",),
    "manifest": ("orchestrator_lessons.md", "source_quality.md"),
    "provider": ("source_quality.md",),
    "source": ("source_quality.md",),
    "citation": ("source_quality.md",),
    "financial": ("source_quality.md", "specialist_playbooks.md"),
    "news": ("source_quality.md", "specialist_playbooks.md"),
    "sentiment": ("source_quality.md", "specialist_playbooks.md", "deprecated_memory.md"),
    "specialist": ("specialist_playbooks.md", "source_quality.md"),
    "writer": ("specialist_playbooks.md",),
    "quality": ("evaluation_metrics.md", "source_quality.md", "deprecated_memory.md"),
    "evaluation": ("evaluation_metrics.md", "source_quality.md"),
    "learning": ("evaluation_metrics.md", "orchestrator_lessons.md", "source_quality.md", "deprecated_memory.md"),
    "all": REQUIRED_MEMORY_FILES,
}


@dataclass(frozen=True)
class MemoryItem:
    path: Path
    fields: dict[str, str]


@dataclass(frozen=True)
class MemoryFile:
    path: Path
    exists: bool
    text: str
    items: list[MemoryItem]


@dataclass(frozen=True)
class MemoryState:
    root: Path
    files: dict[str, MemoryFile]

    @property
    def items(self) -> list[MemoryItem]:
        result: list[MemoryItem] = []
        for memory_file in self.files.values():
            result.extend(memory_file.items)
        return result


@dataclass(frozen=True)
class MemoryValidationReport:
    errors: list[str]
    warnings: list[str]

    @property
    def ok(self) -> bool:
        return not self.errors


def load_memory_state(root: Path | None = None) -> MemoryState:
    repo_root = find_repo_root(root)
    files: dict[str, MemoryFile] = {}
    for name in REQUIRED_MEMORY_FILES:
        path = repo_root / MEMORY_DIR / name
        text = path.read_text(encoding="utf-8") if path.exists() else ""
        items = parse_memory_items(text, path) if name in ITEM_MEMORY_FILES else []
        files[name] = MemoryFile(path=path, exists=path.exists(), text=text, items=items)
    return MemoryState(root=repo_root, files=files)


def parse_memory_items(text: str, path: Path) -> list[MemoryItem]:
    items: list[MemoryItem] = []
    current: dict[str, str] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("- ") or ":" not in line:
            continue

        key, value = line[2:].split(":", 1)
        key = key.strip()
        value = value.strip()

        if key == "id":
            if current:
                items.append(MemoryItem(path=path, fields=current))
            current = {"id": value}
            continue

        if current is not None:
            current[key] = value

    if current:
        items.append(MemoryItem(path=path, fields=current))
    return items


def validate_memory_state(memory: MemoryState) -> MemoryValidationReport:
    errors: list[str] = []
    warnings: list[str] = []

    for name, memory_file in memory.files.items():
        if not memory_file.exists:
            errors.append(f"Missing memory file: {MEMORY_DIR / name}")
        elif not memory_file.text.strip():
            warnings.append(f"Empty memory file: {MEMORY_DIR / name}")

    seen_ids: set[str] = set()
    for item in memory.items:
        item_id = item.fields.get("id", "")
        if not item_id:
            errors.append(f"{relative_to_root(memory.root, item.path)} has memory item without id")
            continue
        if item_id in seen_ids:
            errors.append(f"Duplicate memory id: {item_id}")
        seen_ids.add(item_id)

        missing = [field for field in REQUIRED_ITEM_FIELDS if not item.fields.get(field)]
        if missing:
            errors.append(f"{item_id} missing required field(s): {', '.join(missing)}")

        status = item.fields.get("status", "")
        if status not in {"active", "superseded", "deprecated", "needs_review"}:
            errors.append(f"{item_id} has invalid status: {status}")

        confidence = item.fields.get("confidence", "")
        if confidence not in {"low", "medium", "high"}:
            errors.append(f"{item_id} has invalid confidence: {confidence}")

    return MemoryValidationReport(errors=errors, warnings=warnings)


def relevant_memory_files(task: str) -> tuple[str, ...]:
    normalized = task.strip().lower().replace("_", "-")
    if normalized in TASK_MEMORY_MAP:
        return TASK_MEMORY_MAP[normalized]

    selected: list[str] = []
    for keyword, files in TASK_MEMORY_MAP.items():
        if keyword == "all":
            continue
        if keyword in normalized:
            selected.extend(files)

    if not selected:
        selected = ["memory_index.md", "orchestrator_lessons.md"]

    return tuple(dict.fromkeys(selected))


def build_memory_context(memory: MemoryState, task: str) -> dict[str, object]:
    files = relevant_memory_files(task)
    active_items = [
        {
            "id": item.fields.get("id", ""),
            "file": relative_to_root(memory.root, item.path).as_posix(),
            "type": item.fields.get("type", ""),
            "scope": item.fields.get("scope", ""),
            "status": item.fields.get("status", ""),
            "lesson": item.fields.get("lesson", ""),
            "use_when": item.fields.get("use_when", ""),
            "evidence": item.fields.get("evidence", ""),
        }
        for name in files
        for item in memory.files.get(name, MemoryFile(memory.root / MEMORY_DIR / name, False, "", [])).items
        if item.fields.get("status") in {"active", "needs_review"} or name == "deprecated_memory.md"
    ]
    return {
        "task": task,
        "memory_files": [(MEMORY_DIR / name).as_posix() for name in files],
        "active_items": active_items,
    }


def memory_summary(memory: MemoryState) -> dict[str, object]:
    by_status: dict[str, int] = {}
    by_scope: dict[str, int] = {}
    for item in memory.items:
        status = item.fields.get("status", "unknown")
        scope = item.fields.get("scope", "unknown")
        by_status[status] = by_status.get(status, 0) + 1
        by_scope[scope] = by_scope.get(scope, 0) + 1

    return {
        "memory_dir": MEMORY_DIR.as_posix(),
        "files": {
            name: {
                "exists": memory_file.exists,
                "items": len(memory_file.items),
            }
            for name, memory_file in memory.files.items()
        },
        "total_items": len(memory.items),
        "by_status": by_status,
        "by_scope": by_scope,
    }


def relative_to_root(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path
