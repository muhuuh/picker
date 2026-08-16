from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any


SUBJECT_TYPES = {"company", "industry", "theme", "macro", "strategy", "portfolio", "provider_test"}
SOURCE_TYPES = {
    "filing",
    "market_data",
    "news",
    "web",
    "social",
    "macro_data",
    "transcript",
    "internal",
    "other",
}
CONFIDENCE_VALUES = {"low", "medium", "high", "unknown"}
IMPACT_VALUES = {"low", "medium", "high", "urgent", "unknown"}
UPDATE_TYPES = {"company_file", "category_state", "csv_row", "strategy", "market_research", "human_review", "none"}


@dataclass(frozen=True)
class Source:
    source_id: str
    provider: str
    source_type: str
    title: str = ""
    url: str = ""
    publisher: str = ""
    published_at: str = ""
    accessed_at: str = ""
    artifact_path: str = ""
    notes: str = ""


@dataclass(frozen=True)
class Claim:
    claim: str
    evidence: str
    source_ids: list[str]
    confidence: str = "unknown"
    impact: str = "unknown"
    novelty: str = "unknown"
    display_excerpt: str = ""
    full_evidence_path: str = ""
    full_evidence_selector: str = ""


@dataclass(frozen=True)
class Risk:
    risk: str
    evidence: str
    source_ids: list[str]
    severity: str = "unknown"
    time_horizon: str = "unknown"


@dataclass(frozen=True)
class Contradiction:
    current_repo_claim: str
    new_evidence: str
    source_ids: list[str]
    suggested_action: str


@dataclass(frozen=True)
class RecommendedUpdate:
    target_file: str
    update_type: str
    summary: str
    needs_human_review: bool = False
    source_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidencePacket:
    packet_id: str
    created_at: str
    provider: str
    subject_type: str
    subject_id: str
    time_window: str
    sources: list[Source] = field(default_factory=list)
    claims: list[Claim] = field(default_factory=list)
    risks: list[Risk] = field(default_factory=list)
    contradictions: list[Contradiction] = field(default_factory=list)
    recommended_updates: list[RecommendedUpdate] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    raw_artifact_path: str = ""
    notes: str = ""


@dataclass
class EvidenceValidationReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def make_packet_id(provider: str, subject_type: str, subject_id: str, current_date: date | None = None) -> str:
    day = (current_date or date.today()).isoformat()
    safe_provider = slugify(provider)
    safe_subject = slugify(subject_id or "unknown")
    safe_type = slugify(subject_type)
    return f"{day}_{safe_provider}_{safe_type}_{safe_subject}"


def new_packet(
    provider: str,
    subject_type: str,
    subject_id: str,
    time_window: str = "unspecified",
    current_date: date | None = None,
    **kwargs: Any,
) -> EvidencePacket:
    today = current_date or date.today()
    return EvidencePacket(
        packet_id=make_packet_id(provider, subject_type, subject_id, today),
        created_at=datetime.combine(today, datetime.min.time()).isoformat(),
        provider=provider,
        subject_type=subject_type,
        subject_id=subject_id,
        time_window=time_window,
        **kwargs,
    )


def validate_packet(packet: EvidencePacket) -> EvidenceValidationReport:
    report = EvidenceValidationReport()
    if packet.subject_type not in SUBJECT_TYPES:
        report.errors.append(f"Invalid subject_type '{packet.subject_type}'.")
    if not packet.provider:
        report.errors.append("provider is required.")
    if not packet.subject_id:
        report.errors.append("subject_id is required.")
    if not packet.time_window:
        report.errors.append("time_window is required.")

    source_ids = set()
    for source in packet.sources:
        if not source.source_id:
            report.errors.append("source_id is required for every source.")
        if source.source_id in source_ids:
            report.errors.append(f"Duplicate source_id '{source.source_id}'.")
        source_ids.add(source.source_id)
        if source.source_type not in SOURCE_TYPES:
            report.errors.append(f"Invalid source_type '{source.source_type}' for source {source.source_id}.")
        if not source.url and not source.artifact_path:
            report.warnings.append(f"Source {source.source_id} has no url or artifact_path.")

    for claim in packet.claims:
        validate_source_refs("claim", claim.claim, claim.source_ids, source_ids, report)
        if claim.confidence not in CONFIDENCE_VALUES:
            report.errors.append(f"Invalid claim confidence '{claim.confidence}'.")
        if claim.impact not in IMPACT_VALUES:
            report.errors.append(f"Invalid claim impact '{claim.impact}'.")
        if claim.display_excerpt and len(claim.display_excerpt) < len(claim.evidence) and not claim.full_evidence_path:
            report.warnings.append(
                f"claim '{claim.claim}' has a shortened display_excerpt but no full_evidence_path."
            )
        if claim.full_evidence_path and not claim.evidence:
            report.warnings.append(f"claim '{claim.claim}' links full evidence but has no canonical evidence text.")

    for risk in packet.risks:
        validate_source_refs("risk", risk.risk, risk.source_ids, source_ids, report)
        if risk.severity not in IMPACT_VALUES:
            report.errors.append(f"Invalid risk severity '{risk.severity}'.")

    for contradiction in packet.contradictions:
        validate_source_refs("contradiction", contradiction.current_repo_claim, contradiction.source_ids, source_ids, report)

    for update in packet.recommended_updates:
        if update.update_type not in UPDATE_TYPES:
            report.errors.append(f"Invalid update_type '{update.update_type}'.")
        validate_source_refs("recommended_update", update.summary, update.source_ids, source_ids, report)

    return report


def validate_source_refs(
    kind: str,
    label: str,
    refs: list[str],
    source_ids: set[str],
    report: EvidenceValidationReport,
) -> None:
    if not refs:
        report.warnings.append(f"{kind} '{label}' has no source_ids.")
    for source_id in refs:
        if source_id not in source_ids:
            report.errors.append(f"{kind} '{label}' references unknown source_id '{source_id}'.")


def packet_to_dict(packet: EvidencePacket) -> dict[str, Any]:
    return asdict(packet)


def packet_from_dict(data: dict[str, Any]) -> EvidencePacket:
    return EvidencePacket(
        packet_id=data["packet_id"],
        created_at=data["created_at"],
        provider=data["provider"],
        subject_type=data["subject_type"],
        subject_id=data["subject_id"],
        time_window=data["time_window"],
        sources=[Source(**source) for source in data.get("sources", [])],
        claims=[Claim(**claim) for claim in data.get("claims", [])],
        risks=[Risk(**risk) for risk in data.get("risks", [])],
        contradictions=[Contradiction(**item) for item in data.get("contradictions", [])],
        recommended_updates=[RecommendedUpdate(**item) for item in data.get("recommended_updates", [])],
        unknowns=list(data.get("unknowns", [])),
        raw_artifact_path=data.get("raw_artifact_path", ""),
        notes=data.get("notes", ""),
    )


def write_packet(packet: EvidencePacket, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet_to_dict(packet), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_packet(path: Path) -> EvidencePacket:
    return packet_from_dict(json.loads(path.read_text(encoding="utf-8")))


def default_packet_path(root: Path, run_id: str, packet: EvidencePacket) -> Path:
    return root / "agents" / "runs" / run_id / "evidence_packets" / f"{packet.packet_id}.json"


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"
