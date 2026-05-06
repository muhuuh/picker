from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.memory_llm_writer import (
    build_memory_writer_prompt,
    build_memory_writer_review,
    call_openai_memory_writer,
    write_memory_writer_prompt,
)


class MemoryLlmWriterTests(unittest.TestCase):
    def test_writer_prompt_includes_draft_and_guardrails(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            write_reflection_with_proposal(root, "2026-05-09_weekly")

            prompt = build_memory_writer_prompt(root, "2026-05-09_weekly", date(2026, 5, 5))
            json_path, md_path = write_memory_writer_prompt(root, prompt)

            self.assertEqual(prompt.run_id, "2026-05-09_weekly")
            self.assertIn("memory_update_draft", prompt.input_payload)
            self.assertIn("Do not store secrets.", prompt.input_payload["guardrails"])
            self.assertTrue(json_path.exists())
            self.assertTrue(md_path.exists())

    def test_deterministic_writer_review_accepts_ready_draft_and_updates_drafts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            write_reflection_with_proposal(root, "2026-05-09_weekly")

            review, paths = build_memory_writer_review(
                root=root,
                run_id="2026-05-09_weekly",
                current_date=date(2026, 5, 5),
                execute=False,
                update_drafts=True,
                write_artifacts=True,
            )
            updated_draft = json.loads((root / "agents/runs/2026-05-09_weekly/memory_update_drafts.json").read_text(encoding="utf-8"))

            self.assertEqual(review.mode, "deterministic_review")
            self.assertEqual(review.recommendations[0].decision, "accept")
            self.assertTrue(any(path.name == "memory_writer_review.md" for path in paths))
            self.assertEqual(updated_draft["items"][0]["status"], "ready")

    def test_openai_writer_response_is_parsed_and_validated(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            write_reflection_with_proposal(root, "2026-05-09_weekly")
            draft = build_memory_writer_review(root, "2026-05-09_weekly", date(2026, 5, 5), execute=False)[0]
            fields = draft.recommendations[0].fields

            response = call_openai_memory_writer(
                build_memory_writer_prompt(root, "2026-05-09_weekly", date(2026, 5, 5)),
                api_key="test-key",
                responder=lambda _payload: {
                    "output": [
                        {
                            "content": [
                                {
                                    "text": json.dumps(
                                        {
                                            "recommendations": [
                                                {
                                                    "proposal_id": "proposal-test",
                                                    "decision": "revise",
                                                    "target_file": "evaluation_metrics.md",
                                                    "reason": "Shortened lesson.",
                                                    "fields": {**fields, "lesson": "Shortened test reflection lesson."},
                                                }
                                            ]
                                        }
                                    )
                                }
                            ]
                        }
                    ]
                },
            )

            self.assertEqual(response["recommendations"][0]["decision"], "revise")

    def test_writer_review_can_run_without_writing_artifacts(self):
        with TemporaryDirectory() as temp_dir:
            root = seed_memory_update_repo(Path(temp_dir))
            run_dir = root / "agents/runs/2026-05-09_weekly"
            write_reflection_with_proposal(root, "2026-05-09_weekly")

            review, paths = build_memory_writer_review(
                root=root,
                run_id="2026-05-09_weekly",
                current_date=date(2026, 5, 5),
                execute=False,
                write_artifacts=False,
            )

            self.assertEqual(review.mode, "deterministic_review")
            self.assertEqual(paths, [])
            self.assertFalse((run_dir / "memory_writer_prompt.json").exists())
            self.assertFalse((run_dir / "memory_writer_review.json").exists())


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
                            "use_when": "Testing memory writer.",
                            "do_not_use_when": "Outside tests.",
                            "evidence": "`tests/test_memory_llm_writer.py`",
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
