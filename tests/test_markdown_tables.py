import unittest

from stock_research.markdown_tables import first_markdown_table


class MarkdownTableTests(unittest.TestCase):
    def test_first_markdown_table_parses_rows(self):
        text = """
# Title

| ID | Status |
| --- | --- |
| HIR-0001 | new |
| HIR-0002 | done |
"""
        rows = first_markdown_table(text)

        self.assertEqual(rows[0]["ID"], "HIR-0001")
        self.assertEqual(rows[0]["Status"], "new")
        self.assertEqual(rows[1]["ID"], "HIR-0002")


if __name__ == "__main__":
    unittest.main()
