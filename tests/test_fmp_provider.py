from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.fmp import FmpCompanyOptions, FmpError, build_fmp_company_packet, extract_fmp_metrics


class FmpProviderTests(unittest.TestCase):
    def test_extract_fmp_metrics_combines_quote_profile_and_ratios(self):
        metrics = extract_fmp_metrics(fake_snapshot())

        self.assertEqual(metrics["company_name"], "Apple Inc.")
        self.assertEqual(metrics["price"], 200.0)
        self.assertEqual(metrics["pe_ratio_ttm"], 30.5)
        self.assertEqual(metrics["free_cash_flow_per_share_ttm"], 6.7)

    def test_build_fmp_company_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_fmp_company_packet(
                options=FmpCompanyOptions(ticker="AAPL"),
                api_key="test",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=lambda options, api_key: fake_snapshot(),
            )

            self.assertEqual(packet.provider, "fmp")
            self.assertEqual(packet.subject_id, "AAPL")
            self.assertEqual(len(paths), 2)
            loaded = read_packet(paths[0])
            self.assertTrue(validate_packet(loaded).ok)
            self.assertIn("pe_ratio_ttm", loaded.claims[0].evidence)

    def test_subscription_unavailable_writes_coverage_gap_packet(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_fmp_company_packet(
                options=FmpCompanyOptions(ticker="AXTI"),
                api_key="test",
                run_id="2026-05-16_weekly",
                root=root,
                current_date=date(2026, 5, 16),
                fetcher=lambda options, api_key: (_ for _ in ()).throw(
                    FmpError("FMP request failed with HTTP 402: Premium Query Parameter")
                ),
            )

            self.assertEqual(packet.provider, "fmp")
            self.assertEqual(packet.time_window, "subscription_unavailable")
            self.assertEqual(len(paths), 2)
            self.assertTrue(validate_packet(packet).ok)
            self.assertIn("subscription_unavailable", packet.claims[0].evidence)


def fake_snapshot():
    return {
        "ticker": "AAPL",
        "quote": [{"symbol": "AAPL", "name": "Apple Inc.", "price": 200.0, "marketCap": 3000000000000}],
        "profile": [{"companyName": "Apple Inc.", "currency": "USD", "exchangeShortName": "NASDAQ", "sector": "Technology"}],
        "key_metrics_ttm": [{"freeCashFlowPerShareTTM": 6.7, "enterpriseValueOverEBITDATTM": 24.1}],
        "ratios_ttm": [{"priceToEarningsRatioTTM": 30.5, "debtToEquityRatioTTM": 1.4}],
    }


if __name__ == "__main__":
    unittest.main()
