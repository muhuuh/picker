import unittest

from stock_research.report_formatting import compact_complete_text


class ReportFormattingTests(unittest.TestCase):
    def test_compact_complete_text_repairs_common_mojibake(self):
        self.assertEqual(compact_complete_text("32Ã— P/E and 3.95Ã— P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("32?? P/E and 3.95?? P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("32\u00d7 P/E and 3.95\u00d7 P/S"), "32x P/E and 3.95x P/S")
        self.assertEqual(compact_complete_text("\u00e2\u20ac\u00a2 Revenue \u00e2\u2020\u2019 up"), "- Revenue -> up")

    def test_compact_complete_text_stops_at_a_real_sentence_boundary(self):
        value = "Revenue increased because demand improved. " + "This sentence is intentionally long " * 30
        compact = compact_complete_text(value, 80)
        self.assertNotIn("...", compact)
        self.assertNotIn("[...]", compact)
        self.assertEqual(compact, "Revenue increased because demand improved.")

    def test_compact_complete_text_does_not_repair_fragments_into_fake_sentences(self):
        self.assertEqual(compact_complete_text("Gross profit margin expanded to 62% (up.", 120), "")
        self.assertEqual(compact_complete_text("The company recently announc.", 120), "")
        self.assertEqual(
            compact_complete_text("Revenue increased. The company recently announc.", 120),
            "Revenue increased.",
        )

    def test_compact_complete_text_preserves_source_ellipsis_instead_of_hiding_it(self):
        self.assertEqual(compact_complete_text("Management said demand was... still developing.", 120), "")

    def test_compact_complete_text_does_not_cut_at_an_abbreviation(self):
        value = "Revenue grew in the U.S. and Europe. The next sentence contains more detail."

        compact = compact_complete_text(value, 28)

        self.assertEqual(compact, "Revenue grew in the U.S. and Europe.")


if __name__ == "__main__":
    unittest.main()
