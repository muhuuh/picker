from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.alpha_vantage import (
    AlphaVantageCompanyOptions,
    build_alpha_vantage_company_packet,
    extract_alpha_vantage_metrics,
)


class AlphaVantageProviderTests(unittest.TestCase):
    def test_extract_alpha_vantage_metrics_combines_quote_and_overview(self):
        metrics = extract_alpha_vantage_metrics(fake_snapshot())

        self.assertEqual(metrics["company_name"], "Apple Inc")
        self.assertEqual(metrics["latest_price"], "200.0000")
        self.assertEqual(metrics["pe_ratio"], "31.2")
        self.assertEqual(metrics["volume"], "123456")

    def test_build_alpha_vantage_company_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_alpha_vantage_company_packet(
                options=AlphaVantageCompanyOptions(ticker="AAPL"),
                api_key="test",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=lambda options, api_key: fake_snapshot(),
            )

            self.assertEqual(packet.provider, "alpha_vantage")
            loaded = read_packet(paths[0])
            self.assertTrue(validate_packet(loaded).ok)
            self.assertIn("latest_price", loaded.claims[0].evidence)


def fake_snapshot():
    return {
        "ticker": "AAPL",
        "global_quote": {
            "Global Quote": {
                "05. price": "200.0000",
                "06. volume": "123456",
                "07. latest trading day": "2026-05-01",
                "08. previous close": "198.0000",
            }
        },
        "overview": {
            "Name": "Apple Inc",
            "Exchange": "NASDAQ",
            "Currency": "USD",
            "Sector": "Technology",
            "Industry": "Consumer Electronics",
            "Country": "USA",
            "MarketCapitalization": "3000000000000",
            "PERatio": "31.2",
        },
    }


if __name__ == "__main__":
    unittest.main()
