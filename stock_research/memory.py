from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re

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
    "specialist_playbooks.md",
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
    "sdk": ("orchestrator_lessons.md", "specialist_playbooks.md"),
    "tool": ("orchestrator_lessons.md", "source_quality.md"),
    "guardrail": ("orchestrator_lessons.md", "evaluation_metrics.md", "source_quality.md"),
    "provider": ("source_quality.md",),
    "source": ("source_quality.md",),
    "citation": ("source_quality.md",),
    "financial": ("source_quality.md", "specialist_playbooks.md"),
    "news": ("source_quality.md", "specialist_playbooks.md"),
    "sentiment": ("orchestrator_lessons.md", "source_quality.md", "specialist_playbooks.md", "deprecated_memory.md"),
    "specialist": ("specialist_playbooks.md", "source_quality.md"),
    "writer": ("specialist_playbooks.md",),
    "quality": ("evaluation_metrics.md", "source_quality.md", "deprecated_memory.md"),
    "evaluation": ("evaluation_metrics.md", "source_quality.md"),
    "learning": ("evaluation_metrics.md", "orchestrator_lessons.md", "source_quality.md", "deprecated_memory.md"),
    "all": REQUIRED_MEMORY_FILES,
}

TYPE_MEMORY_FILE_MAP = {
    "procedural": "orchestrator_lessons.md",
    "semantic": "orchestrator_lessons.md",
    "episodic": "orchestrator_lessons.md",
    "source_quality": "source_quality.md",
    "evaluation": "evaluation_metrics.md",
}

MEMORY_FILE_PREFIXES = {
    "orchestrator_lessons.md": "orch",
    "source_quality.md": "source",
    "evaluation_metrics.md": "eval",
    "deprecated_memory.md": "deprecated",
}

VALID_MEMORY_TYPES = {"semantic", "episodic", "procedural", "source_quality", "evaluation"}
VALID_MEMORY_SCOPES = {"orchestrator", "provider", "financial", "news", "sentiment", "writer", "global"}
VALID_MEMORY_STATUSES = {"active", "superseded", "deprecated", "needs_review"}
VALID_MEMORY_CONFIDENCE = {"low", "medium", "high"}


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


@dataclass(frozen=True)
class MemoryWriteResult:
    item_id: str
    path: Path
    action: str


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
        if status not in VALID_MEMORY_STATUSES:
            errors.append(f"{item_id} has invalid status: {status}")

        confidence = item.fields.get("confidence", "")
        if confidence not in VALID_MEMORY_CONFIDENCE:
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


def format_memory_context_for_prompt(memory: MemoryState, task: str, max_items: int = 20) -> str:
    context = build_memory_context(memory, task)
    lines = [
        f"# Operational Memory Context: {task}",
        "",
        "Use these lessons as constraints for this task. Do not treat operational memory as investment facts.",
        "",
        "## Memory Files",
        "",
    ]
    for memory_file in context["memory_files"]:
        lines.append(f"- {memory_file}")
    lines.extend(["", "## Active Lessons", ""])
    items = sorted(list(context["active_items"]), key=lambda item: memory_prompt_score(item, task), reverse=True)[:max_items]
    if not items:
        lines.append("- No task-relevant operational memory items found.")
    for item in items:
        lines.append(f"- [{item['scope']}/{item['type']}/{item['status']}] {item['lesson']}")
        if item.get("use_when"):
            lines.append(f"  Use when: {item['use_when']}")
        if item.get("evidence"):
            lines.append(f"  Evidence: {item['evidence']}")
    return "\n".join(lines).rstrip() + "\n"


def memory_prompt_score(item: dict[str, str], task: str) -> int:
    normalized_task = task.lower()
    text = " ".join(
        [
            item.get("scope", ""),
            item.get("type", ""),
            item.get("lesson", ""),
            item.get("use_when", ""),
        ]
    ).lower()
    score = 0
    for token in re.findall(r"[a-z0-9]+", normalized_task):
        if token and token in text:
            score += 2
    if item.get("scope", "").lower() in normalized_task:
        score += 5
    if item.get("status") == "needs_review":
        score += 1
    return score


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


def add_memory_item(
    root: Path | None,
    fields: dict[str, str],
    current_date: date | None = None,
    memory_file: str | None = None,
) -> MemoryWriteResult:
    repo_root = find_repo_root(root)
    item_date = current_date or date.today()
    normalized = normalize_memory_fields(fields, item_date)
    target_name = resolve_memory_file(normalized, memory_file)
    memory = load_memory_state(repo_root)

    if not normalized.get("id"):
        normalized["id"] = generate_memory_id(
            target_name=target_name,
            item_date=normalized["date"],
            lesson=normalized["lesson"],
            existing_ids={item.fields.get("id", "") for item in memory.items},
        )

    validate_memory_fields(normalized)
    target = repo_root / MEMORY_DIR / target_name
    target.parent.mkdir(parents=True, exist_ok=True)
    append_memory_item(target, normalized)

    updated = load_memory_state(repo_root)
    report = validate_memory_state(updated)
    if not report.ok:
        raise ValueError("Memory validation failed after add: " + "; ".join(report.errors))

    return MemoryWriteResult(item_id=normalized["id"], path=target, action="added")


def deprecate_memory_item(
    root: Path | None,
    item_id: str,
    reason: str,
    replacement: str = "",
    current_date: date | None = None,
) -> MemoryWriteResult:
    repo_root = find_repo_root(root)
    memory = load_memory_state(repo_root)
    matches = [item for item in memory.items if item.fields.get("id") == item_id]
    if not matches:
        raise ValueError(f"Memory item not found: {item_id}")
    if len(matches) > 1:
        raise ValueError(f"Duplicate memory item id prevents safe deprecation: {item_id}")

    item = matches[0]
    item_date = current_date or date.today()
    update_memory_item_field(item.path, item_id, "status", "deprecated")

    action_path = item.path
    if item.path.name != "deprecated_memory.md":
        deprecated_fields = {
            "id": generate_memory_id(
                target_name="deprecated_memory.md",
                item_date=item_date.isoformat(),
                lesson=item.fields.get("lesson", item_id),
                existing_ids={existing.fields.get("id", "") for existing in memory.items},
            ),
            "date": item_date.isoformat(),
            "type": item.fields.get("type", "procedural"),
            "scope": item.fields.get("scope", "global"),
            "status": "deprecated",
            "confidence": item.fields.get("confidence", "medium"),
            "trigger/source": reason,
            "lesson": item.fields.get("lesson", item_id),
            "use_when": "Checking whether a superseded operational path is being reintroduced.",
            "do_not_use_when": replacement or "Do not use unless the user explicitly reverses this deprecation.",
            "evidence": f"`{relative_to_root(repo_root, item.path).as_posix()}`",
            "owner": item.fields.get("owner", "memory and evaluation orchestrator"),
            "next_review": item_date.isoformat(),
        }
        validate_memory_fields(deprecated_fields)
        action_path = repo_root / MEMORY_DIR / "deprecated_memory.md"
        append_memory_item(action_path, deprecated_fields)

    updated = load_memory_state(repo_root)
    report = validate_memory_state(updated)
    if not report.ok:
        raise ValueError("Memory validation failed after deprecate: " + "; ".join(report.errors))

    return MemoryWriteResult(item_id=item_id, path=action_path, action="deprecated")


def normalize_memory_fields(fields: dict[str, str], item_date: date) -> dict[str, str]:
    result = {key: value.strip() for key, value in fields.items()}
    result.setdefault("id", "")
    result.setdefault("date", item_date.isoformat())
    result.setdefault("status", "active")
    result.setdefault("confidence", "medium")
    return result


def resolve_memory_file(fields: dict[str, str], memory_file: str | None) -> str:
    if memory_file:
        if memory_file not in REQUIRED_MEMORY_FILES:
            raise ValueError(f"Invalid memory file: {memory_file}")
        if memory_file not in ITEM_MEMORY_FILES:
            raise ValueError(f"Memory file does not accept structured items: {memory_file}")
        return memory_file
    if fields.get("status") == "deprecated":
        return "deprecated_memory.md"
    return TYPE_MEMORY_FILE_MAP.get(fields.get("type", ""), "orchestrator_lessons.md")


def validate_memory_fields(fields: dict[str, str]) -> None:
    missing = [field for field in REQUIRED_ITEM_FIELDS if not fields.get(field)]
    if missing:
        raise ValueError("Missing required memory field(s): " + ", ".join(missing))
    if fields["type"] not in VALID_MEMORY_TYPES:
        raise ValueError(f"Invalid memory type: {fields['type']}")
    if fields["scope"] not in VALID_MEMORY_SCOPES:
        raise ValueError(f"Invalid memory scope: {fields['scope']}")
    if fields["status"] not in VALID_MEMORY_STATUSES:
        raise ValueError(f"Invalid memory status: {fields['status']}")
    if fields["confidence"] not in VALID_MEMORY_CONFIDENCE:
        raise ValueError(f"Invalid memory confidence: {fields['confidence']}")


def append_memory_item(path: Path, fields: dict[str, str]) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else f"# {path.stem}\n"
    item_text = format_memory_item(fields)
    separator = "\n\n" if text.strip() else ""
    path.write_text(text.rstrip() + separator + item_text + "\n", encoding="utf-8")


def format_memory_item(fields: dict[str, str]) -> str:
    ordered = ["id", *[field for field in REQUIRED_ITEM_FIELDS if field != "id"]]
    return "\n".join(f"- {field}: {fields.get(field, '')}" for field in ordered)


def update_memory_item_field(path: Path, item_id: str, field: str, value: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    start: int | None = None
    end = len(lines)

    for index, line in enumerate(lines):
        if line.strip() == f"- id: {item_id}":
            start = index
            break
    if start is None:
        raise ValueError(f"Memory item not found in {path}: {item_id}")

    for index in range(start + 1, len(lines)):
        if lines[index].strip().startswith("- id: "):
            end = index
            break

    target_prefix = f"- {field}:"
    for index in range(start, end):
        if lines[index].strip().startswith(target_prefix):
            lines[index] = f"- {field}: {value}"
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return

    insert_at = end
    lines.insert(insert_at, f"- {field}: {value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_memory_id(target_name: str, item_date: str, lesson: str, existing_ids: set[str]) -> str:
    prefix = MEMORY_FILE_PREFIXES.get(target_name, "memory")
    slug = slugify(lesson)[:48].strip("-") or "item"
    base = f"{prefix}-{item_date}-{slug}"
    candidate = base
    counter = 2
    while candidate in existing_ids:
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def relative_to_root(root: Path, path: Path) -> Path:
    try:
        return path.relative_to(root)
    except ValueError:
        return path
