import unittest

from cvrepo.job_parser import analyze_text


class JobParserTests(unittest.TestCase):
    def test_analyze_text_extracts_basic_fields(self) -> None:
        text = """
        Quant Developer Junior
        Location: Geneva
        Full-time

        Responsibilities
        Build pricing tools and analyse risk metrics with Python and C++.

        Requirements
        Master degree in mathematics. 2 years experience. Python required.
        """
        summary = analyze_text(text)
        self.assertEqual(summary["title"], "Quant Developer Junior")
        self.assertEqual(summary["employment_type"], "Full-time")
        self.assertIn("Python", summary["skills"])
        self.assertEqual(summary["experience_years"], 2)


if __name__ == "__main__":
    unittest.main()
