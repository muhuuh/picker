from __future__ import annotations

import re


def validate_human_facing_markdown(text: str) -> list[str]:
    findings: list[str] = []
    if "[...]" in text or re.search(r"\w\.\.\.(?:\s|$)", text):
        findings.append("Visible truncation marker found.")
    if re.search(r"[\u00c2\u00c3\u00e2\ufffd]", text):
        findings.append("Mojibake or encoding artifact found.")
    if re.search(
        r"(?:\([^)]*\b(?:up|down|from|during|with)\.|\b(?:hig|implying|compared|indust|announc|subsequen|preliminar|approxim|financ|operat|developm)\.|\b(?:is|are|was|were|be|while)\.)",
        text,
        flags=re.IGNORECASE,
    ):
        findings.append("Dangling sentence fragment found.")
    if re.search(r"(?<!\!)\[[0-9]+\](?!\()", text):
        findings.append("Dead numeric citation marker found.")
    if re.search(r"\[[a-z0-9_:-]+\](?!\()", text, flags=re.IGNORECASE):
        findings.append("Bracketed source id without link found.")
    if re.search(r"\{['\"][a-zA-Z_]+['\"]\s*:", text):
        findings.append("Raw dict/JSON-like object found in human-facing prose.")
    headings = [line.strip().lower() for line in text.splitlines() if line.startswith("## ")]
    duplicates = sorted({heading for heading in headings if headings.count(heading) > 1})
    if duplicates:
        findings.append(f"Duplicate top-level sections found: {', '.join(duplicates)}.")
    repeated = repeated_long_claims(text)
    if repeated:
        findings.append(f"Repeated long claims found: {'; '.join(repeated[:3])}.")
    if "Grok/X social signal:" in text and not re.search(r"\b(Bullish|Bearish|X pulse|Community pulse|Expert / Community)", text):
        findings.append("Status-only Grok/X social signal found without narrative context.")
    if re.search(r"\b(run|provider|lane)\s+status\b", text, flags=re.IGNORECASE) and "## Audit" not in text:
        findings.append("Internal workflow status appears outside an audit section.")
    findings.extend(validate_final_human_report_contract(text))
    return findings


def validate_final_human_report_contract(text: str) -> list[str]:
    if not is_final_human_report(text):
        return []

    findings: list[str] = []
    normalized = text.lower()
    if "this report is a codex-written synthesis from" not in normalized:
        findings.append("Final human report is missing the established Codex synthesis provenance paragraph.")
    if "deterministic opportunity assessment remains the audit artifact" not in normalized:
        findings.append("Final human report does not identify the deterministic opportunity assessment as the audit artifact.")

    headings = [line.strip() for line in text.splitlines() if line.startswith("## ")]
    heading_set = {heading.lower() for heading in headings}
    missing_sections = [
        heading
        for heading in [
            "## Bottom Line",
            "## Why The Setup Changed",
            "## X Sentiment And What It Is Really Saying",
            "## Financial And Valuation Read",
            "## Bull Case",
            "## Bear Case",
            "## What Would Change The Thesis",
            "## Next Research Checks",
            "## Final Assessment",
            "## Sources",
        ]
        if heading.lower() not in heading_set
    ]
    if not any(re.fullmatch(r"## What .+ Actually Does", heading) for heading in headings):
        missing_sections.append("## What [Company] Actually Does")
    if missing_sections:
        findings.append(
            "Final human report is missing established synthesis sections: "
            + ", ".join(missing_sections)
            + "."
        )
    findings.extend(validate_final_human_report_depth(text))
    return findings


def validate_final_human_report_depth(text: str) -> list[str]:
    normalized = text.lower()
    words = re.findall(r"\b[\w./$%-]+\b", text)
    findings: list[str] = []
    if len(words) < 1700:
        findings.append("Final human report is too short to preserve opportunity-assessment depth.")

    required_depth_markers = {
        "source-backed or verified facts": ("source-backed", "verified facts", "source-backed facts", "verified company"),
        "notable X/social accounts or source-quality context": ("notable accounts", "accounts/posts", "informed accounts", "recurring accounts"),
        "rumors or unverified claims separated from facts": ("rumor", "rumors", "unverified", "speculation"),
        "non-obvious or under-discussed angles": ("non-obvious", "under-discussed", "underdiscussed", "hidden optionality"),
        "decision table or investor scorecard": ("decision table", "scorecard", "| signal | evidence |", "| decision area | current read |"),
    }
    missing_markers = [
        label
        for label, markers in required_depth_markers.items()
        if not any(marker in normalized for marker in markers)
    ]
    if missing_markers:
        findings.append(
            "Final human report is missing opportunity-assessment depth markers: "
            + ", ".join(missing_markers)
            + "."
        )
    return findings


def is_final_human_report(text: str) -> bool:
    first_heading = next((line.strip() for line in text.splitlines() if line.startswith("# ")), "")
    return bool(re.search(r"\bfinal human report\b", first_heading, flags=re.IGNORECASE))


def repeated_long_claims(text: str) -> list[str]:
    seen: dict[str, str] = {}
    repeated: list[str] = []
    for claim in iter_report_claims(text):
        key = normalize_claim(claim)
        if len(key.split()) < 12:
            continue
        if key in seen and seen[key] not in repeated:
            repeated.append(seen[key])
            continue
        seen[key] = claim
    return repeated


def iter_report_claims(text: str) -> list[str]:
    claims: list[str] = []
    ignored_section = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            ignored_section = line.lower() in {"## sources", "## audit"}
            continue
        if ignored_section:
            continue
        if not line or line.startswith(("#", "| ---", "```")):
            continue
        if line.startswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|") if cell.strip()]
            claims.extend(cell for cell in cells if len(cell.split()) >= 8)
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        line = re.sub(r"^[A-Za-z /_-]{2,35}:\s+", "", line)
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = sentence.strip()
            if len(sentence.split()) >= 8:
                claims.append(sentence)
    return claims


def normalize_claim(value: str) -> str:
    normalized = re.sub(r"\[[^\]]+\]\([^)]+\)", "", value.lower())
    normalized = re.sub(r"\[\[\d+\]\](?:\([^)]+\))?", "", normalized)
    normalized = re.sub(r"(?<!\!)\[(\d+)\](?!\()", "", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return " ".join(normalized.split())
