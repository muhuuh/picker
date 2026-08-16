from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import EvidencePacket, read_packet
from .memory import relative_to_root
from .repo import find_repo_root


@dataclass(frozen=True)
class RunSummary:
    run_id: str
    generated_at: str
    metrics: dict[str, Any]
    tracked_tickers: dict[str, list[str]]
    recurring_coverage: dict[str, Any]
    provider_packet_counts: dict[str, int]
    financial_reviews: list[dict[str, Any]]
    company_news_reviews: list[dict[str, Any]]
    open_items: list[str]


def build_run_summary(root: Path | None, run_id: str, current_date: date | None = None) -> RunSummary:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    run_dir = repo_root / "agents" / "runs" / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory not found: {run_dir}")

    manifest = read_json_if_exists(run_dir / "manifest.json")
    packets = load_run_packets(run_dir)
    provider_counts: dict[str, int] = {}
    for _path, packet in packets:
        provider_counts[packet.provider] = provider_counts.get(packet.provider, 0) + 1

    financial_reviews = extract_financial_reviews(packets, repo_root)
    company_news_reviews = extract_company_news_reviews(packets, repo_root)
    open_items = build_open_items(manifest, packets)
    metrics = {
        "provider_tasks_planned": len(manifest.get("provider_tasks", [])) if isinstance(manifest, dict) else 0,
        "analysis_tasks_planned": len(manifest.get("analysis_tasks", [])) if isinstance(manifest, dict) else 0,
        "evidence_packets": len(packets),
        "financial_reviews": len(financial_reviews),
        "company_news_reviews": len(company_news_reviews),
        "recommended_updates": sum(len(packet.recommended_updates) for _path, packet in packets),
        "risks": sum(len(packet.risks) for _path, packet in packets),
        "contradictions": sum(len(packet.contradictions) for _path, packet in packets),
        "unknowns": sum(len(packet.unknowns) for _path, packet in packets),
    }

    return RunSummary(
        run_id=run_id,
        generated_at=today.isoformat(),
        metrics=metrics,
        tracked_tickers=manifest.get("tracked_tickers", {}) if isinstance(manifest, dict) else {},
        recurring_coverage=summarize_recurring_coverage(manifest),
        provider_packet_counts=provider_counts,
        financial_reviews=financial_reviews,
        company_news_reviews=company_news_reviews,
        open_items=open_items,
    )


def write_run_summary(root: Path | None, summary: RunSummary) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / summary.run_id
    json_path = run_dir / "run_summary.json"
    md_path = run_dir / "run_summary.md"
    json_path.write_text(json.dumps(run_summary_to_dict(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_run_summary_markdown(summary), encoding="utf-8")
    return json_path, md_path


def run_summary_to_dict(summary: RunSummary) -> dict[str, Any]:
    return {
        "run_id": summary.run_id,
        "generated_at": summary.generated_at,
        "metrics": summary.metrics,
        "tracked_tickers": summary.tracked_tickers,
        "recurring_coverage": summary.recurring_coverage,
        "provider_packet_counts": summary.provider_packet_counts,
        "financial_reviews": summary.financial_reviews,
        "company_news_reviews": summary.company_news_reviews,
        "open_items": summary.open_items,
    }


def format_run_summary_markdown(summary: RunSummary) -> str:
    lines = [
        f"# Run Summary: {summary.run_id}",
        "",
        f"Generated: {summary.generated_at}",
        "",
        "## Metrics",
        "",
    ]
    for key, value in summary.metrics.items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Tracked Tickers", ""])
    if summary.tracked_tickers:
        for bucket, tickers in summary.tracked_tickers.items():
            lines.append(f"- {bucket}: {', '.join(tickers) if tickers else 'none'}")
    else:
        lines.append("- No tracked tickers in manifest.")
    lines.extend(["", "## Recurring Coverage", ""])
    if summary.recurring_coverage:
        coverage = summary.recurring_coverage
        lines.extend(
            [
                f"- profile: {coverage.get('profile', 'unknown')}",
                f"- companies: {coverage.get('company_count', 0)}",
                f"- industry clusters: {coverage.get('industry_cluster_count', 0)}",
                f"- impact basis: {coverage.get('impact_basis', 'unknown')}",
                f"- accepted comparison baseline: {coverage.get('comparison_run_id') or 'none'} ({coverage.get('comparison_status', 'unknown')})",
                f"- latest generated run: {coverage.get('latest_generated_run_id') or 'none'}",
            ]
        )
        clusters = coverage.get("industry_clusters") or []
        if clusters:
            lines.append("- cluster membership:")
            for cluster in clusters:
                members = ", ".join(cluster.get("member_tickers") or []) or "none"
                lines.append(f"  - {cluster.get('label', cluster.get('cluster_id', 'unknown'))}: {members}")
    else:
        lines.append("- No recurring coverage contract found in manifest.")
    lines.extend(["", "## Provider Packet Counts", ""])
    if summary.provider_packet_counts:
        for provider, count in sorted(summary.provider_packet_counts.items()):
            lines.append(f"- {provider}: {count}")
    else:
        lines.append("- No evidence packets found.")
    lines.extend(["", "## Financial Reviews", ""])
    if summary.financial_reviews:
        lines.append("| Ticker | Status | Report |")
        lines.append("| --- | --- | --- |")
        for review in summary.financial_reviews:
            lines.append(f"| {review['ticker']} | {review['status']} | `{review['report_path']}` |")
    else:
        lines.append("- No financial specialist reviews found.")
    lines.extend(["", "## Company News Reviews", ""])
    if summary.company_news_reviews:
        lines.append("| Ticker | Status | Report |")
        lines.append("| --- | --- | --- |")
        for review in summary.company_news_reviews:
            lines.append(f"| {review['ticker']} | {review['status']} | `{review['report_path']}` |")
    else:
        lines.append("- No company news specialist reviews found.")
    lines.extend(["", "## Open Items", ""])
    if summary.open_items:
        for item in summary.open_items:
            lines.append(f"- {item}")
    else:
        lines.append("- No deterministic open items found.")
    return "\n".join(lines).rstrip() + "\n"


def summarize_recurring_coverage(manifest: dict[str, Any] | Any) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        return {}
    coverage = manifest.get("recurring_coverage")
    if not isinstance(coverage, dict):
        return {}
    baseline = coverage.get("comparison_baseline") or {}
    clusters = coverage.get("industry_clusters") or []
    return {
        "profile": manifest.get("research_profile", "portfolio_update"),
        "company_count": len(coverage.get("companies") or []),
        "industry_cluster_count": len(clusters),
        "impact_basis": coverage.get("impact_basis", "unknown"),
        "weights_available": bool(coverage.get("weights_available")),
        "comparison_policy": baseline.get("policy", "unknown"),
        "comparison_status": baseline.get("status", "unknown"),
        "comparison_run_id": baseline.get("comparison_run_id", ""),
        "latest_generated_run_id": baseline.get("latest_generated_run_id", ""),
        "industry_clusters": [
            {
                "cluster_id": cluster.get("cluster_id", ""),
                "label": cluster.get("label", ""),
                "member_tickers": list(cluster.get("member_tickers") or []),
            }
            for cluster in clusters
            if isinstance(cluster, dict)
        ],
    }


def load_run_packets(run_dir: Path) -> list[tuple[Path, EvidencePacket]]:
    evidence_dir = run_dir / "evidence_packets"
    if not evidence_dir.exists():
        return []
    packets: list[tuple[Path, EvidencePacket]] = []
    for path in sorted(evidence_dir.glob("*.json")):
        packets.append((path, read_packet(path)))
    return packets


def extract_financial_reviews(packets: list[tuple[Path, EvidencePacket]], root: Path) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for _path, packet in packets:
        if packet.provider != "financial_data_specialist":
            continue
        status = "unknown"
        report_path = ""
        if packet.claims:
            try:
                claim_data = json.loads(packet.claims[0].evidence)
                status = str(claim_data.get("status", "unknown"))
            except json.JSONDecodeError:
                status = "unknown"
        for source in packet.sources:
            if source.source_id == "financial_specialist_report":
                report_path = relative_to_root(root, Path(source.artifact_path)).as_posix()
        reviews.append({"ticker": packet.subject_id, "status": status, "report_path": report_path})
    return sorted(reviews, key=lambda item: item["ticker"])


def extract_company_news_reviews(packets: list[tuple[Path, EvidencePacket]], root: Path) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for _path, packet in packets:
        if packet.provider != "company_news_specialist":
            continue
        status = "unknown"
        report_path = ""
        if packet.claims:
            try:
                claim_data = json.loads(packet.claims[0].evidence)
                status = str(claim_data.get("status", "unknown"))
            except json.JSONDecodeError:
                status = "unknown"
        for source in packet.sources:
            if source.source_id == "company_news_specialist_report":
                report_path = relative_to_root(root, Path(source.artifact_path)).as_posix()
        reviews.append({"ticker": packet.subject_id, "status": status, "report_path": report_path})
    return sorted(reviews, key=lambda item: item["ticker"])


def build_open_items(manifest: dict[str, Any], packets: list[tuple[Path, EvidencePacket]]) -> list[str]:
    items: list[str] = []
    if isinstance(manifest, dict):
        provider_tasks = manifest.get("provider_tasks", [])
        analysis_tasks = manifest.get("analysis_tasks", [])
        packet_providers = {packet.provider for _path, packet in packets}
        if provider_tasks and not packet_providers:
            items.append("Provider tasks were planned, but no evidence packets were found.")
        if analysis_tasks and not any(packet.provider in {"financial_compare", "financial_data_specialist", "company_news_specialist"} for _path, packet in packets):
            items.append("Analysis tasks were planned, but no analysis packets were found.")
    review_statuses = [item["status"] for item in extract_financial_reviews(packets, Path("."))]
    if any(status == "needs_human_review" for status in review_statuses):
        items.append("At least one financial review needs human review.")
    news_review_statuses = [item["status"] for item in extract_company_news_reviews(packets, Path("."))]
    if any(status == "needs_human_review" for status in news_review_statuses):
        items.append("At least one company news review needs human review.")
    return items


def read_json_if_exists(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
