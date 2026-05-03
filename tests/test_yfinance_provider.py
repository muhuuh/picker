from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.yfinance_provider import build_yfinance_company_packet, extract_metrics


class YFinanceProviderTests(unittest.TestCase):
    def test_extract_metrics_prefers_fast_info_for_market_data(self):
        metrics = extract_metrics(
            {"currency": "USD", "lastPrice": 123.45, "marketCap": 1000},
            {"trailingPE": 20.5, "sector": "Technology", "industry": "Consumer Electronics"},
        )

        self.assertEqual(metrics["currency"], "USD")
        self.assertEqual(metrics["last_price"], 123.45)
        self.assertEqual(metrics["pe_ratio"], 20.5)
        self.assertEqual(metrics["sector"], "Technology")

    def test_build_yfinance_company_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_yfinance_company_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                period="5d",
                fetcher=fake_fetch_snapshot,
            )

            self.assertEqual(packet.provider, "yfinance")
            self.assertEqual(packet.subject_id, "AAPL")
            self.assertEqual(len(paths), 2)
            self.assertTrue(paths[0].exists())
            self.assertTrue(paths[1].exists())
            loaded = read_packet(paths[0])
            self.assertTrue(validate_packet(loaded).ok)
            self.assertIn("last_price", loaded.claims[0].evidence)


def fake_fetch_snapshot(ticker: str, period: str):
    return {
        "ticker": ticker,
        "fast_info": {
            "currency": "USD",
            "lastPrice": 123.45,
            "previousClose": 122.0,
            "marketCap": 1000000000,
            "yearLow": 90.0,
            "yearHigh": 150.0,
        },
        "info": {
            "trailingPE": 25.1,
            "exchange": "NMS",
            "sector": "Technology",
            "industry": "Consumer Electronics",
        },
        "history": {
            "2026-05-01": {"Close": 123.45, "Volume": 1000},
            "2026-05-02": {"Close": 124.0, "Volume": 1100},
        },
    }


if __name__ == "__main__":
    unittest.main()
