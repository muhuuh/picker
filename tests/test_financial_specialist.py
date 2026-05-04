from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import Claim, Contradiction, Source, new_packet, validate_packet, write_packet
from stock_research.financial_specialist import build_financial_specialist_packet


class FinancialSpecialistTests(unittest.TestCase):
    def test_financial_review_writes_packet_raw_and_report(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            packet_path = write_compare_packet(root, conflicts=False)

            result = build_financial_specialist_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 4),
                financial_compare_packet_path=packet_path,
            )

            self.assertEqual(result.packet.provider, "financial_data_specialist")
            self.assertEqual(result.review["status"], "ready_for_company_update")
            self.assertEqual(validate_packet(result.packet).errors, [])
            self.assertEqual(len(result.paths), 3)
            for path in result.paths:
                self.assertTrue(path.exists())
            self.assertIn("Financial Review", result.paths[2].read_text(encoding="utf-8"))

    def test_financial_review_requires_human_review_for_conflicts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            packet_path = write_compare_packet(root, conflicts=True)

            result = build_financial_specialist_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 4),
                financial_compare_packet_path=packet_path,
            )

            self.assertEqual(result.review["status"], "needs_human_review")
            self.assertEqual(validate_packet(result.packet).errors, [])
            self.assertTrue(result.packet.recommended_updates[0].needs_human_review)
            self.assertTrue(result.packet.risks)


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


def write_compare_packet(root: Path, conflicts: bool) -> Path:
    consensus = {
        "company_name": {"value": "Apple Inc.", "confidence": "high", "status": "consistent", "providers": ["fmp", "polygon"]},
        "latest_price": {"value": 280.14, "confidence": "high", "status": "consistent", "providers": ["fmp", "polygon"]},
        "market_cap": {"value": 4114378275000.0, "confidence": "high", "status": "consistent", "providers": ["fmp", "polygon"]},
        "pe_ratio": {"value": 33.6, "confidence": "high", "status": "consistent", "providers": ["fmp", "alpha_vantage"]},
        "currency": {"value": "USD", "confidence": "high", "status": "consistent", "providers": ["fmp", "polygon"]},
        "exchange": {"value": "NASDAQ", "confidence": "high", "status": "consistent", "providers": ["fmp", "polygon"]},
        "sector": {"value": "Technology", "confidence": "high", "status": "consistent", "providers": ["fmp", "alpha_vantage"]},
        "industry": {"value": "Consumer Electronics", "confidence": "high", "status": "consistent", "providers": ["fmp", "alpha_vantage"]},
    }
    packet = new_packet(
        provider="financial_compare",
        subject_type="company",
        subject_id="AAPL",
        time_window="latest_financial_packets",
        current_date=date(2026, 5, 4),
        sources=[
            Source(
                source_id="fmp_packet",
                provider="financial_compare",
                source_type="internal",
                title="FMP packet",
                artifact_path="agents/runs/2026-05-09_weekly/evidence_packets/fmp.json",
            )
        ],
        claims=[
            Claim(
                claim="Financial data comparison completed for AAPL.",
                evidence=json.dumps(consensus, sort_keys=True),
                source_ids=["fmp_packet"],
                confidence="high",
                impact="medium",
                novelty="new",
            )
        ],
        contradictions=[
            Contradiction(
                current_repo_claim="Provider values for market_cap are consistent.",
                new_evidence='{"fmp": 1, "polygon": 2}',
                source_ids=["fmp_packet"],
                suggested_action="Review conflict.",
            )
        ]
        if conflicts
        else [],
    )
    packet_path = root / "agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_financial_compare_company_aapl.json"
    return write_packet(packet, packet_path)


if __name__ == "__main__":
    unittest.main()
