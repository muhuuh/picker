from __future__ import annotations

from dataclasses import dataclass
import re


TRUNCATION_MARKERS = ("[...]", "...")
SUSPICIOUS_TAIL_WORDS = {
    "and",
    "as",
    "at",
    "because",
    "by",
    "during",
    "for",
    "from",
    "if",
    "including",
    "machine",
    "of",
    "or",
    "to",
    "while",
    "with",
}
SUSPICIOUS_CUT_STEMS = (
    "announc",
    "approxim",
    "developm",
    "financ",
    "hig",
    "indust",
    "operat",
    "preliminar",
    "subsequen",
)
SAFE_SHORT_ABBREVIATIONS = {"a.m.", "e.g.", "i.e.", "inc.", "ltd.", "p.m.", "u.k.", "u.s.", "vs."}
SUSPICIOUS_SHORT_TAILS = {"sh"}


@dataclass(frozen=True)
class ExcerptResult:
    text: str
    shortened: bool
    complete: bool
    reason: str = ""


def complete_sentence_excerpt(
    value: str,
    max_length: int = 600,
    *,
    allow_complete_phrase: bool = False,
) -> ExcerptResult:
    """Return bounded complete sentences without inventing or hiding punctuation.

    The original value remains the canonical evidence. When no complete sentence can
    fit within a modest overrun of the display limit, the excerpt is intentionally
    empty so callers can link to the preserved full evidence instead of fabricating a
    sentence ending.
    """

    text = normalize_excerpt_text(value)
    if not text:
        return ExcerptResult(text="", shortened=False, complete=True)

    if len(text) <= max_length:
        reasons = incomplete_segment_reasons(text)
        if not reasons and (has_terminal_sentence_punctuation(text) or allow_complete_phrase):
            return ExcerptResult(text=text, shortened=False, complete=True)
        previous = last_complete_boundary(text, len(text), exclude_final=True)
        if previous > 0:
            return ExcerptResult(
                text=text[:previous].rstrip(),
                shortened=True,
                complete=True,
                reason="source_tail_is_incomplete",
            )
        return ExcerptResult(
            text="",
            shortened=True,
            complete=False,
            reason="source_contains_no_complete_sentence",
        )

    boundary = last_complete_boundary(text, max_length)
    if boundary >= max(40, int(max_length * 0.35)):
        return ExcerptResult(
            text=text[:boundary].rstrip(),
            shortened=True,
            complete=True,
            reason="display_limit",
        )

    forward_limit = min(len(text), max(max_length + 1, int(max_length * 1.6)))
    forward_boundary = first_complete_boundary_after(text, max_length, forward_limit)
    if forward_boundary > 0:
        return ExcerptResult(
            text=text[:forward_boundary].rstrip(),
            shortened=True,
            complete=True,
            reason="completed_first_sentence_beyond_display_limit",
        )

    return ExcerptResult(
        text="",
        shortened=True,
        complete=False,
        reason="no_complete_sentence_within_display_budget",
    )


def normalize_excerpt_text(value: str) -> str:
    return " ".join(str(value or "").split())


def incomplete_segment_reasons(value: str) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    reasons: list[str] = []
    lowered = text.lower()
    if "[...]" in text or re.search(r"\w\.\.\.(?:\s|$)", text):
        reasons.append("visible_truncation_marker")
    if unbalanced_delimiters(text):
        reasons.append("unbalanced_delimiter")

    final_line = next((line.strip() for line in reversed(text.splitlines()) if line.strip()), text)
    final_cell = final_line.strip().strip("|").split("|")[-1].strip()
    final_cell = re.sub(r"\[[^\]]+\]\([^)]+\)\s*$", "", final_cell).strip()
    lower_cell = final_cell.lower()
    if lower_cell in SAFE_SHORT_ABBREVIATIONS:
        return list(dict.fromkeys(reasons))

    match = re.search(r"([A-Za-z]+)\.\s*$", final_cell)
    if match:
        word = match.group(1).lower()
        if word in SUSPICIOUS_TAIL_WORDS:
            reasons.append(f"suspicious_tail_word:{word}")
        if word in SUSPICIOUS_SHORT_TAILS:
            reasons.append(f"suspicious_short_tail:{word}")
        if any(word == stem or word.endswith(stem) for stem in SUSPICIOUS_CUT_STEMS):
            reasons.append(f"suspicious_cut_stem:{word}")

    return list(dict.fromkeys(reasons))


def incomplete_markdown_segments(text: str) -> list[tuple[int, str, tuple[str, ...]]]:
    findings: list[tuple[int, str, tuple[str, ...]]] = []
    in_code_block = False
    for line_number, raw_line in enumerate(str(text or "").splitlines(), start=1):
        stripped = raw_line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or not stripped or stripped.startswith("#") or stripped.startswith("| ---"):
            continue
        segments = [stripped]
        if stripped.startswith("|"):
            segments = [cell.strip() for cell in stripped.strip("|").split("|") if cell.strip()]
        for segment in segments:
            cleaned = re.sub(r"^[-*]\s+", "", segment).strip()
            reasons = incomplete_segment_reasons(cleaned)
            if reasons:
                findings.append((line_number, cleaned, tuple(reasons)))
    return findings


def sentence_boundaries(value: str) -> list[int]:
    boundaries: list[int] = []
    for match in re.finditer(r"[.!?](?=\s|$)", value):
        index = match.start()
        if value[max(0, index - 2) : index + 1].endswith("..."):
            continue
        prefix = value[max(0, match.end() - 6) : match.end()].lower()
        has_following_text = bool(value[match.end() :].strip())
        if has_following_text and any(prefix.endswith(abbreviation) for abbreviation in SAFE_SHORT_ABBREVIATIONS):
            continue
        candidate = value[: match.end()].rstrip()
        if incomplete_segment_reasons(candidate):
            continue
        boundaries.append(match.end())
    return boundaries


def last_complete_boundary(value: str, limit: int, *, exclude_final: bool = False) -> int:
    boundaries = sentence_boundaries(value)
    if exclude_final and boundaries and boundaries[-1] == len(value.rstrip()):
        boundaries = boundaries[:-1]
    eligible = [boundary for boundary in boundaries if boundary <= limit]
    return max(eligible) if eligible else -1


def first_complete_boundary_after(value: str, minimum: int, maximum: int) -> int:
    return next((boundary for boundary in sentence_boundaries(value) if minimum < boundary <= maximum), -1)


def unbalanced_delimiters(value: str) -> bool:
    return any(value.count(open_char) != value.count(close_char) for open_char, close_char in (("(", ")"), ("[", "]")))


def has_terminal_sentence_punctuation(value: str) -> bool:
    return bool(re.search(r"[.!?][)\]\"'`]*\s*$", value))
