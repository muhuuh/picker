from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import Claim, Source, new_packet, read_packet, validate_packet, write_packet
from stock_research.financial_compare import build_financial_compare_packet, compare_observations


class FinancialCompareTests(unittest.TestCase):
    def test_build_financial_compare_packet_writes_valid_consensus_packet(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_id = "2026-05-09_weekly"
            write_input_packet(root, run_id, "fmp", {"price": 100.0, "market_cap": 1000, "pe_ratio_ttm": 20.0, "currency": "USD"})
            write_input_packet(root, run_id, "alpha_vantage", {"latest_price": "100.5", "market_cap": "1010", "pe_ratio": "20.4", "currency": "USD"})
            write_input_packet(root, run_id, "polygon", {"previous_close": 100.2, "market_cap": 1005, "currency": "usd", "primary_exchange": "XNAS"})
            write_input_packet(root, run_id, "exa", {"price": 1.0})

            packet, paths = build_financial_compare_packet(
                ticker="AAPL",
                run_id=run_id,
                root=root,
                current_date=date(2026, 5, 4),
            )

            self.assertEqual(packet.provider, "financial_compare")
            self.assertEqual(packet.subject_id, "AAPL")
            self.assertEqual(len(paths), 2)
            loaded = read_packet(paths[0])
            self.assertTrue(validate_packet(loaded).ok)
            self.assertEqual(len(loaded.sources), 3)
            evidence = json.loads(loaded.claims[0].evidence)
            self.assertEqual(evidence["latest_price"]["status"], "consistent")
            self.assertEqual(evidence["market_cap"]["status"], "consistent")

    def test_compare_observations_flags_material_numeric_conflicts(self):
        from stock_research.financial_compare import FinancialObservation

        comparison = compare_observations(
            [
                FinancialObservation("market_cap", "fmp", 1000, "fmp_packet"),
                FinancialObservation("market_cap", "alpha_vantage", 1500, "alpha_vantage_packet"),
            ]
        )

        self.assertEqual(comparison["consensus"]["market_cap"]["status"], "conflict")
        self.assertEqual(comparison["conflicts"][0]["metric"], "market_cap")


def write_input_packet(root: Path, run_id: str, provider: str, metrics: dict):
    packet = new_packet(
        provider=provider,
        subject_type="company",
        subject_id="AAPL",
        current_date=date(2026, 5, 4),
        sources=[
            Source(
                source_id=f"{provider}_source",
                provider=provider,
                source_type="market_data" if provider != "exa" else "news",
                artifact_path=f"raw/{provider}.json",
            )
        ],
        claims=[
            Claim(
                claim=f"{provider} snapshot",
                evidence=json.dumps(metrics),
                source_ids=[f"{provider}_source"],
                confidence="medium",
                impact="medium",
            )
        ],
    )
    path = root / "agents" / "runs" / run_id / "evidence_packets" / f"{provider}.json"
    write_packet(packet, path)
    return path


if __name__ == "__main__":
    unittest.main()
