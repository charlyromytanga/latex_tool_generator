import tempfile
import unittest
from pathlib import Path

from cvrepo.metadata import artifact_record, infer_artifact_type, infer_language


class MetadataIndexTests(unittest.TestCase):
    def test_infer_artifact_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "cv_fr_2026q1_lo_quantdev.pdf"
            pdf_path.write_bytes(b"%PDF-1.4")
            record = artifact_record(pdf_path)
            self.assertEqual(infer_artifact_type(pdf_path), "cv")
            self.assertEqual(infer_language(pdf_path), "fr")
            self.assertEqual(record["filename"], pdf_path.name)


if __name__ == "__main__":
    unittest.main()
