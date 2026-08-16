from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from stock_research.evidence import read_packet, validate_packet
from stock_research.providers.xai_grok import (
    XAI_MODELS_URL,
    XAI_RESPONSES_URL,
    XaiGrokError,
    XaiModelCatalog,
    XaiXSearchOptions,
    build_xai_x_search_packet,
    build_xai_x_search_payload,
    company_deep_dive_prompt,
    parse_xai_model_catalog,
    resolve_available_xai_search_model,
    resolve_xai_search_model,
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

        self.assertEqual(payload["model"], "grok-4.6")
        self.assertEqual(payload["reasoning"], {"effort": "high"})
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

    def test_payload_supports_web_search_with_domain_filters(self):
        payload = build_xai_x_search_payload(
            XaiXSearchOptions(
                prompt=company_deep_dive_prompt("AMBA", "Ambarella"),
                subject_type="company",
                subject_id="AMBA",
                research_kind="company_deep_dive",
                tool_type="web_search",
                allowed_domains=("ambarella.com", "sec.gov"),
            )
        )

        self.assertEqual(payload["tools"][0]["type"], "web_search")
        self.assertEqual(payload["tools"][0]["filters"]["allowed_domains"], ["ambarella.com", "sec.gov"])
        self.assertIn("Business & Technology Overview", payload["input"][0]["content"])

    def test_model_catalog_resolution_prefers_requested_grok_46(self):
        catalog = parse_xai_model_catalog(
            {
                "data": [
                    {"id": "grok-4.6", "aliases": ["grok-4.6-latest"]},
                    {"id": "grok-4.5", "aliases": []},
                ]
            }
        )

        resolution = resolve_xai_search_model("grok-4.6", catalog)

        self.assertEqual(resolution.resolved_model, "grok-4.6")
        self.assertEqual(resolution.source, "authenticated_model_catalog")
        self.assertEqual(resolution.fallback_reason, "")

    def test_model_catalog_resolution_records_fallback_reason(self):
        catalog = XaiModelCatalog(model_ids=("grok-4.5",), aliases=("grok-4.5-latest",))

        resolution = resolve_xai_search_model("grok-4.6", catalog)

        self.assertEqual(resolution.resolved_model, "grok-4.5")
        self.assertIn("not available", resolution.fallback_reason)

    def test_model_catalog_resolution_fails_without_approved_search_fallback(self):
        catalog = XaiModelCatalog(model_ids=("grok-code-fast-1",), aliases=())

        with self.assertRaisesRegex(XaiGrokError, "no approved X-search fallback"):
            resolve_xai_search_model("grok-4.6", catalog)

    def test_model_catalog_rejects_invalid_or_empty_response(self):
        with self.assertRaisesRegex(XaiGrokError, "valid data list"):
            parse_xai_model_catalog({"data": {}})
        with self.assertRaisesRegex(XaiGrokError, "did not expose any model names"):
            parse_xai_model_catalog({"data": []})

    def test_authenticated_model_resolution_uses_models_endpoint(self):
        def fake_model_fetcher(url: str, api_key: str):
            self.assertEqual(url, XAI_MODELS_URL)
            self.assertEqual(api_key, "test-key")
            return {"data": [{"id": "grok-4.6", "aliases": []}]}

        resolution, catalog = resolve_available_xai_search_model(
            "grok-4.6",
            "test-key",
            fetcher=fake_model_fetcher,
        )

        self.assertEqual(resolution.resolved_model, "grok-4.6")
        self.assertEqual(catalog.model_ids, ("grok-4.6",))

    def test_build_packet_writes_valid_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            packet, paths = build_xai_x_search_packet(
                options=XaiXSearchOptions(
                    prompt=stock_sentiment_prompt("AMD", "Advanced Micro Devices"),
                    subject_type="company",
                    subject_id="AMD",
                    research_kind="stock_sentiment",
                    requested_model="grok-4.6",
                    model_resolution_source="authenticated_model_catalog",
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
            raw_payload = json.loads(paths[1].read_text(encoding="utf-8"))
            self.assertEqual(raw_payload["model_provenance"]["requested_model"], "grok-4.6")
            self.assertEqual(raw_payload["model_provenance"]["resolved_model"], "grok-4.6")
            self.assertEqual(raw_payload["model_provenance"]["tool_type"], "x_search")
            self.assertEqual(raw_payload["model_provenance"]["reasoning_effort"], "high")

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

    def test_recorded_grok46_response_preserves_required_sections_and_full_evidence(self):
        fixture_path = Path(__file__).parent / "fixtures" / "xai" / "grok46_x_search_recorded.json"
        response = json.loads(fixture_path.read_text(encoding="utf-8"))

        with TemporaryDirectory() as temp_dir:
            packet, _paths = build_xai_x_search_packet(
                options=XaiXSearchOptions(
                    prompt=stock_sentiment_prompt("GOOGL", "Alphabet"),
                    subject_type="company",
                    subject_id="GOOGL",
                    research_kind="stock_sentiment",
                    requested_model="grok-4.6",
                    model_resolution_source="authenticated_model_catalog",
                ),
                api_key="test-key",
                run_id="2026-08-16_recorded",
                root=Path(temp_dir),
                current_date=date(2026, 8, 16),
                fetcher=lambda _url, _key, _payload: response,
            )

        evidence = packet.claims[0].evidence
        for section in (
            "Executive X pulse",
            "Trend evolution",
            "Recurring bullish arguments",
            "Recurring bearish or skeptical arguments",
            "Notable accounts/posts worth reviewing",
            "Investor implications and scorecard",
        ):
            self.assertIn(section, evidence)
        self.assertEqual(len(packet.sources), 2)
        self.assertTrue(all(source.url.startswith("https://x.com/") for source in packet.sources))
        self.assertEqual(packet.claims[0].full_evidence_selector, "response.output")

    def test_long_grok_response_is_not_truncated_in_canonical_claim(self):
        long_text = "A complete opening sentence explains the material change. " + (
            "A complete supporting sentence preserves account, narrative, catalyst, risk, and verification detail. " * 70
        )
        response = {
            "id": "resp_long",
            "citations": ["https://x.com/i/status/1"],
            "output": [{"type": "message", "content": [{"type": "output_text", "text": long_text, "annotations": []}]}],
        }

        with TemporaryDirectory() as temp_dir:
            packet, _paths = build_xai_x_search_packet(
                options=XaiXSearchOptions(prompt="test", subject_type="company", subject_id="TEST"),
                api_key="test-key",
                run_id="2026-08-16_long",
                root=Path(temp_dir),
                current_date=date(2026, 8, 16),
                fetcher=lambda _url, _key, _payload: response,
            )

        claim = packet.claims[0]
        self.assertGreater(len(claim.evidence), 4000)
        self.assertEqual(claim.evidence, long_text)
        self.assertLess(len(claim.display_excerpt), len(claim.evidence))
        self.assertNotIn("...", claim.display_excerpt)


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
