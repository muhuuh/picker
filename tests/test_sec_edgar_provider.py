from datetime import date
import gzip
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.sec_edgar import (
    SEC_COMPANY_FACTS_URL,
    SEC_COMPANY_TICKERS_URL,
    SEC_SUBMISSIONS_URL,
    SecEdgarError,
    build_sec_company_packet,
    decode_response_body,
    filing_url,
    resolve_sec_user_agent,
    resolve_ticker,
)


class SecEdgarProviderTests(unittest.TestCase):
    def test_resolve_ticker_uses_sec_mapping(self):
        company = resolve_ticker("AAPL", "test ua", fake_fetch_json)

        self.assertEqual(company.cik, "0000320193")
        self.assertEqual(company.name, "Apple Inc.")
        self.assertEqual(company.exchange, "Nasdaq")

    def test_build_sec_company_packet_writes_packet_and_raw(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_sec_company_packet(
                ticker="AAPL",
                user_agent="test ua",
                run_id="2026-05-09_weekly",
                root=root,
                include_facts=True,
                current_date=date(2026, 5, 3),
                fetcher=fake_fetch_json,
            )

            self.assertEqual(packet.provider, "sec_edgar")
            self.assertEqual(packet.subject_id, "AAPL")
            self.assertEqual(len(paths), 3)
            self.assertTrue(paths[0].exists())
            loaded = read_packet(paths[0])
            report = validate_packet(loaded)
            self.assertTrue(report.ok, report.errors)
            self.assertIn("10-K filed 2025-11-01", loaded.claims[1].claim)

    def test_filing_url_builds_archive_url(self):
        url = filing_url("0000320193-25-000001", "aapl-20250927.htm")

        self.assertEqual(
            url,
            "https://www.sec.gov/Archives/edgar/data/320193/000032019325000001/aapl-20250927.htm",
        )

    def test_decode_response_body_handles_gzip(self):
        body = b'{"ok": true}'
        compressed = gzip.compress(body)

        self.assertEqual(decode_response_body(compressed, "gzip"), body)
        self.assertEqual(decode_response_body(compressed, ""), body)

    def test_user_agent_is_required(self):
        with self.assertRaises(SecEdgarError):
            resolve_sec_user_agent("")


def fake_fetch_json(url: str, user_agent: str):
    if url == SEC_COMPANY_TICKERS_URL:
        return {
            "fields": ["cik", "name", "ticker", "exchange"],
            "data": [[320193, "Apple Inc.", "AAPL", "Nasdaq"]],
        }
    if url == SEC_SUBMISSIONS_URL.format(cik="0000320193"):
        return {
            "name": "Apple Inc.",
            "filings": {
                "recent": {
                    "form": ["10-K", "8-K"],
                    "filingDate": ["2025-11-01", "2025-10-15"],
                    "reportDate": ["2025-09-27", "2025-10-14"],
                    "accessionNumber": ["0000320193-25-000001", "0000320193-25-000002"],
                    "primaryDocument": ["aapl-20250927.htm", "aapl-8k.htm"],
                }
            },
        }
    if url == SEC_COMPANY_FACTS_URL.format(cik="0000320193"):
        return {"facts": {"us-gaap": {}, "dei": {}}}
    raise AssertionError(f"Unexpected URL: {url}")


if __name__ == "__main__":
    unittest.main()
