import json
import tempfile
import unittest
from pathlib import Path

from cvrepo.pipeline import build_offer_summary, write_summary


class PipelineTests(unittest.TestCase):
    def test_build_offer_summary_enriches_with_offer_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            offer_dir = root / "2026" / "Q1" / "tier-1" / "switzerland" / "geneva" / "lombard_odier"
            offer_dir.mkdir(parents=True)
            offer = offer_dir / "offer_quant_dev.md"
            offer.write_text("Quant Developer\nGeneva\nFull-time\nPython and SQL.", encoding="utf-8")

            summary = build_offer_summary(offer, root)

            self.assertEqual(summary["company"], "lombard_odier")
            self.assertEqual(summary["city"], "geneva")
            self.assertEqual(summary["tier"], "tier-1")

    def test_write_summary_persists_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            offer = root / "offer.md"
            offer.write_text("Offer", encoding="utf-8")
            destination = write_summary({"title": "Quant"}, offer, root / "summaries")

            self.assertTrue(destination.exists())
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["title"], "Quant")


if __name__ == "__main__":
    unittest.main()