from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import EvidencePacket, read_packet, validate_packet
from .memory_reflection import packet_matches_task
from .report_quality import validate_human_facing_markdown
from .repo import find_repo_root


@dataclass(frozen=True)
class QualityFinding:
    severity: str
    category: str
    summary: str
    evidence: str


@dataclass(frozen=True)
class QualityReport:
    run_id: str
    generated_at: str
    metrics: dict[str, Any]
    findings: list[QualityFinding]


def build_quality_report(root: Path | None, run_id: str, current_date: date | None = None) -> QualityReport:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    run_dir = repo_root / "agents" / "runs" / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    manifest = read_json_if_exists(run_dir / "manifest.json")
    packets = load_packets(run_dir)
    findings: list[QualityFinding] = []

    for path, packet in packets:
        report = validate_packet(packet)
        for error in report.errors:
            findings.append(QualityFinding("high", "invalid_evidence_packet", error, path.as_posix()))
        for warning in report.warnings:
            findings.append(QualityFinding("medium", "evidence_packet_warning", warning, path.as_posix()))

    provider_tasks = manifest.get("provider_tasks", []) if isinstance(manifest, dict) else []
    for task in planned_provider_tasks_without_packets(provider_tasks, packets):
        findings.append(
            QualityFinding(
                "medium",
                "planned_provider_task_without_packet",
                f"Planned provider task {task.get('id', 'unknown')} has no matching evidence packet.",
                (run_dir / "manifest.json").as_posix(),
            )
        )

    if not (run_dir / "run_summary.md").exists():
        findings.append(QualityFinding("medium", "missing_run_summary", "Run summary has not been generated.", (run_dir / "run_summary.md").as_posix()))

    for report_path in human_facing_report_paths(repo_root, run_dir):
        for finding in validate_human_facing_markdown(report_path.read_text(encoding="utf-8")):
            findings.append(QualityFinding("medium", "human_report_quality", finding, report_path.as_posix()))

    metrics = {
        "provider_tasks_planned": len(provider_tasks),
        "analysis_tasks_planned": len(manifest.get("analysis_tasks", [])) if isinstance(manifest, dict) else 0,
        "evidence_packets": len(packets),
        "findings": len(findings),
        "high_findings": len([finding for finding in findings if finding.severity == "high"]),
        "medium_findings": len([finding for finding in findings if finding.severity == "medium"]),
        "recommended_updates": sum(len(packet.recommended_updates) for _path, packet in packets),
        "human_review_recommended_updates": sum(
            len([update for update in packet.recommended_updates if update.needs_human_review])
            for _path, packet in packets
        ),
    }
    return QualityReport(run_id=run_id, generated_at=today.isoformat(), metrics=metrics, findings=findings)


def write_quality_report(root: Path | None, report: QualityReport) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / report.run_id
    json_path = run_dir / "quality_report.json"
    md_path = run_dir / "quality_report.md"
    json_path.write_text(json.dumps(quality_report_to_dict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_quality_report_markdown(report), encoding="utf-8")
    return json_path, md_path


def quality_report_to_dict(report: QualityReport) -> dict[str, Any]:
    return {
        "run_id": report.run_id,
        "generated_at": report.generated_at,
        "metrics": report.metrics,
        "findings": [
            {
                "severity": finding.severity,
                "category": finding.category,
                "summary": finding.summary,
                "evidence": finding.evidence,
            }
            for finding in report.findings
        ],
    }


def format_quality_report_markdown(report: QualityReport) -> str:
    lines = [
        f"# Quality Report: {report.run_id}",
        "",
        f"Generated: {report.generated_at}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in report.metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Findings", ""])
    if report.findings:
        for finding in report.findings:
            lines.append(f"- [{finding.severity}] {finding.category}: {finding.summary} (`{finding.evidence}`)")
    else:
        lines.append("- No deterministic quality findings.")
    return "\n".join(lines).rstrip() + "\n"


def load_packets(run_dir: Path) -> list[tuple[Path, EvidencePacket]]:
    evidence_dir = run_dir / "evidence_packets"
    if not evidence_dir.exists():
        return []
    return [(path, read_packet(path)) for path in sorted(evidence_dir.glob("*.json"))]


def human_facing_report_paths(repo_root: Path, run_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for direct_name in ("final_digest.md", "codex_supervised_review.md", "run_summary.md", "human_review_digest_summary.md"):
        path = run_dir / direct_name
        if path.exists():
            candidates.append(path)
    human_review_digest = repo_root / "agents" / "human_review_digest.md"
    if human_review_digest.exists():
        candidates.append(human_review_digest)
    opportunity_dir = run_dir / "reports" / "opportunity_assessment"
    if opportunity_dir.exists():
        candidates.extend(sorted(opportunity_dir.glob("*_opportunity_assessment.md")))
    human_synthesis_dir = run_dir / "reports" / "human_synthesis"
    if human_synthesis_dir.exists():
        candidates.extend(sorted(human_synthesis_dir.glob("*_final_human_report.md")))
    company_research_dir = run_dir / "company_research"
    if company_research_dir.exists():
        candidates.extend(sorted(company_research_dir.glob("*_company_research.md")))
    return candidates


def planned_provider_tasks_without_packets(
    provider_tasks: list[dict[str, Any]],
    packets: list[tuple[Path, EvidencePacket]],
) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for task in provider_tasks:
        provider = str(task.get("provider", ""))
        subject_id = str(task.get("subject_id", ""))
        if not provider or not subject_id:
            continue
        if not any(packet_matches_task(packet, task) for _path, packet in packets):
            missing.append(task)
    return missing


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
