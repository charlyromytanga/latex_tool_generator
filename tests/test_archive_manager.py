import tempfile
import unittest
from pathlib import Path

from cvrepo.archive_manager import archive_rendered_pdfs


class ArchiveManagerTests(unittest.TestCase):
    def test_archive_rendered_pdfs_copies_into_archive_tree(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            source = root / "render"
            archive = root / "archive"
            source.mkdir()
            pdf = source / "cv_fr_sample.pdf"
            pdf.write_bytes(b"%PDF-1.4")
            archived = archive_rendered_pdfs(source, archive)
            self.assertEqual(len(archived), 1)
            self.assertTrue(archived[0].destination.exists())
            self.assertTrue(pdf.exists())


if __name__ == "__main__":
    unittest.main()