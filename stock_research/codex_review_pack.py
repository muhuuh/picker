from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .memory import relative_to_root
from .repo import find_repo_root


@dataclass(frozen=True)
class CodexReviewPack:
    run_id: str
    status: str
    expected_output_path: str
    required_artifacts: list[dict[str, Any]]
    human_synthesis_packs: list[dict[str, Any]]
    final_human_report_targets: list[dict[str, Any]]
    post_codex_quality_command: str
    company_reports: list[dict[str, Any]]
    memory_artifacts: list[dict[str, Any]]
    hygiene_artifacts: list[dict[str, Any]]
    human_review_artifacts: list[dict[str, Any]]
    quality_findings: list[str]
    codex_instructions: list[str]
    written_paths: list[str]


def build_codex_review_pack(root: Path | None, run_id: str) -> CodexReviewPack:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / run_id
    expected_output_path = f"agents/runs/{run_id}/codex_supervised_review.md"

    required_artifacts = [
        artifact(repo_root, run_dir / "manifest.json", "Recurring portfolio scope, industry clusters, provider roles, freshness, and accepted comparison baseline."),
        artifact(repo_root, run_dir / "final_digest.md", "Primary quick-read digest. Start here."),
        artifact(repo_root, run_dir / "quality_report.md", "Deterministic quality findings and provider/report coverage."),
        artifact(repo_root, run_dir / "run_summary.md", "Provider, evidence, and run coverage summary."),
        artifact(repo_root, run_dir / "finalization.md", "Run-end reflection, recurring issues, and archive proposals."),
        artifact(repo_root, repo_root / "agents" / "human_review_digest.md", "Current user decision inbox."),
        artifact(repo_root, run_dir / "company_file_factual_updates.md", "FYI summary of scoped factual company-file sync.", required=False),
        artifact(repo_root, run_dir / "category_state_updates.md", "FYI summary of holdings/monitoring/rejected state updates.", required=False),
    ]
    human_synthesis_packs = sorted_artifacts(
        repo_root,
        run_dir / "reports" / "human_synthesis",
        "*_synthesis_pack.md",
        "Codex app final-report evidence pack.",
    )
    final_human_report_targets = final_report_targets_for_synthesis_packs(repo_root, human_synthesis_packs)
    post_codex_quality_command = (
        f"python -m stock_research quality-report --run-id {run_id} --write --require-final-reports"
    )
    company_reports = sorted_artifacts(
        repo_root,
        run_dir / "reports" / "opportunity_assessment",
        "*_opportunity_assessment.md",
        "Deterministic opportunity audit trail.",
    )
    memory_artifacts = [
        artifact(repo_root, run_dir / "memory_reflection.md", "Post-run operational lessons and update proposals."),
        artifact(repo_root, run_dir / "memory_update_drafts.md", "Schema-ready memory draft updates, if any.", required=False),
        artifact(repo_root, run_dir / "memory_writer_review.md", "Deterministic or optional LLM review of memory drafts.", required=False),
    ]
    hygiene_artifacts = [
        artifact(repo_root, run_dir / "archive_proposals.md", "Run-local archive/hygiene proposals.", required=False),
        artifact(repo_root, repo_root / "archive" / "research_index.md", "Global generated-artifact index.", required=False),
    ]
    human_review_artifacts = [
        artifact(repo_root, repo_root / "agents" / "human_review_digest.md", "Primary open-decision digest."),
        artifact(repo_root, repo_root / "agents" / "human_review_queue.md", "Durable review queue state."),
        artifact(repo_root, run_dir / "human_review_digest_summary.md", "Run-local review digest pointer.", required=False),
    ]

    quality_findings = pack_quality_findings(
        repo_root=repo_root,
        required_artifacts=required_artifacts,
        company_reports=company_reports,
        run_dir=run_dir,
    )
    status = "ready" if not quality_findings else "needs_review"
    return CodexReviewPack(
        run_id=run_id,
        status=status,
        expected_output_path=expected_output_path,
        required_artifacts=required_artifacts,
        human_synthesis_packs=human_synthesis_packs,
        final_human_report_targets=final_human_report_targets,
        post_codex_quality_command=post_codex_quality_command,
        company_reports=company_reports,
        memory_artifacts=memory_artifacts,
        hygiene_artifacts=hygiene_artifacts,
        human_review_artifacts=human_review_artifacts,
        quality_findings=quality_findings,
        codex_instructions=codex_supervised_instructions(run_id, expected_output_path),
        written_paths=[],
    )


def write_codex_review_pack(root: Path | None, pack: CodexReviewPack) -> tuple[Path, Path]:
    repo_root = find_repo_root(root)
    run_dir = repo_root / "agents" / "runs" / pack.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    json_path = run_dir / "codex_supervised_review_pack.json"
    md_path = run_dir / "codex_supervised_review_pack.md"
    payload = codex_review_pack_to_dict(pack)
    payload["written_paths"] = [
        relative_to_root(repo_root, json_path).as_posix(),
        relative_to_root(repo_root, md_path).as_posix(),
    ]
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(format_codex_review_pack_markdown(pack), encoding="utf-8")
    return json_path, md_path


def codex_review_pack_to_dict(pack: CodexReviewPack) -> dict[str, Any]:
    return asdict(pack)


def artifact(repo_root: Path, path: Path, purpose: str, *, required: bool = True) -> dict[str, Any]:
    return {
        "path": relative_to_root(repo_root, path).as_posix(),
        "exists": path.exists(),
        "required": required,
        "purpose": purpose,
    }


def sorted_artifacts(repo_root: Path, directory: Path, pattern: str, purpose: str) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    return [
        artifact(repo_root, path, purpose, required=False)
        for path in sorted(directory.glob(pattern))
        if path.is_file()
    ]


def final_report_targets_for_synthesis_packs(repo_root: Path, packs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    for pack in packs:
        pack_path = Path(str(pack["path"]))
        if not pack_path.name.endswith("_synthesis_pack.md"):
            continue
        target_name = pack_path.name.replace("_synthesis_pack.md", "_final_human_report.md")
        target_path = repo_root / pack_path.parent / target_name
        targets.append(
            artifact(
                repo_root,
                target_path,
                "Codex app-written per-ticker final report.",
                required=False,
            )
        )
    return targets


def pack_quality_findings(
    *,
    repo_root: Path,
    required_artifacts: list[dict[str, Any]],
    company_reports: list[dict[str, Any]],
    run_dir: Path,
) -> list[str]:
    findings = [
        f"Missing required artifact: {item['path']}"
        for item in required_artifacts
        if item["required"] and not item["exists"]
    ]
    if not company_reports:
        findings.append("No opportunity assessment reports were found; Codex should inspect whether analysis execution failed or no tracked tickers exist.")
    human_synthesis_dir = run_dir / "reports" / "human_synthesis"
    if company_reports and not list(human_synthesis_dir.glob("*_synthesis_pack.md")):
        findings.append("No human synthesis packs were found; Codex cannot write final per-ticker human reports from first-principles inputs.")
    quality_report_json = run_dir / "quality_report.json"
    if quality_report_json.exists():
        quality = read_json(quality_report_json)
        for finding in quality.get("findings") or []:
            severity = finding.get("severity", "unknown")
            category = finding.get("category", "quality")
            summary = finding.get("summary", "Unspecified quality finding")
            evidence = finding.get("evidence", "")
            findings.append(f"Quality report finding: [{severity}] {category}: {summary} ({evidence})")
    final_digest_json = run_dir / "final_digest.json"
    if final_digest_json.exists():
        digest = read_json(final_digest_json)
        for finding in digest.get("quality_findings") or []:
            findings.append(f"Final digest quality finding: {finding}")
        if int(digest.get("ticker_count") or 0) != len(company_reports):
            findings.append(
                f"Final digest ticker count ({digest.get('ticker_count')}) differs from opportunity report count ({len(company_reports)})."
            )
    return unique(findings)


def codex_supervised_instructions(run_id: str, expected_output_path: str) -> list[str]:
    post_codex_quality_command = (
        f"python -m stock_research quality-report --run-id {run_id} --write --require-final-reports"
    )
    return [
        "Use Codex GPT-5.5 high as the outer orchestrator. Do not run the OpenAI API SDK orchestrator unless the user explicitly asks for remote/headless fallback or SDK debugging.",
        "Read this review pack first, then read every existing required artifact and every human synthesis pack listed below. Use opportunity assessments as audit/evidence artifacts, not as final prose to patch together.",
        "Read `manifest.json` recurring_coverage before synthesis. Use its company coverage reasons, deduplicated industry clusters, freshness, provider roles, and explicit accepted comparison baseline. Never substitute the latest generated run for an accepted baseline.",
        "Write or update the Codex-supervised final review at "
        f"`{expected_output_path}`. This file is the human-facing synthesis for the scheduled run.",
        "For every human synthesis pack, write or refresh the matching canonical `reports/human_synthesis/{TICKER}_final_human_report.md` target from first principles. This is the reader-facing company/opportunity report; `reports/opportunity_assessment/` is the deterministic audit trail.",
        "Do not create separate side reports, alternate report names, or chat-only report artifacts for automation-style stock research. If a report needs correction, overwrite the same canonical final human report target.",
        "Each final human report should include: bottom line, business context, what changed, material X/Grok narrative shifts, source-backed news, valuation/financial flags, non-obvious opportunities/risks, what changed vs existing company files, open human decisions, and next actions.",
        "If a human-facing report is obviously poor, duplicated, over-compressed, stale, or missing key X/Grok/web insight, fix the synthesis pack, formatter, prompt, or provider coverage and regenerate the affected artifact before finalizing.",
        f"After writing `codex_supervised_review.md` and all final human reports, run `{post_codex_quality_command}`. Do not finish the supervised run while it reports missing, orphaned, shallow, or malformed final human reports.",
        "Keep low-risk factual company-file updates as FYI. Do not ask for approval for routine source-backed factual syncs. Do ask for approval for thesis/status/strategy/buy/sell/position-size changes.",
        "Do not make trades, do not silently move stocks between holdings/monitoring/rejected, and do not auto-approve human-review rows.",
        "Review memory artifacts. If the run produced a durable operational lesson, update `agents/memory/` through the deterministic memory workflow or update the relevant scratchpad/backlog when that is the right scope.",
        "Review artifact hygiene and category state updates. Preserve active reports, keep old inactive material discoverable through the archive index, and avoid cluttering active context with stale run artifacts.",
        "End with a concise verdict: result quality, whether expectations were met, verification run, remaining risks, open human decisions, and the next backlog-driven step.",
    ]


def format_codex_review_pack_markdown(pack: CodexReviewPack) -> str:
    lines = [
        f"# Codex-Supervised Review Pack: {pack.run_id}",
        "",
        f"Status: {pack.status}",
        f"Expected Codex output: `{pack.expected_output_path}`",
        f"Post-Codex quality gate: `{pack.post_codex_quality_command}`",
        "",
        "## Purpose",
        "",
        "This pack is the deterministic handoff from Python to Codex app automation. The lower-cost scheduled workflow uses provider and analysis code to gather evidence, then asks Codex to synthesize, quality-check, and update repo memory/state without running the OpenAI API SDK orchestrator.",
        "",
        "## Codex Instructions",
        "",
    ]
    lines.extend(f"{index}. {instruction}" for index, instruction in enumerate(pack.codex_instructions, 1))
    lines.extend(["", "## Required Artifacts", ""])
    append_artifact_table(lines, pack.required_artifacts)
    lines.extend(["", "## Human Synthesis Packs", ""])
    append_artifact_table(lines, pack.human_synthesis_packs)
    lines.extend(["", "## Final Human Report Targets", ""])
    append_artifact_table(lines, pack.final_human_report_targets)
    lines.extend(
        [
            "",
            "After Codex writes or refreshes those targets, rerun the post-Codex quality gate. It must be clean before the run is treated as complete.",
        ]
    )
    lines.extend(["", "## Opportunity Assessment Reports", ""])
    append_artifact_table(lines, pack.company_reports)
    lines.extend(["", "## Human Review Artifacts", ""])
    append_artifact_table(lines, pack.human_review_artifacts)
    lines.extend(["", "## Memory And Learning Artifacts", ""])
    append_artifact_table(lines, pack.memory_artifacts)
    lines.extend(["", "## Hygiene And State Artifacts", ""])
    append_artifact_table(lines, pack.hygiene_artifacts)
    lines.extend(["", "## Quality Findings To Resolve Or Explain", ""])
    if pack.quality_findings:
        lines.extend(f"- {finding}" for finding in pack.quality_findings)
    else:
        lines.append("- None detected by the deterministic review-pack builder.")
    lines.extend(
        [
            "",
            "## API Workflow Fallback",
            "",
            "The OpenAI Agents SDK workflow remains available for remote/headless API mode, traces, and debugging when Codex app supervision is unavailable:",
            "",
            "```powershell",
            "C:\\Python313\\python.exe -m stock_research run-weekly --write --execute-providers --execute-analysis --execute-orchestrator --orchestrator-timeout-seconds 900",
            "```",
            "",
            "Do not use API mode in the scheduled Codex-supervised automation unless the user explicitly asks for remote/headless fallback or SDK debugging.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def append_artifact_table(lines: list[str], rows: list[dict[str, Any]]) -> None:
    if not rows:
        lines.append("- None found.")
        return
    lines.extend(["| Status | Required | Artifact | Purpose |", "| --- | --- | --- | --- |"])
    for row in rows:
        status = "present" if row["exists"] else "missing"
        required = "yes" if row["required"] else "no"
        lines.append(f"| {status} | {required} | `{row['path']}` | {row['purpose']} |")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def unique(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result
