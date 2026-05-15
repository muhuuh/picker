from __future__ import annotations

import re


def validate_human_facing_markdown(text: str) -> list[str]:
    findings: list[str] = []
    if "[...]" in text or re.search(r"\w\.\.\.(?:\s|$)", text):
        findings.append("Visible truncation marker found.")
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
    if "Grok/X social signal:" in text and not re.search(r"\b(Bullish|Bearish|X pulse|Community pulse|Expert / Community)", text):
        findings.append("Status-only Grok/X social signal found without narrative context.")
    if re.search(r"\b(run|provider|lane)\s+status\b", text, flags=re.IGNORECASE) and "## Audit" not in text:
        findings.append("Internal workflow status appears outside an audit section.")
    return findings
