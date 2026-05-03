from __future__ import annotations

from pathlib import Path


def append_markdown_table_row(path: Path, header_prefix: str, row: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    table_end = find_table_end(lines, header_prefix)
    escaped = [cell.replace("|", "/").replace("\n", " ").strip() for cell in row]
    lines.insert(table_end, "| " + " | ".join(escaped) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def find_table_end(lines: list[str], header_prefix: str) -> int:
    for index, line in enumerate(lines):
        if line.startswith(header_prefix):
            table_end = index + 2
            while table_end < len(lines) and lines[table_end].startswith("|"):
                table_end += 1
            return table_end
    raise ValueError(f"Could not find markdown table starting with: {header_prefix}")


def append_section_entry(path: Path, heading: str, entry: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if heading not in text:
        if text and not text.endswith("\n"):
            text += "\n"
        text += f"\n{heading}\n\n"
    if not text.endswith("\n"):
        text += "\n"
    text += entry.rstrip() + "\n"
    path.write_text(text, encoding="utf-8")
