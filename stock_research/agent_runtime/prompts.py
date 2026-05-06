from __future__ import annotations

from pathlib import Path


def load_prompt(root: Path, relative_path: str, fallback: str) -> str:
    path = root / relative_path
    if path.exists():
        text = path.read_text(encoding="utf-8").strip()
        if text:
            return text
    return fallback.strip()


def with_memory(prompt: str, memory_context: str) -> str:
    if not memory_context.strip():
        return prompt
    return f"{prompt.rstrip()}\n\n{memory_context.strip()}"
