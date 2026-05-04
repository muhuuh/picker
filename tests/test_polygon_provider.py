from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.polygon_provider import PolygonCompanyOptions, build_polygon_company_packet, extract_polygon_metrics


class PolygonProviderTests(unittest.TestCase):
    def test_extract_polygon_metrics_combines_details_and_previous_bar(self):
        metrics = extract_polygon_metrics(fake_snapshot())

        self.assertEqual(metrics["company_name"], "Apple Inc.")
        self.assertEqual(metrics["primary_exchange"], "XNAS")
        self.assertEqual(metrics["previous_close"], 200.0)
        self.assertEqual(metrics["previous_volume"], 123456)

    def test_build_polygon_company_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_polygon_company_packet(
                options=PolygonCompanyOptions(ticker="AAPL"),
                api_key="test",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=lambda options, api_key: fake_snapshot(),
            )

            self.assertEqual(packet.provider, "polygon")
            loaded = read_packet(paths[0])
            self.assertTrue(validate_packet(loaded).ok)
            self.assertIn("previous_close", loaded.claims[0].evidence)


def fake_snapshot():
    return {
        "ticker": "AAPL",
        "ticker_details": {
            "results": {
                "ticker": "AAPL",
                "name": "Apple Inc.",
                "primary_exchange": "XNAS",
                "currency_name": "usd",
                "market": "stocks",
                "locale": "us",
                "market_cap": 3000000000000,
            }
        },
        "previous_day_bar": {"results": [{"o": 198.0, "h": 201.0, "l": 197.5, "c": 200.0, "v": 123456, "vw": 199.8}]},
    }


if __name__ == "__main__":
    unittest.main()
