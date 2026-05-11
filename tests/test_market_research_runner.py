from __future__ import annotations

from contextlib import redirect_stdout
from dataclasses import replace
from datetime import date
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.cli import main
from stock_research.evidence import Claim, Source, new_packet, write_packet
from stock_research.market_research_runner import (
    build_manual_market_manifest,
    evaluate_candidate_leads_quality,
    extract_candidate_leads,
    run_manual_market_research,
)
from stock_research.candidate_review import build_candidate_review, group_candidate_leads
from stock_research.candidate_followup import build_candidate_verification_followup
from stock_research.candidate_promotion import build_candidate_monitoring_promotion
from stock_research.candidate_verification_result import build_candidate_verification_result
from stock_research.agent_runtime.outputs import CandidateLead


REPO_ROOT = Path(__file__).resolve().parents[1]


class MarketResearchRunnerTests(unittest.TestCase):
    def test_manual_market_manifest_plans_exa_and_grok_discovery_lanes(self):
        manifest = build_manual_market_manifest(
            topic="robotics suppliers in Europe",
            subject_type="industry",
            subject_id="robotics_suppliers_in_europe",
            run_id="test_manual_market",
            current_date=date(2026, 5, 10),
            days=21,
        )
        tasks = {task["id"]: task for task in manifest["provider_tasks"]}

        self.assertEqual(tasks["manual_exa_context_robotics_suppliers_in_europe"]["provider"], "exa")
        self.assertEqual(tasks["manual_exa_context_robotics_suppliers_in_europe"]["args"]["mode"], "industry")
        self.assertEqual(tasks["manual_exa_company_discovery_robotics_suppliers_in_europe"]["args"]["mode"], "company")
        self.assertEqual(tasks["manual_xai_x_search_robotics_suppliers_in_europe"]["provider"], "xai_grok")
        self.assertEqual(tasks["manual_xai_x_search_robotics_suppliers_in_europe"]["args"]["from_date"], "2026-04-19")
        self.assertTrue(tasks["manual_xai_x_search_robotics_suppliers_in_europe"]["args"]["enable_image_understanding"])

    def test_candidate_extraction_marks_grok_only_and_exa_verified_leads(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_rejected_csv(root, "COOL", "2026-06-01")
            packets = [
                packet(
                    provider="xai_grok",
                    subject_id="robotics_suppliers_in_europe",
                    claim="X accounts are hyping $ROBO and sharing an unconfirmed rumor about $COOL.",
                    evidence="$ROBO is described as bullish; $COOL is a rumor only.",
                    source_id="grok-1",
                ),
                packet(
                    provider="exa",
                    subject_id="robotics_suppliers_in_europe",
                    claim="ROBO appears in public-company supplier coverage for robotics.",
                    evidence="Ticker ROBO is mentioned by a source-backed Exa result.",
                    source_id="exa-1",
                ),
            ]

            leads = {lead.ticker: lead for lead in extract_candidate_leads(packets=packets, root=root, current_date=date(2026, 5, 10))}

        self.assertEqual(leads["ROBO"].verification_status, "verified")
        self.assertEqual(leads["ROBO"].next_action, "human_review")
        self.assertEqual(sorted(leads["ROBO"].source_channels), ["exa", "grok"])
        self.assertEqual(leads["COOL"].verification_status, "grok_only")
        self.assertEqual(leads["COOL"].rejected_cooldown_status, "cooldown_active")
        self.assertEqual(leads["COOL"].next_action, "ignore")
        self.assertTrue(leads["COOL"].rumor_flag)

    def test_candidate_extraction_ignores_country_parentheses(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_rejected_csv(root, "", "")
            exa_packet = packet(
                provider="exa",
                subject_id="robotics_suppliers_in_europe",
                claim="Relevant Exa result: KUKA",
                evidence="KUKA (KU2) is a robotics company operating in 53 countries (including Germany, France, and Italy).",
                source_id="exa-1",
            )

            leads = {lead.ticker: lead for lead in extract_candidate_leads(packets=[exa_packet], root=root, current_date=date(2026, 5, 10))}

        self.assertIn("KU2", leads)
        self.assertNotIn("GERMANY", leads)
        self.assertNotIn("FRANCE", leads)
        self.assertEqual(leads["KU2"].company_name, "KUKA")

    def test_discovery_quality_gate_blocks_grok_only_promotion(self):
        findings = evaluate_candidate_leads_quality(
            [
                CandidateLead(
                    ticker="HYPE",
                    source_channels=["grok"],
                    source_ids=["grok-1"],
                    verification_status="grok_only",
                    next_action="add_to_monitoring",
                )
            ]
        )

        self.assertTrue(any("Grok-only lead cannot be promoted" in finding for finding in findings))

    def test_manual_market_research_writes_report_with_candidates(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            evidence_dir = root / "agents" / "runs" / run_id / "evidence_packets"
            write_packet(
                packet(
                    provider="xai_grok",
                    subject_id="robotics_suppliers_in_europe",
                    claim="X users are hyping $ROBO as a robotics supplier.",
                    evidence="$ROBO is a Grok-only social lead until verified.",
                    source_id="grok-1",
                ),
                evidence_dir / "grok.json",
            )
            write_packet(
                packet(
                    provider="exa",
                    subject_id="robotics_suppliers_in_europe",
                    claim="ROBO appears in supplier-discovery coverage.",
                    evidence="Ticker ROBO is mentioned in an Exa source.",
                    source_id="exa-1",
                ),
                evidence_dir / "exa.json",
            )

            result = run_manual_market_research(
                root=root,
                topic="robotics suppliers in Europe",
                subject_type="industry",
                subject_id="robotics_suppliers_in_europe",
                run_id=run_id,
                write=True,
                execute_providers=False,
                execute_orchestrator=False,
                current_date=date(2026, 5, 10),
            )
            report_path = root / "agents" / "runs" / run_id / "market_research" / "robotics_suppliers_in_europe_manual_market_research.md"
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.status, "dry_run")
        self.assertEqual(result.quality_findings, [])
        self.assertIn("| ROBO | exa, grok | verified", report)
        self.assertIn("## Discovery Quality Gate", report)
        self.assertTrue(any(path.endswith("_candidate_leads.json") for path in result.written_paths))

    def test_market_research_cli_dry_run_is_easy_manual_entrypoint(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = main(
                [
                    "--root",
                    str(REPO_ROOT),
                    "market-research",
                    "run",
                    "--topic",
                    "grid scale energy storage",
                    "--subject-type",
                    "theme",
                    "--today",
                    "2026-05-10",
                ]
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["status"], "dry_run")
        self.assertEqual(payload["provider_result"]["planned_count"], 3)
        self.assertFalse(payload["live_model_called"])

    def test_candidate_review_groups_duplicate_share_classes_by_company_name(self):
        groups = group_candidate_leads(
            [
                CandidateLead(
                    ticker="EXA",
                    company_name="Exail Technologies",
                    source_channels=["exa"],
                    source_ids=["exa-1"],
                    verification_status="exa_only",
                    next_action="verify",
                ),
                CandidateLead(
                    ticker="EXA.PA",
                    company_name="Exail Technologies",
                    source_channels=["exa"],
                    source_ids=["exa-2"],
                    verification_status="exa_only",
                    next_action="verify",
                ),
                CandidateLead(
                    ticker="EXALF",
                    company_name="Exail Technologies",
                    source_channels=["grok"],
                    source_ids=["grok-1"],
                    verification_status="grok_only",
                    next_action="verify",
                    hype_level="high",
                ),
            ]
        )

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0].canonical_name, "Exail Technologies")
        self.assertEqual(groups[0].tickers, ["EXA", "EXA.PA", "EXALF"])
        self.assertEqual(groups[0].verification_status, "verified")
        self.assertEqual(groups[0].decision_kind, "monitoring_candidate")

    def test_candidate_review_writes_report_and_duplicate_safe_review_queue(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            market_dir = root / "agents" / "runs" / run_id / "market_research"
            market_dir.mkdir(parents=True, exist_ok=True)
            (market_dir / "robotics_candidate_leads.json").write_text(
                json.dumps(
                    [
                        {
                            "ticker": "ROBO",
                            "company_name": "Robo Holdings",
                            "source_channels": ["exa", "grok"],
                            "source_ids": ["exa-1", "grok-1"],
                            "verification_status": "verified",
                            "hype_level": "high",
                            "next_action": "human_review",
                            "rejected_cooldown_status": "not_rejected",
                            "why_surfaced": "Exa and Grok both surfaced this robotics supplier.",
                        },
                        {
                            "ticker": "HYPE",
                            "source_channels": ["grok"],
                            "source_ids": ["grok-2"],
                            "verification_status": "grok_only",
                            "hype_level": "high",
                            "next_action": "verify",
                            "rumor_flag": True,
                            "rejected_cooldown_status": "not_rejected",
                            "why_surfaced": "Grok/X chatter surfaced a rumor-like lead.",
                        },
                    ],
                    indent=2,
                ),
                encoding="utf-8",
            )

            first = build_candidate_review(
                root=root,
                run_id=run_id,
                current_date=date(2026, 5, 10),
                write=True,
                queue_review=True,
            )
            second = build_candidate_review(
                root=root,
                run_id=run_id,
                current_date=date(2026, 5, 10),
                write=True,
                queue_review=True,
            )
            queue = (root / "agents" / "human_review_queue.md").read_text(encoding="utf-8")
            report = (market_dir / "candidate_review.md").read_text(encoding="utf-8")

        self.assertEqual(first.status, "ready_for_human_review")
        self.assertEqual(second.status, "ready_for_human_review")
        self.assertEqual(queue.count("candidate_review.md#CRG-0001"), 1)
        self.assertEqual(queue.count("candidate_review.md#CRG-0002"), 1)
        self.assertIn("| CRG-0001 | Robo Holdings | ROBO | exa, grok | verified", report)
        self.assertIn("verify_grok_lead", report)

    def test_market_research_candidate_review_cli(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            market_dir = root / "agents" / "runs" / run_id / "market_research"
            market_dir.mkdir(parents=True, exist_ok=True)
            (market_dir / "grid_candidate_leads.json").write_text(
                json.dumps(
                    [
                        {
                            "ticker": "ADSE",
                            "company_name": "ADS-TEC Energy",
                            "source_channels": ["exa"],
                            "source_ids": ["exa-1"],
                            "verification_status": "exa_only",
                            "next_action": "verify",
                            "rejected_cooldown_status": "not_rejected",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "market-research",
                        "candidate-review",
                        "--run-id",
                        run_id,
                        "--write",
                        "--queue-review",
                        "--today",
                        "2026-05-10",
                    ]
                )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ready_for_human_review")
        self.assertEqual(payload["groups"][0]["canonical_name"], "ADS-TEC Energy")
        self.assertTrue(any(path.endswith("candidate_review.md") for path in payload["written_paths"]))

    def test_candidate_followup_requires_approved_review_row(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="open")

            result = build_candidate_verification_followup(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )

        self.assertEqual(result.status, "blocked")
        self.assertIn("not 'approved'", result.findings[0])
        self.assertEqual(result.provider_task_count, 0)

    def test_candidate_followup_writes_verification_manifest_for_approved_candidate(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")

            result = build_candidate_verification_followup(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )
            manifest_path = root / "agents" / "runs" / run_id / "market_research" / "candidate_verification_manifest.json"
            report_path = root / "agents" / "runs" / run_id / "market_research" / "candidate_verification_plan.md"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.status, "ready_for_verification")
        self.assertEqual(result.provider_task_count, 8)
        self.assertEqual(result.analysis_task_count, 4)
        self.assertEqual(manifest["run_type"], "candidate_verification")
        self.assertIn("candidate_exa_news_robo_hrq_0004", {task["id"] for task in manifest["provider_tasks"]})
        self.assertIn("candidate_financial_review_robo_hrq_0004", {task["id"] for task in manifest["analysis_tasks"]})
        self.assertIn("It does not add stocks to monitoring", report)

    def test_market_research_candidate_followup_cli(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "market-research",
                        "candidate-followup",
                        "--run-id",
                        run_id,
                        "--review-id",
                        "HRQ-0004",
                        "--write",
                        "--today",
                        "2026-05-10",
                    ]
                )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ready_for_verification")
        self.assertEqual(payload["review_ids"], ["HRQ-0004"])
        self.assertTrue(any(path.endswith("candidate_verification_manifest.json") for path in payload["written_paths"]))

    def test_candidate_verification_result_summarizes_missing_provider_and_review_status(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")
            build_candidate_verification_followup(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )
            write_candidate_verification_artifacts(root, run_id, "ROBO", include_fmp_packet=False, financial_status="needs_human_review")

            result = build_candidate_verification_result(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )
            report_path = root / "agents" / "runs" / run_id / "market_research" / "candidate_verification_result.md"
            report = report_path.read_text(encoding="utf-8")

        self.assertEqual(result.status, "needs_human_review")
        self.assertTrue(any("Missing provider evidence" in finding for finding in result.findings))
        self.assertIn("fmp", result.items[0].findings[0])
        self.assertIn("needs_human_review", report)
        self.assertIn("candidate_fmp_robo_hrq_0004", report)
        self.assertIn("candidate_verification_result.md", result.written_paths[1])

    def test_market_research_candidate_verification_result_cli(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")
            build_candidate_verification_followup(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )
            write_candidate_verification_artifacts(root, run_id, "ROBO", include_fmp_packet=True, financial_status="ready_for_company_update")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "market-research",
                        "candidate-verification-result",
                        "--run-id",
                        run_id,
                        "--review-id",
                        "HRQ-0004",
                        "--write",
                        "--today",
                        "2026-05-10",
                    ]
                )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ready_for_promotion_review")
        self.assertTrue(any(path.endswith("candidate_verification_result.md") for path in payload["written_paths"]))

    def test_candidate_promotion_blocks_without_approval(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="open")
            write_candidate_verification_artifacts(root, run_id, "ROBO")

            result = build_candidate_monitoring_promotion(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )

        self.assertEqual(result.status, "blocked")
        self.assertTrue(any("not 'approved'" in finding for finding in result.findings))

    def test_candidate_promotion_blocks_without_verification_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")

            result = build_candidate_monitoring_promotion(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=False,
            )

        self.assertEqual(result.status, "blocked")
        self.assertTrue(any("Missing verification manifest" in finding for finding in result.findings))

    def test_candidate_promotion_writes_monitoring_row_and_company_file(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")
            write_candidate_verification_artifacts(root, run_id, "ROBO")

            result = build_candidate_monitoring_promotion(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )
            repeat_result = build_candidate_monitoring_promotion(
                root=root,
                run_id=run_id,
                review_id="HRQ-0004",
                current_date=date(2026, 5, 10),
                write=True,
            )
            monitoring = (root / "stock_tracking" / "monitoring" / "monitoring.csv").read_text(encoding="utf-8")
            company_file = root / "stock_tracking" / "stock_info_files" / "monitoring" / "ROBO.md"
            report = root / "agents" / "runs" / run_id / "market_research" / "candidate_promotion_report.md"
            company_file_exists = company_file.exists()
            company_file_text = company_file.read_text(encoding="utf-8")
            report_exists = report.exists()

        self.assertEqual(result.status, "promoted")
        self.assertEqual(repeat_result.status, "already_promoted")
        self.assertIn("ROBO,Robo Holdings", monitoring)
        self.assertEqual(sum(1 for line in monitoring.splitlines() if line.startswith("ROBO,")), 1)
        self.assertTrue(company_file_exists)
        self.assertIn("not an investment recommendation", company_file_text)
        self.assertTrue(report_exists)

    def test_market_research_candidate_promote_cli(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            write_minimal_repo(root)
            run_id = "2026-05-10_manual-market"
            write_candidate_review_artifacts(root, run_id, status="approved")
            write_candidate_verification_artifacts(root, run_id, "ROBO")
            buffer = io.StringIO()
            with redirect_stdout(buffer):
                exit_code = main(
                    [
                        "--root",
                        str(root),
                        "market-research",
                        "candidate-promote",
                        "--run-id",
                        run_id,
                        "--review-id",
                        "HRQ-0004",
                        "--write",
                        "--today",
                        "2026-05-10",
                    ]
                )
            payload = json.loads(buffer.getvalue())

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "promoted")
        self.assertEqual(payload["item"]["ticker"], "ROBO")


def packet(provider: str, subject_id: str, claim: str, evidence: str, source_id: str):
    source = Source(
        source_id=source_id,
        provider=provider,
        source_type="social" if provider == "xai_grok" else "web",
        url=f"https://example.com/{source_id}",
    )
    packet_obj = new_packet(
        provider=provider,
        subject_type="industry",
        subject_id=subject_id,
        time_window="test",
        current_date=date(2026, 5, 10),
        sources=[source],
        claims=[Claim(claim=claim, evidence=evidence, source_ids=[source_id], confidence="medium")],
    )
    return replace(packet_obj, packet_id=f"{packet_obj.packet_id}_{source_id}")


def write_minimal_repo(root: Path) -> None:
    (root / "AGENTS.md").write_text("# Test agents\n", encoding="utf-8")
    (root / "MEMORY.md").write_text("# Memory\n", encoding="utf-8")
    (root / "stock_tracking" / "rejected").mkdir(parents=True, exist_ok=True)
    (root / "stock_tracking" / "rejected" / "rejected.csv").write_text(
        "ticker,company_name,next_eligible_review_date\n",
        encoding="utf-8",
    )
    memory_dir = root / "agents" / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "README.md",
        "memory_index.md",
        "orchestrator_lessons.md",
        "source_quality.md",
        "specialist_playbooks.md",
        "evaluation_metrics.md",
        "deprecated_memory.md",
    ):
        (memory_dir / name).write_text("# Test memory\n", encoding="utf-8")


def write_rejected_csv(root: Path, ticker: str, next_eligible: str) -> None:
    target = root / "stock_tracking" / "rejected"
    target.mkdir(parents=True, exist_ok=True)
    (target / "rejected.csv").write_text(
        "ticker,company_name,next_eligible_review_date\n"
        f"{ticker},{ticker} Inc.,{next_eligible}\n",
        encoding="utf-8",
    )


def write_candidate_review_artifacts(root: Path, run_id: str, status: str) -> None:
    market_dir = root / "agents" / "runs" / run_id / "market_research"
    market_dir.mkdir(parents=True, exist_ok=True)
    (market_dir / "candidate_review.md").write_text(
        "\n".join(
            [
                f"# Candidate Review: {run_id}",
                "",
                "## Candidate Groups",
                "",
                "| Group ID | Candidate | Tickers | Channels | Verification | Hype | Cooldown | Decision Kind | Priority | Why surfaced |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                "| CRG-0001 | Robo Holdings | ROBO | exa, grok | verified | high | not_rejected | monitoring_candidate | high | Exa and Grok surfaced the candidate. |",
                "",
                "## Human Review Bridge",
                "",
                "| Review Item ID | Candidate | Decision Kind | Priority | Question | Reason |",
                "| --- | --- | --- | --- | --- | --- |",
                "| CRG-0001 | Robo Holdings (ROBO) | monitoring_candidate | high | Approve adding this candidate to monitoring, or request more research first. | Candidate surfaced from exa, grok. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "agents").mkdir(parents=True, exist_ok=True)
    (root / "agents" / "human_review_queue.md").write_text(
        "\n".join(
            [
                "# Human Review Queue",
                "",
                "## Review Items",
                "",
                "| ID | Date Added | Item | Decision Needed | Priority | Status | Related Files | Evidence / Run Link | Notes |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                f"| HRQ-0004 | 2026-05-10 | Review verified discovery candidate Robo Holdings (ROBO) for possible monitoring. | Approve adding this candidate to monitoring, or request more research first. | high | {status} | agents/runs/{run_id}/market_research | agents/runs/{run_id}/market_research/candidate_review.md#CRG-0001 | Candidate surfaced from exa/grok. |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def write_candidate_verification_artifacts(
    root: Path,
    run_id: str,
    ticker: str,
    include_fmp_packet: bool = True,
    financial_status: str = "ready_for_company_update",
) -> None:
    market_dir = root / "agents" / "runs" / run_id / "market_research"
    market_dir.mkdir(parents=True, exist_ok=True)
    (market_dir / "candidate_verification_manifest.json").write_text(
        json.dumps(
            {
                "provider_tasks": [
                    {"id": "candidate_yfinance_robo_hrq_0004", "provider": "yfinance", "subject_id": ticker},
                    {"id": "candidate_fmp_robo_hrq_0004", "provider": "fmp", "subject_id": ticker},
                ],
                "analysis_tasks": [
                    {"id": "candidate_company_news_review_robo_hrq_0004", "tool": "company_news_review", "subject_id": ticker},
                    {"id": "candidate_financial_review_robo_hrq_0004", "tool": "financial_review", "subject_id": ticker},
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    evidence_dir = root / "agents" / "runs" / run_id / "evidence_packets"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    write_packet(new_packet("yfinance", "company", ticker, current_date=date(2026, 5, 10)), evidence_dir / f"2026-05-10_yfinance_company_{ticker.lower()}.json")
    if include_fmp_packet:
        write_packet(new_packet("fmp", "company", ticker, current_date=date(2026, 5, 10)), evidence_dir / f"2026-05-10_fmp_company_{ticker.lower()}.json")
    news_dir = root / "agents" / "runs" / run_id / "reports" / "company_news_specialist"
    financial_dir = root / "agents" / "runs" / run_id / "reports" / "financial_data_specialist"
    news_dir.mkdir(parents=True, exist_ok=True)
    financial_dir.mkdir(parents=True, exist_ok=True)
    (news_dir / f"{ticker}_company_news_review.md").write_text("# News review\n\nStatus: ready_for_company_update\n", encoding="utf-8")
    (financial_dir / f"{ticker}_financial_review.md").write_text(f"# Financial review\n\nStatus: {financial_status}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
