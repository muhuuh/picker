from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.exa import (
    EXA_CONTENTS_URL,
    EXA_SEARCH_URL,
    ExaError,
    ExaContentsOptions,
    ExaSearchOptions,
    build_exa_contents_packet,
    build_exa_contents_payload,
    build_exa_search_packet,
    build_exa_search_payload,
)


class ExaProviderTests(unittest.TestCase):
    def test_company_search_payload_uses_company_category_and_highlights(self):
        payload = build_exa_search_payload(
            ExaSearchOptions(
                query="German robotics companies",
                subject_type="industry",
                subject_id="robotics",
                search_mode="company",
            )
        )

        self.assertEqual(payload["category"], "company")
        self.assertEqual(payload["contents"], {"highlights": True})

    def test_company_search_rejects_unsupported_filters(self):
        with self.assertRaises(ExaError):
            build_exa_search_payload(
                ExaSearchOptions(
                    query="German robotics companies",
                    subject_type="industry",
                    subject_id="robotics",
                    search_mode="company",
                    start_published_date="2026-01-01",
                )
            )

    def test_contents_payload_keeps_content_options_top_level(self):
        payload = build_exa_contents_payload(
            ExaContentsOptions(
                urls=("https://example.com/article",),
                subject_type="company",
                subject_id="EXAMPLE",
                highlights_query="investment relevance",
                text_max_characters=5000,
                max_age_hours=24,
            )
        )

        self.assertNotIn("contents", payload)
        self.assertEqual(payload["highlights"], {"query": "investment relevance"})
        self.assertEqual(payload["text"], {"maxCharacters": 5000})
        self.assertEqual(payload["maxAgeHours"], 24)

    def test_build_search_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_exa_search_packet(
                options=ExaSearchOptions(
                    query="AI regulation updates in Europe",
                    subject_type="theme",
                    subject_id="ai_regulation",
                    search_mode="news",
                    num_results=2,
                ),
                api_key="test-key",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=fake_fetch_json,
            )

            self.assertEqual(packet.provider, "exa")
            self.assertEqual(packet.subject_id, "ai_regulation")
            self.assertEqual(len(paths), 2)
            loaded = read_packet(paths[0])
            self.assertTrue(validate_packet(loaded).ok)
            self.assertEqual(loaded.sources[0].source_type, "news")

    def test_build_contents_packet_records_status_errors_as_unknowns(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_exa_contents_packet(
                options=ExaContentsOptions(
                    urls=("https://example.com/article", "https://example.com/missing"),
                    subject_type="company",
                    subject_id="EXAMPLE",
                ),
                api_key="test-key",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=fake_fetch_json,
            )

            self.assertEqual(packet.provider, "exa")
            self.assertEqual(len(paths), 2)
            self.assertIn("CRAWL_NOT_FOUND", "\n".join(packet.unknowns))
            self.assertTrue(validate_packet(read_packet(paths[0])).ok)


def fake_fetch_json(url: str, api_key: str, payload: dict):
    if url == EXA_SEARCH_URL:
        return {
            "requestId": "req_search",
            "searchType": payload["type"],
            "results": [
                {
                    "title": "EU AI regulation update",
                    "url": "https://example.com/eu-ai",
                    "publishedDate": "2026-05-01T00:00:00.000Z",
                    "author": "Reporter",
                    "highlights": ["European regulators advanced an AI compliance proposal."],
                }
            ],
            "costDollars": {"total": 0.001},
        }
    if url == EXA_CONTENTS_URL:
        return {
            "requestId": "req_contents",
            "results": [
                {
                    "title": "Example article",
                    "url": "https://example.com/article",
                    "highlights": ["The article describes a market development."],
                }
            ],
            "statuses": [
                {"id": "https://example.com/article", "status": "success"},
                {
                    "id": "https://example.com/missing",
                    "status": "error",
                    "error": {"tag": "CRAWL_NOT_FOUND", "httpStatusCode": 404},
                },
            ],
            "costDollars": {"total": 0.002},
        }
    raise AssertionError(f"Unexpected URL: {url}")


if __name__ == "__main__":
    unittest.main()
