from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from stock_research.config import get_config_value, read_env_file


class ConfigTests(unittest.TestCase):
    def test_read_env_file_parses_simple_values(self):
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / ".env"
            path.write_text(
                """
# comment
SEC_USER_AGENT="Stock Research test@example.com"
EMPTY=
""",
                encoding="utf-8",
            )

            values = read_env_file(path)

            self.assertEqual(values["SEC_USER_AGENT"], "Stock Research test@example.com")
            self.assertEqual(values["EMPTY"], "")

    def test_get_config_value_reads_repo_env(self):
        with TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / ".env").write_text("SEC_USER_AGENT=ua\n", encoding="utf-8")

            self.assertEqual(get_config_value(root, "SEC_USER_AGENT"), "ua")


if __name__ == "__main__":
    unittest.main()
