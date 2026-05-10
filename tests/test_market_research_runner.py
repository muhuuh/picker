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


if __name__ == "__main__":
    unittest.main()
