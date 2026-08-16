import json
from pathlib import Path
import unittest

from stock_research.report_characterization import (
    READER_VALUE_RUBRIC,
    characterize_report_corpus,
    evaluate_reader_value,
)
from stock_research.report_quality import validate_human_facing_markdown


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "report_quality"


class ReportCharacterizationTests(unittest.TestCase):
    def test_known_bad_corpus_fails_despite_legacy_zero_findings(self):
        metadata = json.loads((FIXTURE_ROOT / "characterization.json").read_text(encoding="utf-8"))
        baseline = json.loads((FIXTURE_ROOT / metadata["legacy_quality_report"]).read_text(encoding="utf-8"))
        corpus = json.loads((FIXTURE_ROOT / metadata["known_bad_corpus"]).read_text(encoding="utf-8"))
        reports = corpus["reports"]

        corpus_findings = characterize_report_corpus(reports)
        per_report_findings = [
            finding
            for text in reports.values()
            for finding in validate_human_facing_markdown(text)
        ]

        self.assertEqual(baseline["run_id"], metadata["source_run"])
        self.assertEqual(baseline["metrics"]["findings"], 0)
        self.assertEqual(baseline["findings"], [])
        self.assertEqual(metadata["expected_verdict"], "fail")
        self.assertTrue(any(finding.category == "cross_report_boilerplate" for finding in corpus_findings))
        self.assertIn("Dangling sentence fragment found.", per_report_findings)
        self.assertIn("Historical output excerpts", corpus["snapshot_notice"])
        self.assertEqual(set(reports), {f"{name}_final_human_report.md" for name in metadata["source_report_names"]})
        self.assertEqual(len(reports), metadata["source_report_count"])
        self.assertTrue(
            any(len(finding.evidence_paths) == 12 for finding in corpus_findings),
            "The known 12-report boilerplate regression must remain characterized.",
        )

    def test_real_positive_reader_excerpts_pass_their_executable_rubric(self):
        metadata = json.loads((FIXTURE_ROOT / "characterization.json").read_text(encoding="utf-8"))
        reports = {}
        for relative_path, options in metadata["positive_reports"].items():
            text = (FIXTURE_ROOT / relative_path).read_text(encoding="utf-8")
            reports[relative_path] = text
            results = evaluate_reader_value(
                text,
                subject_terms=tuple(options["subject_terms"]),
                require_x_insight=options["require_x_insight"],
            )
            failures = [f"{result.dimension}: {result.reason}" for result in results if result.required and not result.passed]
            self.assertEqual(failures, [], relative_path)

        self.assertEqual(characterize_report_corpus(reports, minimum_report_count=2), [])
        for text in reports.values():
            self.assertEqual(validate_human_facing_markdown(text), [])

    def test_near_duplicate_template_with_subject_substitution_is_flagged(self):
        reports = {
            "ALPHA_final_human_report.md": "The key judgment for ALPHA is whether customer demand is becoming verified operating evidence rather than merely louder social attention.",
            "BRAVO_final_human_report.md": "The key judgment for BRAVO is whether customer demand is becoming verified operating proof rather than merely louder social attention.",
            "CHARLIE_final_human_report.md": "The key judgment for CHARLIE is whether customer demand is becoming verified business evidence instead of merely louder social attention.",
        }

        findings = characterize_report_corpus(reports)

        self.assertTrue(any(finding.category == "cross_report_near_boilerplate" for finding in findings))

    def test_padding_does_not_pass_reader_efficiency(self):
        text = (
            "# PAD Final Human Report\n\n## Bottom Line\n\n"
            + "Depth sentence for realistic report coverage. " * 260
            + "\n\n## Sources\n\n[Internal source](https://example.com/source)"
        )

        results = {result.dimension: result for result in evaluate_reader_value(text, subject_terms=("PAD",))}

        self.assertFalse(results["reader_efficiency"].passed)
        self.assertFalse(results["material_change"].passed)

    def test_reader_value_rubric_covers_decision_value_and_completeness(self):
        dimensions = {item["dimension"] for item in READER_VALUE_RUBRIC}

        self.assertIn("material_change", dimensions)
        self.assertIn("x_insight", dimensions)
        self.assertIn("reader_efficiency", dimensions)
        self.assertIn("completeness", dimensions)


if __name__ == "__main__":
    unittest.main()
