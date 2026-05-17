from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from stock_research.agent_runtime.proposal_review import normalize_ascii
from stock_research.manifest import (
    analysis_task,
    company_news_query,
    company_search_query,
    provider_task,
    slugify,
    stock_sentiment_prompt,
    x_search_window_args,
)
from stock_research.model_routing import resolve_model_for_route
from stock_research.repo import find_repo_root, load_all_tables, load_first_table


CANDIDATE_REVIEW_REPORT = "candidate_review.md"
CANDIDATE_VERIFICATION_MANIFEST = "candidate_verification_manifest.json"
CANDIDATE_VERIFICATION_REPORT = "candidate_verification_plan.md"


@dataclass
class CandidateVerificationItem:
    review_item_id: str
    candidate_group_id: str
    candidate: str
    tickers: list[str] = field(default_factory=list)
    decision_kind: str = ""
    review_status: str = ""
    planned_provider_task_ids: list[str] = field(default_factory=list)
    planned_analysis_task_ids: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CandidateFollowupResult:
    run_id: str
    generated_at: str
    status: str
    review_ids: list[str] = field(default_factory=list)
    verification_items: list[CandidateVerificationItem] = field(default_factory=list)
    provider_task_count: int = 0
    analysis_task_count: int = 0
    findings: list[str] = field(default_factory=list)
    written_paths: list[str] = field(default_factory=list)


def build_candidate_verification_followup(
    *,
    root: Path | None = None,
    run_id: str,
    review_id: str = "",
    current_date: date | None = None,
    write: bool = False,
) -> CandidateFollowupResult:
    repo_root = find_repo_root(root)
    today = current_date or date.today()
    market_dir = repo_root / "agents" / "runs" / run_id / "market_research"
    review_report_path = market_dir / CANDIDATE_REVIEW_REPORT
    if not review_report_path.exists():
        return CandidateFollowupResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            findings=[f"Missing candidate review report: {review_report_path.relative_to(repo_root).as_posix()}"],
        )

    review_rows = matching_human_review_rows(repo_root, run_id, review_id)
    if review_id and not review_rows:
        return CandidateFollowupResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="blocked",
            findings=[f"No candidate-review human-review row found for review id: {review_id}"],
        )

    selected_rows = [row for row in review_rows if normalize_ascii(row.get("Status", "")).lower() == "approved"]
    if not selected_rows:
        findings = ["No approved candidate-review rows found."]
        if review_id and review_rows:
            status = normalize_ascii(review_rows[0].get("Status", "")).lower() or "unknown"
            findings = [f"Human-review item {review_id} is '{status}', not 'approved'."]
        return CandidateFollowupResult(
            run_id=run_id,
            generated_at=today.isoformat(),
            status="no_approved_items" if not review_id else "blocked",
            review_ids=[row.get("ID", "") for row in review_rows],
            findings=findings,
        )

    groups = load_candidate_groups(review_report_path)
    manifest, items, findings = build_candidate_verification_manifest(
        run_id=run_id,
        generated_at=today,
        root=repo_root,
        review_rows=selected_rows,
        groups=groups,
    )
    status = "ready_for_verification" if manifest["provider_tasks"] or manifest["analysis_tasks"] else "blocked"
    if findings and not manifest["provider_tasks"] and not manifest["analysis_tasks"]:
        status = "blocked"

    written_paths: list[str] = []
    if write:
        market_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = market_dir / CANDIDATE_VERIFICATION_MANIFEST
        report_path = market_dir / CANDIDATE_VERIFICATION_REPORT
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        report_path.write_text(
            format_candidate_verification_report(
                repo_root=repo_root,
                run_id=run_id,
                generated_at=today,
                status=status,
                items=items,
                findings=findings,
                manifest_path=manifest_path,
            ),
            encoding="utf-8",
        )
        written_paths.extend([manifest_path.relative_to(repo_root).as_posix(), report_path.relative_to(repo_root).as_posix()])

    return CandidateFollowupResult(
        run_id=run_id,
        generated_at=today.isoformat(),
        status=status,
        review_ids=[row.get("ID", "") for row in selected_rows],
        verification_items=items,
        provider_task_count=len(manifest["provider_tasks"]),
        analysis_task_count=len(manifest["analysis_tasks"]),
        findings=findings,
        written_paths=written_paths,
    )


def matching_human_review_rows(repo_root: Path, run_id: str, review_id: str = "") -> list[dict[str, str]]:
    review_path = repo_root / "agents" / "human_review_queue.md"
    prefix = f"agents/runs/{run_id}/market_research/{CANDIDATE_REVIEW_REPORT}#"
    rows = []
    for row in load_first_table(review_path):
        row_id = normalize_ascii(row.get("ID", ""))
        evidence = normalize_ascii(row.get("Evidence / Run Link", ""))
        if review_id and row_id != review_id:
            continue
        if evidence.startswith(prefix):
            rows.append(row)
    return rows


def load_candidate_groups(review_report_path: Path) -> dict[str, dict[str, str]]:
    tables = load_all_tables(review_report_path)
    if not tables:
        return {}
    groups: dict[str, dict[str, str]] = {}
    for table in tables:
        if not table or "Group ID" not in table[0]:
            continue
        for row in table:
            group_id = normalize_ascii(row.get("Group ID", ""))
            if group_id:
                groups[group_id] = normalize_candidate_group_row(row)
    return groups


def normalize_candidate_group_row(row: dict[str, str]) -> dict[str, str]:
    normalized = {key: normalize_ascii(value) for key, value in row.items()}
    candidate, label_tickers = split_candidate_label(normalized.get("Candidate", ""))
    evidence = parse_evidence_state(normalized.get("Evidence state", ""))

    if candidate:
        normalized["Candidate"] = candidate
    if not normalized.get("Tickers") and label_tickers:
        normalized["Tickers"] = ", ".join(label_tickers)
    if not normalized.get("Channels") and evidence.get("channels"):
        normalized["Channels"] = evidence["channels"]
    if not normalized.get("Verification") and evidence.get("verification"):
        normalized["Verification"] = evidence["verification"]
    if not normalized.get("Hype") and evidence.get("hype"):
        normalized["Hype"] = evidence["hype"]
    if not normalized.get("Cooldown") and evidence.get("cooldown"):
        normalized["Cooldown"] = evidence["cooldown"]
    if not normalized.get("Decision Kind"):
        normalized["Decision Kind"] = decision_kind_from_group_state(normalized)
    if not normalized.get("Why surfaced") and normalized.get("Why it surfaced"):
        normalized["Why surfaced"] = normalized["Why it surfaced"]
    return normalized


def split_candidate_label(label: str) -> tuple[str, list[str]]:
    cleaned = normalize_ascii(label)
    match = re.search(r"\(([^()]*)\)\s*$", cleaned)
    if not match:
        return cleaned, []
    tickers = [ticker.strip().upper() for ticker in match.group(1).split(",") if ticker.strip()]
    if not tickers or not all(re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]*", ticker) for ticker in tickers):
        return cleaned, []
    candidate = cleaned[: match.start()].strip()
    return candidate or cleaned, tickers


def parse_evidence_state(value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for part in normalize_ascii(value).split(";"):
        if "=" not in part:
            continue
        key, raw_value = part.split("=", 1)
        parsed[key.strip().lower()] = raw_value.strip()
    return parsed


def decision_kind_from_group_state(group: dict[str, str]) -> str:
    cooldown_status = normalize_ascii(group.get("Cooldown", "")).lower()
    verification_status = normalize_ascii(group.get("Verification", "")).lower()
    if cooldown_status == "cooldown_active":
        return "cooldown_override"
    if verification_status in {"verified", "partially_verified"}:
        return "monitoring_candidate"
    if verification_status == "grok_only":
        return "verify_grok_lead"
    return "verify_before_monitoring"


def build_candidate_verification_manifest(
    *,
    run_id: str,
    generated_at: date,
    root: Path | None = None,
    review_rows: list[dict[str, str]],
    groups: dict[str, dict[str, str]],
) -> tuple[dict[str, Any], list[CandidateVerificationItem], list[str]]:
    provider_tasks: list[dict[str, Any]] = []
    analysis_tasks: list[dict[str, Any]] = []
    seen_provider_ids: set[str] = set()
    seen_analysis_ids: set[str] = set()
    items: list[CandidateVerificationItem] = []
    findings: list[str] = []

    for row in review_rows:
        group_id = candidate_group_id_from_evidence(row.get("Evidence / Run Link", ""))
        group = groups.get(group_id)
        if not group:
            finding = f"{row.get('ID', '')}: missing candidate group {group_id} in candidate review report."
            findings.append(finding)
            items.append(
                CandidateVerificationItem(
                    review_item_id=row.get("ID", ""),
                    candidate_group_id=group_id,
                    candidate="unknown",
                    review_status=row.get("Status", ""),
                    findings=[finding],
                )
            )
            continue
        item = build_verification_item(row, group)
        for ticker in item.tickers:
            label = f"{ticker} {item.candidate}".strip()
            add_provider_tasks_for_ticker(provider_tasks, seen_provider_ids, ticker, item.candidate, run_id, generated_at, row.get("ID", ""), root=root)
            add_analysis_tasks_for_ticker(analysis_tasks, seen_analysis_ids, ticker, run_id, row.get("ID", ""))
            item.planned_provider_task_ids.extend(task["id"] for task in provider_tasks if task["subject_id"] == ticker and task["id"].endswith(slugify(row.get("ID", ""))))
            item.planned_analysis_task_ids.extend(task["id"] for task in analysis_tasks if task["subject_id"] == ticker and task["id"].endswith(slugify(row.get("ID", ""))))
            if "." in ticker:
                item.findings.append(f"{label}: non-US/listing-specific ticker; some U.S.-centric providers may not resolve it.")
        if not item.tickers:
            item.findings.append("No ticker was available; company-name-only verification needs a future resolver.")
            findings.append(f"{row.get('ID', '')}: no ticker available for candidate {item.candidate}.")
        items.append(item)

    manifest = {
        "manifest_version": 1,
        "manifest_id": f"candidate_verification_{run_id}",
        "generated_at": datetime.combine(generated_at, datetime.min.time()).isoformat(),
        "run_type": "candidate_verification",
        "run_date": generated_at.isoformat(),
        "scope": ["US", "Europe"],
        "inputs": {
            "source_run_id": run_id,
            "candidate_review_report": f"agents/runs/{run_id}/market_research/{CANDIDATE_REVIEW_REPORT}",
            "approved_review_ids": [row.get("ID", "") for row in review_rows],
        },
        "provider_tasks": provider_tasks,
        "analysis_tasks": analysis_tasks,
        "outputs": {
            "verification_manifest": f"agents/runs/{run_id}/market_research/{CANDIDATE_VERIFICATION_MANIFEST}",
            "verification_plan": f"agents/runs/{run_id}/market_research/{CANDIDATE_VERIFICATION_REPORT}",
            "evidence_packets": f"agents/runs/{run_id}/evidence_packets/",
        },
    }
    return manifest, items, findings


def build_verification_item(row: dict[str, str], group: dict[str, str]) -> CandidateVerificationItem:
    tickers = [ticker.strip().upper() for ticker in group.get("Tickers", "").split(",") if ticker.strip()]
    return CandidateVerificationItem(
        review_item_id=row.get("ID", ""),
        candidate_group_id=group.get("Group ID", ""),
        candidate=normalize_ascii(group.get("Candidate", "")),
        tickers=tickers,
        decision_kind=normalize_ascii(group.get("Decision Kind", "")),
        review_status=normalize_ascii(row.get("Status", "")),
    )


def add_provider_tasks_for_ticker(
    tasks: list[dict[str, Any]],
    seen_task_ids: set[str],
    ticker: str,
    company: str,
    run_id: str,
    generated_at: date,
    review_id: str,
    root: Path | None = None,
) -> None:
    suffix = f"{slugify(ticker)}_{slugify(review_id)}"
    xai_stock_model = resolve_model_for_route(root, "xai_stock_sentiment").model
    candidates = [
        provider_task(
            task_id=f"candidate_yfinance_{suffix}",
            provider="yfinance",
            tool="company",
            subject_type="company",
            subject_id=ticker,
            args={"ticker": ticker, "run_id": run_id, "period": "5d"},
            reason=f"Candidate verification market-data snapshot for {ticker} from approved review {review_id}.",
            priority="high",
            source_bucket="candidate_review",
        ),
        provider_task(
            task_id=f"candidate_exa_news_{suffix}",
            provider="exa",
            tool="search",
            subject_type="company",
            subject_id=ticker,
            args={"mode": "news", "query": company_news_query(ticker, company), "run_id": run_id, "num_results": 8},
            reason=f"Candidate verification latest news scan for {ticker} from approved review {review_id}.",
            priority="high",
            source_bucket="candidate_review",
            follow_up=["Run Exa contents follow-up before company-file or monitoring promotion."],
        ),
        provider_task(
            task_id=f"candidate_exa_company_search_{suffix}",
            provider="exa",
            tool="search",
            subject_type="company",
            subject_id=ticker,
            args={"mode": "company", "query": company_search_query(ticker, company), "run_id": run_id, "num_results": 8},
            reason=f"Candidate verification company/source discovery scan for {ticker} from approved review {review_id}.",
            priority="high",
            source_bucket="candidate_review",
        ),
        provider_task(
            task_id=f"candidate_xai_x_search_{suffix}",
            provider="xai_grok",
            tool="x_search",
            subject_type="company",
            subject_id=ticker,
            args={
                "prompt": stock_sentiment_prompt(ticker, company),
                "run_id": run_id,
                "research_kind": "stock_sentiment",
                "model": xai_stock_model,
                **x_search_window_args(generated_at, days=14),
            },
            reason=f"Candidate verification Grok/X sentiment scan for {ticker} from approved review {review_id}.",
            priority="high",
            source_bucket="candidate_review",
        ),
    ]
    if "." not in ticker:
        candidates.extend(
            [
                provider_task(
                    task_id=f"candidate_fmp_{suffix}",
                    provider="fmp",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "include_statements": False},
                    reason=f"Candidate verification FMP fundamentals cross-check for {ticker}.",
                    priority="high",
                    source_bucket="candidate_review",
                ),
                provider_task(
                    task_id=f"candidate_alpha_vantage_{suffix}",
                    provider="alpha_vantage",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "include_statements": False},
                    reason=f"Candidate verification Alpha Vantage quote/overview cross-check for {ticker}.",
                    priority="medium",
                    source_bucket="candidate_review",
                    conditions=["Watch Alpha Vantage rate limits, especially on free keys."],
                ),
                provider_task(
                    task_id=f"candidate_polygon_{suffix}",
                    provider="polygon",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "adjusted": True},
                    reason=f"Candidate verification Polygon/Massive ticker/OHLC cross-check for {ticker}.",
                    priority="medium",
                    source_bucket="candidate_review",
                    conditions=["Best suited for U.S. tickers; treat failures as coverage gaps."],
                ),
                provider_task(
                    task_id=f"candidate_sec_{suffix}",
                    provider="sec_edgar",
                    tool="company",
                    subject_type="company",
                    subject_id=ticker,
                    args={"ticker": ticker, "run_id": run_id, "include_facts": False},
                    reason=f"Candidate verification SEC filings check for {ticker} if it resolves in SEC company tickers.",
                    priority="medium",
                    source_bucket="candidate_review",
                    conditions=["Run only if the ticker resolves in SEC company tickers."],
                ),
            ]
        )
    for task in candidates:
        if task["id"] in seen_task_ids:
            continue
        tasks.append(task)
        seen_task_ids.add(task["id"])


def add_analysis_tasks_for_ticker(
    tasks: list[dict[str, Any]],
    seen_task_ids: set[str],
    ticker: str,
    run_id: str,
    review_id: str,
) -> None:
    suffix = f"{slugify(ticker)}_{slugify(review_id)}"
    contents_id = f"candidate_company_news_contents_follow_up_{suffix}"
    candidates = [
        analysis_task(
            task_id=contents_id,
            tool="company_news_contents_follow_up",
            subject_id=ticker,
            args={"ticker": ticker, "run_id": run_id, "max_urls": 3},
            reason=f"Candidate verification Exa contents follow-up for {ticker} before any promotion.",
            priority="high",
            source_bucket="candidate_review",
            expected_artifacts=["exa_contents_evidence_packet", "exa_contents_raw_json"],
        ),
        analysis_task(
            task_id=f"candidate_company_news_review_{suffix}",
            tool="company_news_review",
            subject_id=ticker,
            args={"ticker": ticker, "run_id": run_id},
            reason=f"Candidate verification company-news review for {ticker}.",
            priority="high",
            source_bucket="candidate_review",
            depends_on=[contents_id],
            expected_artifacts=["company_news_specialist_evidence_packet", "company_news_review_json", "company_news_review_markdown"],
        ),
    ]
    compare_id = f"candidate_financial_compare_{suffix}"
    candidates.extend(
        [
            analysis_task(
                task_id=compare_id,
                tool="financial_compare",
                subject_id=ticker,
                args={"ticker": ticker, "run_id": run_id},
                reason=f"Candidate verification financial provider comparison for {ticker}.",
                priority="high",
                source_bucket="candidate_review",
            ),
            analysis_task(
                task_id=f"candidate_financial_review_{suffix}",
                tool="financial_review",
                subject_id=ticker,
                args={"ticker": ticker, "run_id": run_id},
                reason=f"Candidate verification financial review for {ticker}.",
                priority="high",
                source_bucket="candidate_review",
                depends_on=[compare_id],
                expected_artifacts=["financial_specialist_evidence_packet", "financial_review_json", "financial_review_markdown"],
            ),
        ]
    )
    for task in candidates:
        if task["id"] in seen_task_ids:
            continue
        tasks.append(task)
        seen_task_ids.add(task["id"])


def candidate_group_id_from_evidence(evidence: str) -> str:
    if "#" not in evidence:
        return ""
    return evidence.rsplit("#", 1)[-1].strip()


def format_candidate_verification_report(
    *,
    repo_root: Path,
    run_id: str,
    generated_at: date,
    status: str,
    items: list[CandidateVerificationItem],
    findings: list[str],
    manifest_path: Path,
) -> str:
    lines = [
        f"# Candidate Verification Plan: {run_id}",
        "",
        f"Generated: {generated_at.isoformat()}",
        f"Status: {status}",
        "",
        "## Purpose",
        "",
        "This file turns approved candidate-review rows into verification tasks. It does not add stocks to monitoring.",
        "",
        "## Manifest",
        "",
        f"- {manifest_path.relative_to(repo_root).as_posix()}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        lines.extend(f"- {finding}" for finding in findings)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Verification Items",
            "",
            "| Review ID | Group ID | Candidate | Tickers | Provider Tasks | Analysis Tasks | Findings |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if items:
        for item in items:
            lines.append(
                "| "
                + " | ".join(
                    escape_cell(value)
                    for value in [
                        item.review_item_id,
                        item.candidate_group_id,
                        item.candidate,
                        ", ".join(item.tickers),
                        ", ".join(item.planned_provider_task_ids),
                        ", ".join(item.planned_analysis_task_ids),
                        "; ".join(item.findings),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none |  |  |  |  |  | No approved candidates selected. |")
    lines.extend(
        [
            "",
            "## Next Step",
            "",
            "- Run provider tasks from the manifest, then analysis tasks from the same manifest.",
            "- Review company-research output before any monitoring promotion.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def candidate_followup_to_dict(result: CandidateFollowupResult) -> dict[str, Any]:
    return {
        "run_id": result.run_id,
        "generated_at": result.generated_at,
        "status": result.status,
        "review_ids": result.review_ids,
        "verification_items": [asdict(item) for item in result.verification_items],
        "provider_task_count": result.provider_task_count,
        "analysis_task_count": result.analysis_task_count,
        "findings": result.findings,
        "written_paths": result.written_paths,
    }


def escape_cell(value: Any) -> str:
    return normalize_ascii(str(value)).replace("|", "/").replace("\n", " ").strip()
