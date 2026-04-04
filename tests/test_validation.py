import tempfile
import unittest
from pathlib import Path

from cvrepo.validation import validate_offer_tree


class ValidationTests(unittest.TestCase):
    def test_validate_offer_tree_reports_missing_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            offer_dir = root / "2026" / "Q1" / "tier-1" / "ch" / "gva" / "lombard_odier"
            offer_dir.mkdir(parents=True)
            offer_path = offer_dir / "quant_dev_jr.md"
            offer_path.write_text("Quant Developer Junior", encoding="utf-8")
            issues = validate_offer_tree(root)
            self.assertTrue(issues)
            self.assertEqual(issues[0].level, "info")


if __name__ == "__main__":
    unittest.main()