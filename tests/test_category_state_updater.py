from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.category_state_updater import update_category_state_files


class CategoryStateUpdaterTests(unittest.TestCase):
    def test_updates_category_state_files_and_is_idempotent(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_repo(Path(temp_dir))

            dry_run = update_category_state_files(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
            )
            result = update_category_state_files(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
                write=True,
            )
            second = update_category_state_files(
                root=root,
                run_id="2026-05-16_weekly",
                current_date=date(2026, 5, 16),
                write=True,
            )

            self.assertEqual(dry_run.status, "ready_to_update")
            self.assertEqual(result.status, "complete")
            self.assertTrue(all(item.status == "already_applied" for item in second.items))
            holdings = (root / "stock_tracking/current_holdings/current_holdings_state.md").read_text(encoding="utf-8")
            rejected = (root / "stock_tracking/rejected/rejected_state.md").read_text(encoding="utf-8")
            self.assertIn("## Automated State Updates", holdings)
            self.assertIn("1 current holding(s): AMZN", holdings)
            self.assertIn("1 rejected stock(s): 1 still in cooldown", rejected)


def seed_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking/current_holdings").mkdir(parents=True)
    (root / "stock_tracking/monitoring").mkdir(parents=True)
    (root / "stock_tracking/rejected").mkdir(parents=True)
    (root / "agents/runs/2026-05-16_weekly").mkdir(parents=True)
    write_csv(
        root / "stock_tracking/current_holdings/current_holdings.csv",
        ["AMZN,Amazon.com Inc.,NASDAQ,US,Technology,Internet,current_holding,stock_tracking/stock_info_files/current_holdings/AMZN.md,,,"],
    )
    write_csv(
        root / "stock_tracking/monitoring/monitoring.csv",
        ["AAPL,Apple Inc.,NASDAQ,US,Technology,Consumer Electronics,monitoring,stock_tracking/stock_info_files/monitoring/AAPL.md,,,"],
    )
    write_csv(
        root / "stock_tracking/rejected/rejected.csv",
        ["OLD,Old Co.,NASDAQ,US,Technology,Software,rejected,stock_tracking/stock_info_files/rejected/OLD.md,2026-05-01,Weak thesis,2026-06-12"],
    )
    for category in ("current_holdings", "monitoring", "rejected"):
        title = category.replace("_", " ").title()
        (root / f"stock_tracking/{category}/{category}_state.md").write_text(
            f"# {title} State\n\nLast updated: 2026-05-01\n\n## Current View\n\n- Seed.\n",
            encoding="utf-8",
        )
    (root / "agents/runs/2026-05-16_weekly/final_digest.md").write_text("# Final Digest\n", encoding="utf-8")
    return root


def write_csv(path: Path, rows: list[str]) -> None:
    header = "ticker,company_name,exchange,country,sector,industry,status,stock_info_file,date_rejected,reject_reason,next_eligible_review_date"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
