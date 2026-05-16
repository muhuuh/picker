import unittest

from stock_research.report_formatting import compact_complete_text


class ReportFormattingTests(unittest.TestCase):
    def test_compact_complete_text_repairs_common_mojibake(self):
        self.assertEqual(compact_complete_text("32Ã— P/E and 3.95Ã— P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("32?? P/E and 3.95?? P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("32\u00d7 P/E and 3.95\u00d7 P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("\u00e2\u20ac\u00a2 Revenue \u00e2\u2020\u2019 up"), "- Revenue -> up")

    def test_compact_complete_text_does_not_emit_visible_ellipsis(self):
        value = "Revenue increased. " + "This sentence is intentionally long " * 30
        compact = compact_complete_text(value, 80)
        self.assertNotIn("...", compact)
        self.assertNotIn("[...]", compact)

    def test_compact_complete_text_removes_dangling_tail_fragments(self):
        self.assertEqual(compact_complete_text("Gross profit margin expanded to 62% (up.", 120), "Gross profit margin expanded to 62%")
        self.assertEqual(compact_complete_text("The company recently announc.", 120), "The company recently")


if __name__ == "__main__":
    unittest.main()
