from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.alpha_vantage import (
    AlphaVantageCompanyOptions,
    AlphaVantageError,
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

    def test_rate_limit_unavailable_writes_coverage_gap_packet(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_alpha_vantage_company_packet(
                options=AlphaVantageCompanyOptions(ticker="MU"),
                api_key="test",
                run_id="2026-05-16_weekly",
                root=root,
                current_date=date(2026, 5, 16),
                fetcher=lambda options, api_key: (_ for _ in ()).throw(
                    AlphaVantageError("standard API rate limit is 25 requests per day")
                ),
            )

            self.assertEqual(packet.provider, "alpha_vantage")
            self.assertEqual(packet.time_window, "rate_limit_unavailable")
            self.assertEqual(len(paths), 2)
            self.assertTrue(validate_packet(packet).ok)
            self.assertIn("rate_limit_unavailable", packet.claims[0].evidence)

    def test_fallback_key_is_used_after_rate_limit_unavailable(self):
        calls = []

        def fetcher(options, api_key):
            calls.append(api_key)
            if api_key == "primary":
                raise AlphaVantageError("standard API rate limit is 25 requests per day")
            return fake_snapshot()

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_alpha_vantage_company_packet(
                options=AlphaVantageCompanyOptions(ticker="MU"),
                api_key="primary",
                fallback_api_key="secondary",
                run_id="2026-05-16_weekly",
                root=root,
                current_date=date(2026, 5, 16),
                fetcher=fetcher,
            )

            raw_snapshot = json.loads(paths[1].read_text(encoding="utf-8"))
            self.assertEqual(calls, ["primary", "secondary"])
            self.assertEqual(packet.time_window, "quote_overview_snapshot")
            self.assertEqual(raw_snapshot["credential"]["api_key_label"], "secondary")
            self.assertTrue(raw_snapshot["credential"]["fallback_used"])
            self.assertEqual(raw_snapshot["credential"]["prior_attempts"][0]["api_key_label"], "primary")

    def test_fallback_key_failure_writes_attempt_labels_without_secrets(self):
        def fetcher(options, api_key):
            raise AlphaVantageError(f"standard API rate limit reached for {api_key}")

        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_alpha_vantage_company_packet(
                options=AlphaVantageCompanyOptions(ticker="MU"),
                api_key="primary-secret",
                fallback_api_key="secondary-secret",
                run_id="2026-05-16_weekly",
                root=root,
                current_date=date(2026, 5, 16),
                fetcher=fetcher,
            )

            raw_text = paths[1].read_text(encoding="utf-8")
            self.assertNotIn("primary-secret", raw_text)
            self.assertNotIn("secondary-secret", raw_text)
            self.assertEqual(packet.time_window, "rate_limit_unavailable")
            self.assertIn('"attempt_labels": ["primary", "secondary"]', packet.claims[0].evidence)


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
