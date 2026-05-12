from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import json

from stock_research.weekly_digest import build_weekly_digest, format_weekly_digest_markdown


class WeeklyDigestTests(unittest.TestCase):
    def test_weekly_digest_includes_evidence_links_and_quality_passes(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_digest_repo(Path(temp_dir))
            write_opportunity_input(root, "AAPL")
            write_required_reports(root, "AAPL")

            digest = build_weekly_digest(root, "2026-05-16_weekly")
            markdown = format_weekly_digest_markdown(digest)

            self.assertEqual(digest.status, "ready")
            self.assertEqual(digest.quality_findings, [])
            self.assertIn("### Evidence Links", markdown)
            self.assertIn("financial_review", markdown)
            self.assertIn("Grok/X pulse", markdown)
            self.assertIn("X bull case", markdown)
            self.assertIn("- market_cap: $1.00M", markdown)
            self.assertIn("- profit_margin: 10.00%", markdown)
            self.assertIn("- pe_ratio: 30.00x", markdown)
            self.assertIn("- free_cash_flow_per_share_ttm: -$1.00", markdown)
            self.assertNotIn("Digest Quality Findings", markdown)

    def test_weekly_digest_flags_missing_evidence_links(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_digest_repo(Path(temp_dir))
            write_opportunity_input(root, "AAPL")
            write_required_reports(root, "AAPL", include_financial=False)

            digest = build_weekly_digest(root, "2026-05-16_weekly")

            self.assertEqual(digest.status, "needs_review")
            self.assertTrue(any("missing evidence links" in finding for finding in digest.quality_findings))

    def test_weekly_digest_flags_non_social_sentiment_label(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_digest_repo(Path(temp_dir))
            write_opportunity_input(root, "AAPL", social_sentiment="positive")
            write_required_reports(root, "AAPL")

            digest = build_weekly_digest(root, "2026-05-16_weekly")

            self.assertEqual(digest.status, "needs_review")
            self.assertTrue(any("social signal" in finding for finding in digest.quality_findings))

    def test_weekly_digest_flags_direct_trade_language(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_digest_repo(Path(temp_dir))
            write_opportunity_input(root, "AAPL", summary="AAPL assessment says buy the stock now, which should be blocked.")
            write_required_reports(root, "AAPL")

            digest = build_weekly_digest(root, "2026-05-16_weekly")

            self.assertEqual(digest.status, "needs_review")
            self.assertTrue(any("direct trade language" in finding for finding in digest.quality_findings))

    def test_weekly_digest_flags_status_only_social_output(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_digest_repo(Path(temp_dir))
            write_opportunity_input(root, "AAPL", include_social_narrative=False)
            write_required_reports(root, "AAPL")

            digest = build_weekly_digest(root, "2026-05-16_weekly")

            self.assertEqual(digest.status, "needs_review")
            self.assertTrue(any("Grok/X pulse" in finding for finding in digest.quality_findings))
            self.assertTrue(any("bullish or bearish claims" in finding for finding in digest.quality_findings))


def seed_digest_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir()
    (root / "agents").mkdir()
    (root / "agents/human_review_queue.md").write_text("# Human Review Queue\n", encoding="utf-8")
    return root


def write_opportunity_input(
    root: Path,
    ticker: str,
    *,
    social_sentiment: str = "positive_social_signal",
    summary: str | None = None,
    include_social_narrative: bool = True,
) -> None:
    run_dir = root / "agents/runs/2026-05-16_weekly/raw/opportunity_assessment"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ticker": ticker,
        "status": "ready_for_human_review",
        "opportunity_view": "interesting",
        "opportunity_score": 82,
        "risk_level": "medium",
        "confidence": "medium",
        "thesis_freshness": "fresh_recent_evidence",
        "summary": summary or f"{ticker} assessment is interesting with source-backed evidence and no trade instruction.",
        "positives": ["Revenue TTM is available."],
        "negatives": ["Providers disagree on industry taxonomy; treat this as a classification/watch item, not a numeric conflict."],
        "watch_items": ["Pick the preferred industry taxonomy label for the company file."],
        "financial_snapshot": {
            "status": "partial_review",
            "latest_price": 100.0,
            "market_cap": 1000000.0,
            "pe_ratio": 30.0,
            "price_to_sales_ttm": 3.0,
            "profit_margin": 0.1,
            "free_cash_flow_per_share_ttm": -1.0,
            "currency": "USD",
            "conflict_count": 1,
        },
        "news_snapshot": {
            "status": "ready_for_company_update",
            "source_count": 3,
            "contents_claim_count": 3,
            "material_developments": [{"claim": "AWS demand accelerated and operating margins expanded.", "source_ids": ["exa_result_1"]}],
        },
        "social_snapshot": {
            "status": "available",
            "sentiment": social_sentiment,
            "citation_count": 2,
            "rumor_flag": False,
        },
        "filing_snapshot": {"status": "available", "packet_count": 1, "unknown_count": 0},
        "recommended_next_action": "Use this as a reviewable holding update and inspect watch items before changing the thesis.",
    }
    if include_social_narrative:
        payload["social_snapshot"].update(
            {
                "x_pulse": "X discussion is constructive because investors focus on AWS acceleration and margin expansion.",
                "bullish_claims": ["AWS and AI demand are the main upside narrative."],
                "bearish_claims": ["Valuation remains the main pushback."],
            }
        )
    (run_dir / f"{ticker}_opportunity_assessment.json").write_text(json.dumps(payload), encoding="utf-8")


def write_required_reports(root: Path, ticker: str, *, include_financial: bool = True) -> None:
    run_dir = root / "agents/runs/2026-05-16_weekly"
    paths = [
        run_dir / "reports/opportunity_assessment" / f"{ticker}_opportunity_assessment.md",
        run_dir / "reports/company_news_specialist" / f"{ticker}_company_news_review.md",
        run_dir / "company_research" / f"{ticker}_company_research.md",
    ]
    if include_financial:
        paths.append(run_dir / "reports/financial_data_specialist" / f"{ticker}_financial_review.md")
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {ticker}\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
