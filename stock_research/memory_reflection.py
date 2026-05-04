from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import EvidencePacket, read_packet, validate_packet
from .memory import relative_to_root
from .repo import find_repo_root


@dataclass(frozen=True)
class ReflectionIssue:
    severity: str
    category: str
    summary: str
    evidence: str


@dataclass(frozen=True)
class MemoryUpdateProposal:
    proposal_id: str
    action: str
    target_file: str
    reason: str
    fields: dict[str, str]
    apply_command: str


@dataclass(frozen=True)
class RunReflection:
    run_id: str
    run_dir: str
    generated_at: str
    metrics: dict[str, Any]
    issues: list[ReflectionIssue] = field(default_factory=list)
    memory_update_proposals: list[MemoryUpdateProposal] = field(default_factory=list)


def build_run_reflection(
    root: Path | None,
    run_id: str,
    current_date: date | None = None,
) -> RunReflection:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    run_dir = repo_root / "agents" / "runs" / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    manifest_path = run_dir / "manifest.json"
    manifest = read_json_if_exists(manifest_path)
    evidence_dir = run_dir / "evidence_packets"
    packet_paths = sorted(evidence_dir.glob("*.json")) if evidence_dir.exists() else []
    packets: list[tuple[Path, EvidencePacket | None, list[str], list[str]]] = []
    issues: list[ReflectionIssue] = []

    for packet_path in packet_paths:
        try:
            packet = read_packet(packet_path)
            report = validate_packet(packet)
            packets.append((packet_path, packet, report.errors, report.warnings))
            for error in report.errors:
                issues.append(
                    ReflectionIssue(
                        severity="high",
                        category="invalid_evidence_packet",
                        summary=f"{relative_to_root(repo_root, packet_path).as_posix()} failed evidence validation: {error}",
                        evidence=relative_to_root(repo_root, packet_path).as_posix(),
                    )
                )
            for warning in report.warnings:
                issues.append(
                    ReflectionIssue(
                        severity="medium",
                        category="evidence_packet_warning",
                        summary=f"{relative_to_root(repo_root, packet_path).as_posix()} validation warning: {warning}",
                        evidence=relative_to_root(repo_root, packet_path).as_posix(),
                    )
                )
        except Exception as exc:  # noqa: BLE001 - reflection should report malformed artifacts.
            packets.append((packet_path, None, [str(exc)], []))
            issues.append(
                ReflectionIssue(
                    severity="high",
                    category="unreadable_evidence_packet",
                    summary=f"{relative_to_root(repo_root, packet_path).as_posix()} could not be read: {exc}",
                    evidence=relative_to_root(repo_root, packet_path).as_posix(),
                )
            )

    run_summary_path = run_dir / "run_summary.md"
    quality_report_path = run_dir / "quality_report.md"
    if not run_summary_path.exists():
        issues.append(
            ReflectionIssue(
                severity="medium",
                category="missing_run_summary",
                summary="Run has no run_summary.md artifact.",
                evidence=relative_to_root(repo_root, run_summary_path).as_posix(),
            )
        )
    if not quality_report_path.exists():
        issues.append(
            ReflectionIssue(
                severity="medium",
                category="missing_quality_report",
                summary="Run has no quality_report.md artifact.",
                evidence=relative_to_root(repo_root, quality_report_path).as_posix(),
            )
        )

    provider_tasks = list(manifest.get("provider_tasks", [])) if isinstance(manifest, dict) else []
    analysis_tasks = list(manifest.get("analysis_tasks", [])) if isinstance(manifest, dict) else []
    provider_counts = count_packets_by_provider(packets)
    missing_provider_tasks = planned_tasks_without_packets(provider_tasks, packets)
    for task in missing_provider_tasks:
        issues.append(
            ReflectionIssue(
                severity="medium",
                category="planned_provider_task_without_packet",
                summary=f"Manifest task {task.get('id', 'unknown')} planned provider {task.get('provider', '')} but no matching evidence packet was found.",
                evidence=relative_to_root(repo_root, manifest_path).as_posix(),
            )
        )

    metrics = {
        "manifest_exists": manifest_path.exists(),
        "run_summary_exists": run_summary_path.exists(),
        "quality_report_exists": quality_report_path.exists(),
        "provider_tasks_planned": len(provider_tasks),
        "analysis_tasks_planned": len(analysis_tasks),
        "evidence_packets": len(packet_paths),
        "valid_evidence_packets": len([packet for _, packet, errors, _ in packets if packet is not None and not errors]),
        "invalid_evidence_packets": len([errors for _, _, errors, _ in packets if errors]),
        "provider_packet_counts": provider_counts,
        "claims": sum(len(packet.claims) for _, packet, _, _ in packets if packet is not None),
        "risks": sum(len(packet.risks) for _, packet, _, _ in packets if packet is not None),
        "contradictions": sum(len(packet.contradictions) for _, packet, _, _ in packets if packet is not None),
        "recommended_updates": sum(len(packet.recommended_updates) for _, packet, _, _ in packets if packet is not None),
        "unknowns": sum(len(packet.unknowns) for _, packet, _, _ in packets if packet is not None),
        "issues": len(issues),
    }

    proposals = build_memory_proposals(run_id, today, metrics, issues)
    return RunReflection(
        run_id=run_id,
        run_dir=relative_to_root(repo_root, run_dir).as_posix(),
        generated_at=today.isoformat(),
        metrics=metrics,
        issues=issues,
        memory_update_proposals=proposals,
    )


def write_run_reflection(root: Path | None, reflection: RunReflection) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / reflection.run_dir
    json_path = run_dir / "memory_reflection.json"
    md_path = run_dir / "memory_reflection.md"
    json_path.write_text(json.dumps(reflection_to_dict(reflection), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_reflection_markdown(reflection), encoding="utf-8")
    return json_path, md_path


def reflection_to_dict(reflection: RunReflection) -> dict[str, Any]:
    return {
        "run_id": reflection.run_id,
        "run_dir": reflection.run_dir,
        "generated_at": reflection.generated_at,
        "metrics": reflection.metrics,
        "issues": [asdict(issue) for issue in reflection.issues],
        "memory_update_proposals": [asdict(proposal) for proposal in reflection.memory_update_proposals],
    }


def format_reflection_markdown(reflection: RunReflection) -> str:
    lines = [
        f"# Memory Reflection: {reflection.run_id}",
        "",
        f"Generated: {reflection.generated_at}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in reflection.metrics.items():
        lines.append(f"- {key}: {json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value}")
    lines.extend(["", "## Issues", ""])
    if reflection.issues:
        for issue in reflection.issues:
            lines.append(f"- [{issue.severity}] {issue.category}: {issue.summary} ({issue.evidence})")
    else:
        lines.append("- No deterministic reflection issues found.")
    lines.extend(["", "## Memory Update Proposals", ""])
    if reflection.memory_update_proposals:
        for proposal in reflection.memory_update_proposals:
            lines.append(f"### {proposal.proposal_id}")
            lines.append("")
            lines.append(f"- action: {proposal.action}")
            lines.append(f"- target_file: {proposal.target_file}")
            lines.append(f"- reason: {proposal.reason}")
            lines.append("")
            lines.append("```powershell")
            lines.append(proposal.apply_command)
            lines.append("```")
            lines.append("")
    else:
        lines.append("- No memory update proposals.")
    return "\n".join(lines).rstrip() + "\n"


def build_memory_proposals(
    run_id: str,
    today: date,
    metrics: dict[str, Any],
    issues: list[ReflectionIssue],
) -> list[MemoryUpdateProposal]:
    proposals: list[MemoryUpdateProposal] = []
    if issues:
        lesson = (
            f"Run {run_id} produced {len(issues)} deterministic reflection issue(s). "
            "Review `memory_reflection.md`, run summary, quality report, and evidence packets before treating the run as complete."
        )
        fields = {
            "type": "evaluation",
            "scope": "global",
            "status": "needs_review",
            "confidence": "medium",
            "trigger/source": f"post-run reflection for {run_id}",
            "lesson": lesson,
            "use_when": "Reviewing run quality, deciding whether to update operational memory, or planning reruns.",
            "do_not_use_when": "Making investment conclusions without reviewing underlying evidence.",
            "evidence": f"`agents/runs/{run_id}/memory_reflection.md`",
            "owner": "memory and evaluation orchestrator",
            "next_review": today.isoformat(),
        }
        proposals.append(
            MemoryUpdateProposal(
                proposal_id=f"proposal-{today.isoformat()}-{run_id}-reflection-issues",
                action="memory_add",
                target_file="evaluation_metrics.md",
                reason="Reflection found issues that should be reviewed before the run is considered complete.",
                fields=fields,
                apply_command=memory_add_command(fields, "evaluation_metrics.md", today),
            )
        )

    if metrics.get("invalid_evidence_packets", 0):
        lesson = (
            f"Run {run_id} had {metrics['invalid_evidence_packets']} invalid evidence packet(s). "
            "Evidence validation failures should block downstream synthesis until fixed."
        )
        fields = {
            "type": "evaluation",
            "scope": "provider",
            "status": "needs_review",
            "confidence": "high",
            "trigger/source": f"post-run reflection for {run_id}",
            "lesson": lesson,
            "use_when": "Running quality review or deciding whether provider outputs are safe for synthesis.",
            "do_not_use_when": "Ignoring evidence validation failures.",
            "evidence": f"`agents/runs/{run_id}/memory_reflection.md`",
            "owner": "quality reviewer",
            "next_review": today.isoformat(),
        }
        proposals.append(
            MemoryUpdateProposal(
                proposal_id=f"proposal-{today.isoformat()}-{run_id}-invalid-evidence",
                action="memory_add",
                target_file="evaluation_metrics.md",
                reason="Invalid evidence packets require run-quality memory.",
                fields=fields,
                apply_command=memory_add_command(fields, "evaluation_metrics.md", today),
            )
        )

    return proposals


def memory_add_command(fields: dict[str, str], memory_file: str, today: date) -> str:
    parts = [
        "python -m stock_research memory add",
        f"--memory-file {memory_file}",
        f"--type {shell_quote(fields['type'])}",
        f"--scope {shell_quote(fields['scope'])}",
        f"--status {shell_quote(fields['status'])}",
        f"--confidence {shell_quote(fields['confidence'])}",
        f"--trigger-source {shell_quote(fields['trigger/source'])}",
        f"--lesson {shell_quote(fields['lesson'])}",
        f"--use-when {shell_quote(fields['use_when'])}",
        f"--do-not-use-when {shell_quote(fields['do_not_use_when'])}",
        f"--evidence {shell_quote(fields['evidence'])}",
        f"--owner {shell_quote(fields['owner'])}",
        f"--next-review {shell_quote(fields['next_review'])}",
        f"--today {today.isoformat()}",
    ]
    return " ".join(parts)


def shell_quote(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_packets_by_provider(packets: list[tuple[Path, EvidencePacket | None, list[str], list[str]]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for _, packet, _, _ in packets:
        if packet is None:
            continue
        counts[packet.provider] = counts.get(packet.provider, 0) + 1
    return counts


def planned_tasks_without_packets(
    provider_tasks: list[dict[str, Any]],
    packets: list[tuple[Path, EvidencePacket | None, list[str], list[str]]],
) -> list[dict[str, Any]]:
    result = []
    for task in provider_tasks:
        provider = task.get("provider", "")
        subject_id = task.get("subject_id", "")
        if not provider or not subject_id:
            continue
        if not any(packet_matches_task(packet, provider, subject_id) for _, packet, _, _ in packets if packet is not None):
            result.append(task)
    return result


def packet_matches_task(packet: EvidencePacket, provider: str, subject_id: str) -> bool:
    provider_aliases = {
        "xai_grok": {"xai_grok"},
        "alpha_vantage": {"alpha_vantage"},
        "polygon": {"polygon", "polygon_provider"},
    }
    providers = provider_aliases.get(provider, {provider})
    return packet.provider in providers and packet.subject_id.lower() == str(subject_id).lower()
