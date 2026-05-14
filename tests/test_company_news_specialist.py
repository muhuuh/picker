from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.company_news_specialist import build_company_news_contents_follow_up_packet, build_company_news_specialist_packet
from stock_research.evidence import Claim, Source, new_packet, validate_packet, write_packet


class CompanyNewsSpecialistTests(unittest.TestCase):
    def test_company_news_review_writes_packet_raw_and_report(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            packet_path = write_exa_news_packet(root, with_sources=True)

            result = build_company_news_specialist_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 4),
                exa_news_packet_path=packet_path,
            )

            self.assertEqual(result.packet.provider, "company_news_specialist")
            self.assertEqual(result.review["status"], "partial_review")
            self.assertIn("contents extraction", result.review["status_reason"])
            self.assertEqual(validate_packet(result.packet).errors, [])
            self.assertEqual(len(result.paths), 3)
            for path in result.paths:
                self.assertTrue(path.exists())
            self.assertIn("Company News Review", result.paths[2].read_text(encoding="utf-8"))

    def test_company_news_review_is_ready_after_contents_follow_up(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            packet_path = write_exa_news_packet(root, with_sources=True)

            follow_up = build_company_news_contents_follow_up_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                api_key="test-key",
                current_date=date(2026, 5, 4),
                exa_news_packet_path=packet_path,
                fetcher=fake_exa_contents_fetcher,
            )
            result = build_company_news_specialist_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 4),
                exa_news_packet_path=packet_path,
            )

            self.assertEqual(follow_up.urls, ["https://example.com/apple-supplier-update"])
            self.assertEqual(result.review["status"], "ready_for_company_update")
            self.assertEqual(result.review["contents_source_count"], 1)
            self.assertEqual(validate_packet(result.packet).errors, [])
            source_ids = {source.source_id for source in result.packet.sources}
            self.assertIn("exa_result_1", source_ids)
            self.assertNotIn("exa_news_packet", source_ids)
            self.assertNotIn("company_news_specialist_report", source_ids)
            update_source_ids = result.packet.recommended_updates[0].source_ids
            self.assertIn("exa_result_1", update_source_ids)
            self.assertNotIn("exa_news_packet", update_source_ids)

    def test_company_news_review_is_partial_when_exa_has_no_sources(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))
            packet_path = write_exa_news_packet(root, with_sources=False)

            result = build_company_news_specialist_packet(
                ticker="AAPL",
                run_id="2026-05-09_weekly",
                root=root,
                current_date=date(2026, 5, 4),
                exa_news_packet_path=packet_path,
            )

            self.assertEqual(result.review["status"], "partial_review")
            self.assertTrue(result.packet.risks)
            self.assertEqual(validate_packet(result.packet).errors, [])


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly/evidence_packets").mkdir(parents=True)
    return root


def write_exa_news_packet(root: Path, with_sources: bool) -> Path:
    sources = [
        Source(
            source_id="exa_result_1",
            provider="exa",
            source_type="news",
            title="Apple announces supplier update",
            url="https://example.com/apple-supplier-update",
            publisher="example.com",
            published_at="2026-05-03T00:00:00.000Z",
            artifact_path="agents/runs/2026-05-09_weekly/raw/exa/exa_news_company_aapl.json",
        )
    ] if with_sources else []
    claims = [
        Claim(
            claim="Exa news search returned 1 result(s) for AAPL.",
            evidence=json.dumps({"requestId": "req"}),
            source_ids=[source.source_id for source in sources],
            confidence="medium" if sources else "low",
            impact="medium",
        )
    ]
    if sources:
        claims.append(
            Claim(
                claim="Relevant Exa result: Apple announces supplier update",
                evidence="Apple announced a supplier update relevant to investors.",
                source_ids=["exa_result_1"],
                confidence="medium",
                impact="medium",
            )
        )
    packet = new_packet(
        provider="exa",
        subject_type="company",
        subject_id="AAPL",
        time_window="current_news",
        current_date=date(2026, 5, 4),
        sources=sources,
        claims=claims,
    )
    packet_path = root / "agents/runs/2026-05-09_weekly/evidence_packets/2026-05-04_exa_company_aapl_exa_news_company_aapl.json"
    return write_packet(packet, packet_path)


def fake_exa_contents_fetcher(url: str, api_key: str, payload: dict) -> dict:
    return {
        "requestId": "contents-req",
        "results": [
            {
                "title": "Apple announces supplier update",
                "url": payload["urls"][0],
                "publishedDate": "2026-05-03T00:00:00.000Z",
                "highlights": ["Apple announced supplier updates with investor relevance."],
                "text": "Apple announced supplier updates with investor relevance.",
            }
        ],
        "statuses": [{"id": payload["urls"][0], "status": "success"}],
        "costDollars": {"total": 0.001},
    }


if __name__ == "__main__":
    unittest.main()
