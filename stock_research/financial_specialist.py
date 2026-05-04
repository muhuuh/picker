from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .evidence import Claim, Contradiction, EvidencePacket, RecommendedUpdate, Risk, Source, default_packet_path, new_packet, read_packet, write_packet
from .memory import relative_to_root
from .repo import find_repo_root


CORE_METRICS = ("company_name", "latest_price", "market_cap", "pe_ratio", "currency", "exchange", "sector", "industry")
HEADLINE_METRICS = (
    "company_name",
    "latest_price",
    "market_cap",
    "pe_ratio",
    "price_to_sales_ttm",
    "ev_to_ebitda_ttm",
    "revenue_ttm",
    "profit_margin",
    "eps",
    "free_cash_flow_per_share_ttm",
    "debt_to_equity_ttm",
    "currency",
    "exchange",
    "sector",
    "industry",
    "country",
)


class FinancialSpecialistError(RuntimeError):
    pass


@dataclass(frozen=True)
class FinancialReviewResult:
    packet: EvidencePacket
    paths: list[Path]
    review: dict[str, Any]


def build_financial_specialist_packet(
    ticker: str,
    run_id: str,
    root: Path | None,
    current_date: date | None = None,
    financial_compare_packet_path: Path | None = None,
) -> FinancialReviewResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    ticker_upper = ticker.upper()
    compare_path, compare_packet = load_financial_compare_packet(repo_root, run_id, ticker_upper, financial_compare_packet_path)
    consensus = parse_financial_compare_consensus(compare_packet)
    review = build_financial_review(ticker_upper, compare_packet, consensus, compare_path)

    raw_path = write_raw_review(repo_root, run_id, ticker_upper, review)
    report_path = write_markdown_review(repo_root, run_id, ticker_upper, review)
    packet = review_to_packet(ticker_upper, compare_path, compare_packet, review, raw_path, report_path, today)
    packet_path = default_packet_path(repo_root, run_id, packet)
    write_packet(packet, packet_path)
    return FinancialReviewResult(packet=packet, paths=[packet_path, raw_path, report_path], review=review)


def load_financial_compare_packet(
    root: Path,
    run_id: str,
    ticker: str,
    packet_path: Path | None = None,
) -> tuple[Path, EvidencePacket]:
    if packet_path:
        path = packet_path if packet_path.is_absolute() else root / packet_path
        packet = read_packet(path)
        validate_financial_compare_packet(packet, ticker)
        return path, packet

    packet_dir = root / "agents" / "runs" / run_id / "evidence_packets"
    candidates: list[tuple[Path, EvidencePacket]] = []
    for path in sorted(packet_dir.glob("*.json")):
        packet = read_packet(path)
        if packet.provider == "financial_compare" and packet.subject_type == "company" and packet.subject_id.upper() == ticker.upper():
            candidates.append((path, packet))
    if not candidates:
        raise FinancialSpecialistError(f"No financial_compare packet found for {ticker} in run {run_id}.")
    return max(candidates, key=lambda item: item[1].created_at)


def validate_financial_compare_packet(packet: EvidencePacket, ticker: str) -> None:
    if packet.provider != "financial_compare":
        raise FinancialSpecialistError(f"Expected provider financial_compare, got {packet.provider}.")
    if packet.subject_type != "company" or packet.subject_id.upper() != ticker.upper():
        raise FinancialSpecialistError(f"Expected financial_compare company packet for {ticker}, got {packet.subject_type}:{packet.subject_id}.")


def parse_financial_compare_consensus(packet: EvidencePacket) -> dict[str, dict[str, Any]]:
    for claim in packet.claims:
        try:
            parsed = json.loads(claim.evidence)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise FinancialSpecialistError(f"Financial compare packet {packet.packet_id} has no parseable consensus claim evidence.")


def build_financial_review(
    ticker: str,
    compare_packet: EvidencePacket,
    consensus: dict[str, dict[str, Any]],
    compare_path: Path,
) -> dict[str, Any]:
    conflicts = [contradiction.current_repo_claim for contradiction in compare_packet.contradictions]
    missing_core = [metric for metric in CORE_METRICS if metric not in consensus]
    low_confidence_core = [
        metric
        for metric in CORE_METRICS
        if metric in consensus and consensus[metric].get("confidence") in {"low", "unknown"}
    ]
    single_provider_metrics = [
        metric
        for metric, result in consensus.items()
        if len(result.get("providers", [])) == 1
    ]
    confidence_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}
    for result in consensus.values():
        confidence = str(result.get("confidence", "unknown"))
        status = str(result.get("status", "unknown"))
        confidence_counts[confidence] = confidence_counts.get(confidence, 0) + 1
        status_counts[status] = status_counts.get(status, 0) + 1

    if conflicts or low_confidence_core:
        status = "needs_human_review"
        status_reason = "Material conflicts or low-confidence core metrics need review before file updates."
    elif missing_core:
        status = "partial_review"
        status_reason = "No material conflicts found, but some core metrics are missing."
    else:
        status = "ready_for_company_update"
        status_reason = "Core metrics are available and no material provider conflicts were found."

    return {
        "ticker": ticker,
        "status": status,
        "status_reason": status_reason,
        "financial_compare_packet": compare_path.as_posix(),
        "financial_compare_packet_id": compare_packet.packet_id,
        "headline_metrics": {metric: consensus[metric] for metric in HEADLINE_METRICS if metric in consensus},
        "confidence_counts": confidence_counts,
        "status_counts": status_counts,
        "single_provider_metrics": single_provider_metrics,
        "missing_core_metrics": missing_core,
        "low_confidence_core_metrics": low_confidence_core,
        "unknowns": compare_packet.unknowns,
        "conflicts": conflicts,
        "needs_human_review": status == "needs_human_review",
        "recommended_company_file_action": recommended_company_file_action(status),
    }


def recommended_company_file_action(status: str) -> str:
    if status == "ready_for_company_update":
        return "Update the company file financial snapshot from the review packet."
    if status == "partial_review":
        return "Update available metrics, but preserve missing-core-metric notes for follow-up."
    return "Do not update financial conclusions until conflicts or low-confidence core metrics are reviewed."


def review_to_packet(
    ticker: str,
    compare_path: Path,
    compare_packet: EvidencePacket,
    review: dict[str, Any],
    raw_path: Path,
    report_path: Path,
    today: date,
) -> EvidencePacket:
    source_id = "financial_compare_packet"
    sources = [
        Source(
            source_id=source_id,
            provider="financial_data_specialist",
            source_type="internal",
            title=f"financial_compare packet for {ticker}",
            publisher="financial_compare",
            accessed_at=today.isoformat(),
            artifact_path=compare_path.as_posix(),
            notes=f"Input packet {compare_packet.packet_id}.",
        ),
        Source(
            source_id="financial_specialist_report",
            provider="financial_data_specialist",
            source_type="internal",
            title=f"Financial specialist review for {ticker}",
            publisher="financial_data_specialist",
            accessed_at=today.isoformat(),
            artifact_path=report_path.as_posix(),
            notes="Generated deterministic specialist report.",
        ),
    ]
    claim_summary = {
        "status": review["status"],
        "status_reason": review["status_reason"],
        "headline_metrics": review["headline_metrics"],
        "confidence_counts": review["confidence_counts"],
        "status_counts": review["status_counts"],
        "missing_core_metrics": review["missing_core_metrics"],
        "single_provider_metrics": review["single_provider_metrics"],
    }
    claims = [
        Claim(
            claim=f"Financial data specialist review completed for {ticker}.",
            evidence=json.dumps(claim_summary, sort_keys=True),
            source_ids=[source_id, "financial_specialist_report"],
            confidence="high" if review["status"] == "ready_for_company_update" else "medium",
            impact="medium",
            novelty="new",
        )
    ]
    risks = build_review_risks(review, [source_id])
    recommended_updates = [
        RecommendedUpdate(
            target_file="stock_tracking/stock_info_files/",
            update_type="company_file",
            summary=review["recommended_company_file_action"],
            needs_human_review=bool(review["needs_human_review"]),
            source_ids=[source_id, "financial_specialist_report"],
        )
    ]
    return new_packet(
        provider="financial_data_specialist",
        subject_type="company",
        subject_id=ticker,
        time_window="latest_financial_review",
        current_date=today,
        sources=sources,
        claims=claims,
        risks=risks,
        contradictions=[
            Contradiction(
                current_repo_claim=contradiction.current_repo_claim,
                new_evidence=contradiction.new_evidence,
                source_ids=[source_id],
                suggested_action=contradiction.suggested_action,
            )
            for contradiction in compare_packet.contradictions
        ],
        recommended_updates=recommended_updates,
        unknowns=list(review["unknowns"]),
        raw_artifact_path=raw_path.as_posix(),
        notes="Deterministic financial specialist synthesis built from a financial_compare packet. Exa/Grok are intentionally excluded.",
    )


def build_review_risks(review: dict[str, Any], source_ids: list[str]) -> list[Risk]:
    risks: list[Risk] = []
    if review["conflicts"]:
        risks.append(
            Risk(
                risk="Financial provider conflicts remain after deterministic comparison.",
                evidence=json.dumps(review["conflicts"], sort_keys=True),
                source_ids=source_ids,
                severity="medium",
                time_horizon="current_review",
            )
        )
    if review["missing_core_metrics"]:
        risks.append(
            Risk(
                risk="Some core financial snapshot metrics are missing.",
                evidence=json.dumps(review["missing_core_metrics"], sort_keys=True),
                source_ids=source_ids,
                severity="medium",
                time_horizon="current_review",
            )
        )
    if review["single_provider_metrics"]:
        risks.append(
            Risk(
                risk="Some financial metrics rely on a single provider and should be treated as lower-confidence context.",
                evidence=json.dumps(review["single_provider_metrics"], sort_keys=True),
                source_ids=source_ids,
                severity="low",
                time_horizon="current_review",
            )
        )
    return risks


def write_raw_review(root: Path, run_id: str, ticker: str, review: dict[str, Any]) -> Path:
    raw_dir = root / "agents" / "runs" / run_id / "raw" / "financial_data_specialist"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{ticker.upper()}_financial_review.json"
    path.write_text(json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def write_markdown_review(root: Path, run_id: str, ticker: str, review: dict[str, Any]) -> Path:
    report_dir = root / "agents" / "runs" / run_id / "reports" / "financial_data_specialist"
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{ticker.upper()}_financial_review.md"
    path.write_text(format_financial_review_markdown(root, review), encoding="utf-8")
    return path


def format_financial_review_markdown(root: Path, review: dict[str, Any]) -> str:
    lines = [
        f"# Financial Review: {review['ticker']}",
        "",
        f"Status: {review['status']}",
        f"Reason: {review['status_reason']}",
        "",
        "## Headline Metrics",
        "",
        "| Metric | Value | Confidence | Providers |",
        "| --- | --- | --- | --- |",
    ]
    for metric, result in review["headline_metrics"].items():
        providers = ", ".join(result.get("providers", []))
        lines.append(f"| {metric} | {format_metric_value(result.get('value'))} | {result.get('confidence', 'unknown')} | {providers} |")
    lines.extend(["", "## Review Notes", ""])
    lines.append(f"- financial_compare packet: `{relative_to_root(root, Path(review['financial_compare_packet'])).as_posix()}`")
    lines.append(f"- confidence_counts: {json.dumps(review['confidence_counts'], sort_keys=True)}")
    lines.append(f"- status_counts: {json.dumps(review['status_counts'], sort_keys=True)}")
    lines.append(f"- single_provider_metrics: {', '.join(review['single_provider_metrics']) or 'none'}")
    lines.append(f"- missing_core_metrics: {', '.join(review['missing_core_metrics']) or 'none'}")
    lines.append(f"- low_confidence_core_metrics: {', '.join(review['low_confidence_core_metrics']) or 'none'}")
    lines.append(f"- conflicts: {len(review['conflicts'])}")
    lines.append(f"- recommended_company_file_action: {review['recommended_company_file_action']}")
    return "\n".join(lines).rstrip() + "\n"


def format_metric_value(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.4g}"
    return str(value)
