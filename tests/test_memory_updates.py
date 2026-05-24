from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.memory import load_memory_state, validate_memory_state
from stock_research.memory_updates import (
    apply_memory_update_draft,
    build_memory_update_draft,
    write_memory_update_draft,
)


class MemoryUpdateTests(unittest.TestCase):
    def test_memory_update_draft_validates_reflection_proposal(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            write_reflection_with_proposal(root, "2026-05-09_weekly")

            draft = build_memory_update_draft(root, "2026-05-09_weekly", date(2026, 5, 5))
            json_path, md_path = write_memory_update_draft(root, draft)

            self.assertEqual(len(draft.items), 1)
            self.assertEqual(draft.items[0].status, "ready")
            self.assertTrue(draft.items[0].fields["id"].startswith("eval-2026-05-05"))
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())
            self.assertIn("Memory Update Drafts", md_path.read_text(encoding="utf-8"))

    def test_apply_memory_update_draft_writes_selected_ready_item(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            write_reflection_with_proposal(root, "2026-05-09_weekly")
            draft = build_memory_update_draft(root, "2026-05-09_weekly", date(2026, 5, 5))
            write_memory_update_draft(root, draft)

            result = apply_memory_update_draft(
                root=root,
                run_id="2026-05-09_weekly",
                proposal_ids={draft.items[0].proposal_id},
                current_date=date(2026, 5, 5),
            )
            memory = load_memory_state(root)
            report = validate_memory_state(memory)
            updated_draft = json.loads((root / "agents/runs/2026-05-09_weekly/memory_update_drafts.json").read_text(encoding="utf-8"))

            self.assertEqual(len(result.applied), 1)
            self.assertFalse(result.skipped)
            self.assertEqual(updated_draft["items"][0]["status"], "applied")
            self.assertTrue(report.ok, report.errors)
            self.assertIn("Test reflection lesson", (root / "agents/memory/evaluation_metrics.md").read_text(encoding="utf-8"))

    def test_memory_update_draft_blocks_duplicate_lesson(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            write_reflection_with_proposal(root, "2026-05-09_weekly")
            (root / "agents/memory/evaluation_metrics.md").write_text(
                """# Evaluation Metrics

- id: eval-existing
- date: 2026-05-05
- type: evaluation
- scope: global
- status: active
- confidence: medium
- trigger/source: test
- lesson: Test reflection lesson.
- use_when: Testing.
- do_not_use_when: Outside tests.
- evidence: `test`
- owner: tests
- next_review: 2026-06-01
""",
                encoding="utf-8",
            )

            draft = build_memory_update_draft(root, "2026-05-09_weekly", date(2026, 5, 5))

            self.assertEqual(draft.items[0].status, "blocked")
            self.assertIn("matching active/needs_review", draft.items[0].issues[0])


def seed_memory_update_repo(root: Path) -> Path:
    (root / "AGENTS.md").write_text("# AGENTS\n", encoding="utf-8")
    (root / "stock_tracking").mkdir(parents=True)
    (root / "agents/memory").mkdir(parents=True)
    (root / "agents/runs/2026-05-09_weekly").mkdir(parents=True)
    for name in [
        "README.md",
        "memory_index.md",
        "orchestrator_lessons.md",
        "source_quality.md",
        "specialist_playbooks.md",
        "evaluation_metrics.md",
        "deprecated_memory.md",
    ]:
        title = name.replace("_", " ").replace(".md", "").title()
        (root / "agents/memory" / name).write_text(f"# {title}\n", encoding="utf-8")
    return root


def write_reflection_with_proposal(root: Path, run_id: str) -> None:
    (root / "agents/runs" / run_id / "memory_reflection.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "run_dir": f"agents/runs/{run_id}",
                "generated_at": "2026-05-05",
                "metrics": {"issues": 1},
                "issues": [],
                "memory_update_proposals": [
                    {
                        "proposal_id": "proposal-test",
                        "action": "memory_add",
                        "target_file": "evaluation_metrics.md",
                        "reason": "Unit test proposal.",
                        "fields": {
                            "type": "evaluation",
                            "scope": "global",
                            "status": "needs_review",
                            "confidence": "medium",
                            "trigger/source": "unit test reflection",
                            "lesson": "Test reflection lesson.",
                            "use_when": "Testing memory draft/apply.",
                            "do_not_use_when": "Outside tests.",
                            "evidence": "`tests/test_memory_updates.py`",
                            "owner": "memory tests",
                            "next_review": "2026-06-01",
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
