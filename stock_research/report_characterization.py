from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
import re
from typing import Mapping

from .report_quality import iter_report_claims, normalize_claim, repeated_long_claims, validate_human_facing_markdown


@dataclass(frozen=True)
class CorpusQualityFinding:
    category: str
    summary: str
    evidence_paths: tuple[str, ...]
    excerpt: str = ""


@dataclass(frozen=True)
class ReaderValueResult:
    dimension: str
    passed: bool
    reason: str
    required: bool = True


@dataclass(frozen=True)
class ClaimOccurrence:
    report_path: str
    claim: str
    normalized: str


ALLOWED_SHARED_CLAIM_PREFIXES = (
    "this report is a codex written synthesis from",
    "the deterministic opportunity assessment remains the audit artifact",
)


READER_VALUE_RUBRIC: tuple[dict[str, str], ...] = (
    {
        "dimension": "material_change",
        "pass_condition": "The report leads with what changed, why it matters, and what did not change materially.",
    },
    {
        "dimension": "specificity",
        "pass_condition": "Claims, thesis implications, and next checks are specific to the company or industry.",
    },
    {
        "dimension": "source_quality",
        "pass_condition": "Material facts are source-backed and social or speculative claims remain clearly labeled.",
    },
    {
        "dimension": "x_insight",
        "pass_condition": "X coverage identifies concrete narratives, expert accounts/posts, disagreements, and verification work.",
    },
    {
        "dimension": "reader_efficiency",
        "pass_condition": "Stable background and workflow boilerplate do not crowd out decision-relevant deltas.",
    },
    {
        "dimension": "completeness",
        "pass_condition": "Reader-facing prose contains complete claims rather than clipped excerpts or repaired truncation.",
    },
)


def characterize_report_corpus(
    reports: Mapping[str, str],
    *,
    minimum_report_count: int = 3,
    minimum_words: int = 12,
) -> list[CorpusQualityFinding]:
    findings: list[CorpusQualityFinding] = []
    for claim, paths in repeated_claims_across_reports(
        reports,
        minimum_report_count=minimum_report_count,
        minimum_words=minimum_words,
    ):
        findings.append(
            CorpusQualityFinding(
                category="cross_report_boilerplate",
                summary=f"The same long reader claim appears in {len(paths)} reports.",
                evidence_paths=paths,
                excerpt=claim,
            )
        )
    for claim, paths in near_duplicate_claims_across_reports(
        reports,
        minimum_report_count=minimum_report_count,
        minimum_words=minimum_words,
    ):
        findings.append(
            CorpusQualityFinding(
                category="cross_report_near_boilerplate",
                summary=f"A lightly varied reader claim appears in {len(paths)} reports.",
                evidence_paths=paths,
                excerpt=claim,
            )
        )
    return findings


def repeated_claims_across_reports(
    reports: Mapping[str, str],
    *,
    minimum_report_count: int = 3,
    minimum_words: int = 12,
) -> list[tuple[str, tuple[str, ...]]]:
    occurrences: dict[str, dict[str, str]] = {}
    for report_path, text in sorted(reports.items()):
        seen_in_report: set[str] = set()
        for claim in iter_report_claims(text):
            normalized = normalize_claim(claim)
            if len(normalized.split()) < minimum_words or normalized in seen_in_report:
                continue
            if any(normalized.startswith(prefix) for prefix in ALLOWED_SHARED_CLAIM_PREFIXES):
                continue
            seen_in_report.add(normalized)
            occurrences.setdefault(normalized, {})[report_path] = claim

    repeated: list[tuple[str, tuple[str, ...]]] = []
    for normalized, report_claims in occurrences.items():
        if len(report_claims) < minimum_report_count:
            continue
        paths = tuple(sorted(report_claims))
        excerpt = report_claims[paths[0]]
        repeated.append((excerpt, paths))
    repeated.sort(key=lambda item: (-len(item[1]), normalize_claim(item[0])))
    return repeated


def load_markdown_reports(paths: list[Path]) -> dict[str, str]:
    return {path.as_posix(): path.read_text(encoding="utf-8") for path in paths}


def near_duplicate_claims_across_reports(
    reports: Mapping[str, str],
    *,
    minimum_report_count: int = 3,
    minimum_words: int = 12,
    similarity_threshold: float = 0.82,
) -> list[tuple[str, tuple[str, ...]]]:
    occurrences: list[ClaimOccurrence] = []
    exact_paths: dict[str, set[str]] = {}
    for report_path, text in sorted(reports.items()):
        subject_tokens = subject_tokens_from_path(report_path)
        seen: set[str] = set()
        for claim in iter_report_claims(text):
            normalized = normalize_for_similarity(claim, subject_tokens)
            if len(normalized.split()) < minimum_words or normalized in seen:
                continue
            if any(normalized.startswith(prefix) for prefix in ALLOWED_SHARED_CLAIM_PREFIXES):
                continue
            seen.add(normalized)
            exact_paths.setdefault(normalized, set()).add(report_path)
            occurrences.append(ClaimOccurrence(report_path, claim, normalized))

    parent = list(range(len(occurrences)))
    token_sets = [set(occurrence.normalized.split()) for occurrence in occurrences]

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for left_index, left in enumerate(occurrences):
        for right_index in range(left_index + 1, len(occurrences)):
            right = occurrences[right_index]
            if left.report_path == right.report_path or left.normalized == right.normalized:
                continue
            if word_count_ratio(left.normalized, right.normalized) < 0.72:
                continue
            left_tokens = token_sets[left_index]
            right_tokens = token_sets[right_index]
            shared_token_count = len(left_tokens & right_tokens)
            overlap_coefficient = shared_token_count / max(1, min(len(left_tokens), len(right_tokens)))
            if overlap_coefficient < 0.55:
                continue
            union_token_count = len(left_tokens | right_tokens)
            jaccard = shared_token_count / union_token_count if union_token_count else 0.0
            if jaccard >= similarity_threshold or SequenceMatcher(
                None,
                left.normalized,
                right.normalized,
                autojunk=False,
            ).ratio() >= similarity_threshold:
                union(left_index, right_index)

    groups: dict[int, list[ClaimOccurrence]] = {}
    for index, occurrence in enumerate(occurrences):
        groups.setdefault(find(index), []).append(occurrence)

    results: list[tuple[str, tuple[str, ...]]] = []
    seen_groups: set[tuple[str, ...]] = set()
    for group in groups.values():
        paths = tuple(sorted({item.report_path for item in group}))
        if len(paths) < minimum_report_count or paths in seen_groups:
            continue
        if any(len(exact_paths.get(item.normalized, set())) >= minimum_report_count for item in group):
            continue
        seen_groups.add(paths)
        excerpt = sorted(group, key=lambda item: (item.report_path, item.claim))[0].claim
        results.append((excerpt, paths))
    results.sort(key=lambda item: (-len(item[1]), normalize_claim(item[0])))
    return results


def evaluate_reader_value(
    text: str,
    *,
    subject_terms: tuple[str, ...] = (),
    require_x_insight: bool = True,
) -> tuple[ReaderValueResult, ...]:
    normalized = " ".join(str(text or "").lower().split())
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    change_signal = bool(
        re.search(r"\b(chang(?:e|ed)|shift(?:ed)?|new|reported|announced|increased|declined|expanded|accelerat(?:ed|ing))\b", normalized)
    )
    impact_signal = bool(
        re.search(r"\b(matters?|implication|read-through|because|therefore|risk|decision|verify|confirm|invalidate)\b", normalized)
    )
    subject_signal = not subject_terms or any(term.lower() in normalized for term in subject_terms if term.strip())
    concrete_anchors = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", text)) + len(re.findall(r"@[A-Za-z0-9_]{2,}", text)) + len(links)
    source_context = bool(re.search(r"\b(source|filing|investor relations|company disclosure|verify|verified|primary|social|unverified)\b", normalized))
    x_links = [link for link in links if "x.com/" in link.lower()]
    x_context = bool(re.search(r"\b(debate|disagree|credible|promotional|noise|narrative|bull|bear|skeptic|account|post)\b", normalized))
    handles = re.findall(r"@[A-Za-z0-9_]{2,}", text)
    repeated = repeated_long_claims(text)
    repetition_ratio = repeated_ngram_ratio(text)
    structural_findings = validate_human_facing_markdown(text)
    completeness_findings = [
        finding
        for finding in structural_findings
        if any(marker in finding for marker in ("truncation", "Dangling", "Mojibake", "Raw dict", "citation"))
    ]

    return (
        ReaderValueResult(
            "material_change",
            change_signal and impact_signal,
            "Contains both a concrete change and its decision relevance."
            if change_signal and impact_signal
            else "Missing a concrete change or why it matters.",
        ),
        ReaderValueResult(
            "specificity",
            subject_signal and concrete_anchors >= 2,
            "Names the subject and includes multiple concrete anchors."
            if subject_signal and concrete_anchors >= 2
            else "Insufficient subject-specific numbers, handles, or source links.",
        ),
        ReaderValueResult(
            "source_quality",
            bool(links) and source_context,
            "Links evidence and explains its verification/source status."
            if links and source_context
            else "Missing linked evidence or verification/source context.",
        ),
        ReaderValueResult(
            "x_insight",
            (bool(x_links or handles) and x_context) if require_x_insight else True,
            (
                "Names X accounts/posts and explains the narrative or credibility split."
                if (x_links or handles) and x_context
                else "Missing concrete X accounts/posts or narrative/source-quality interpretation."
            )
            if require_x_insight
            else "Not required for this source-specific excerpt.",
            required=require_x_insight,
        ),
        ReaderValueResult(
            "reader_efficiency",
            not repeated and repetition_ratio <= 0.35,
            "Avoids repeated claims and excessive phrase recycling."
            if not repeated and repetition_ratio <= 0.35
            else "Contains repeated claims or excessive phrase recycling.",
        ),
        ReaderValueResult(
            "completeness",
            not completeness_findings,
            "Contains complete, readable evidence statements."
            if not completeness_findings
            else "; ".join(completeness_findings),
        ),
    )


def normalize_for_similarity(claim: str, subject_tokens: set[str]) -> str:
    normalized = normalize_claim(claim)
    tokens = ["subject" if token in subject_tokens else "number" if token.isdigit() else token for token in normalized.split()]
    return " ".join(tokens)


def subject_tokens_from_path(path: str) -> set[str]:
    stem = Path(path).stem.lower()
    subject = stem.split("_", 1)[0]
    return {token for token in re.split(r"[^a-z0-9]+", subject) if token}


def word_count_ratio(left: str, right: str) -> float:
    left_count = max(1, len(left.split()))
    right_count = max(1, len(right.split()))
    return min(left_count, right_count) / max(left_count, right_count)


def repeated_ngram_ratio(text: str, n: int = 5) -> float:
    tokens = normalize_claim(text).split()
    if len(tokens) < max(40, n * 2):
        return 0.0
    ngrams = [tuple(tokens[index : index + n]) for index in range(len(tokens) - n + 1)]
    if not ngrams:
        return 0.0
    return 1.0 - (len(set(ngrams)) / len(ngrams))
