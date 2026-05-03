from __future__ import annotations


def parse_markdown_tables(text: str) -> list[list[dict[str, str]]]:
    """Parse simple GitHub-style markdown tables.

    This intentionally supports only the table shape used by repo planning files.
    It does not try to parse nested pipes or multiline cells.
    """
    lines = text.splitlines()
    tables: list[list[dict[str, str]]] = []
    index = 0

    while index < len(lines) - 1:
        current = lines[index].strip()
        next_line = lines[index + 1].strip()
        if _is_table_row(current) and _is_separator_row(next_line):
            headers = _split_row(current)
            index += 2
            rows: list[dict[str, str]] = []
            while index < len(lines) and _is_table_row(lines[index].strip()):
                values = _split_row(lines[index].strip())
                row = {header: values[pos] if pos < len(values) else "" for pos, header in enumerate(headers)}
                rows.append(row)
                index += 1
            tables.append(rows)
            continue
        index += 1

    return tables


def first_markdown_table(text: str) -> list[dict[str, str]]:
    tables = parse_markdown_tables(text)
    return tables[0] if tables else []


def _is_table_row(line: str) -> bool:
    return line.startswith("|") and line.endswith("|")


def _is_separator_row(line: str) -> bool:
    if not _is_table_row(line):
        return False
    cells = _split_row(line)
    return bool(cells) and all(set(cell.replace(":", "").strip()) <= {"-"} and "-" in cell for cell in cells)


def _split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]
