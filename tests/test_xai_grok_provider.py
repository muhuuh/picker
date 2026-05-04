from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.xai_grok import (
    XAI_RESPONSES_URL,
    XaiGrokError,
    XaiXSearchOptions,
    build_xai_x_search_packet,
    build_xai_x_search_payload,
    stock_sentiment_prompt,
)


class XaiGrokProviderTests(unittest.TestCase):
    def test_payload_uses_x_search_tool_with_date_and_handles(self):
        payload = build_xai_x_search_payload(
            XaiXSearchOptions(
                prompt="What are people saying about AMD?",
                subject_type="company",
                subject_id="AMD",
                from_date="2026-05-01",
                to_date="2026-05-03",
                allowed_x_handles=("amd",),
            )
        )

        self.assertEqual(payload["model"], "grok-4.3")
        self.assertEqual(payload["tools"][0]["type"], "x_search")
        self.assertEqual(payload["tools"][0]["from_date"], "2026-05-01")
        self.assertEqual(payload["tools"][0]["allowed_x_handles"], ["amd"])

    def test_payload_rejects_allowed_and_excluded_handles_together(self):
        with self.assertRaises(XaiGrokError):
            build_xai_x_search_payload(
                XaiXSearchOptions(
                    prompt="test",
                    subject_type="company",
                    subject_id="AMD",
                    allowed_x_handles=("amd",),
                    excluded_x_handles=("intel",),
                )
            )

    def test_build_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_xai_x_search_packet(
                options=XaiXSearchOptions(
                    prompt=stock_sentiment_prompt("AMD", "Advanced Micro Devices"),
                    subject_type="company",
                    subject_id="AMD",
                    research_kind="stock_sentiment",
                ),
                api_key="test-key",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=fake_fetch_json,
            )

            self.assertEqual(packet.provider, "xai_grok")
            self.assertEqual(packet.subject_id, "AMD")
            self.assertEqual(packet.sources[0].source_type, "social")
            self.assertEqual(len(paths), 2)
            self.assertTrue(validate_packet(read_packet(paths[0])).ok)
            self.assertIn("x_search_stock_sentiment", packet.packet_id)

    def test_x_search_packets_for_same_subject_use_distinct_artifact_ids(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            first_packet, first_paths = build_xai_x_search_packet(
                options=XaiXSearchOptions(
                    prompt="Search X for stock sentiment about AMD.",
                    subject_type="company",
                    subject_id="AMD",
                    research_kind="stock_sentiment",
                    artifact_id="xai_x_search_company_amd",
                ),
                api_key="test-key",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=fake_fetch_json,
            )
            second_packet, second_paths = build_xai_x_search_packet(
                options=XaiXSearchOptions(
                    prompt="Search X for latest news about AMD.",
                    subject_type="company",
                    subject_id="AMD",
                    research_kind="latest_news",
                    artifact_id="xai_x_news_company_amd",
                ),
                api_key="test-key",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 3),
                fetcher=fake_fetch_json,
            )

            self.assertNotEqual(first_packet.packet_id, second_packet.packet_id)
            self.assertNotEqual(first_paths[0], second_paths[0])
            self.assertNotEqual(first_paths[1], second_paths[1])


def fake_fetch_json(url: str, api_key: str, payload: dict):
    if url == XAI_RESPONSES_URL:
        return {
            "id": "resp_1",
            "citations": ["https://x.com/investor/status/123"],
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Sentiment is mixed, with investors debating AI accelerator demand. [[1]](https://x.com/investor/status/123)",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url": "https://x.com/investor/status/123",
                                    "title": "1",
                                    "start_index": 74,
                                    "end_index": 112,
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    raise AssertionError(f"Unexpected URL: {url}")


if __name__ == "__main__":
    unittest.main()
