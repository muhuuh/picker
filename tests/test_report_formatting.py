import unittest

from stock_research.report_formatting import compact_complete_text


class ReportFormattingTests(unittest.TestCase):
    def test_compact_complete_text_repairs_common_mojibake(self):
        self.assertEqual(compact_complete_text("32Ã— P/E and 3.95Ã— P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("32?? P/E and 3.95?? P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("32\u00d7 P/E and 3.95\u00d7 P/S"), "32x P/E and 3.95x P/S")

    def test_compact_complete_text_does_not_emit_visible_ellipsis(self):
        value = "Revenue increased. " + "This sentence is intentionally long " * 30
        compact = compact_complete_text(value, 80)
        self.assertNotIn("...", compact)
        self.assertNotIn("[...]", compact)


if __name__ == "__main__":
    unittest.main()
