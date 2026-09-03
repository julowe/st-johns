import unittest
import sys
import os
import tempfile
import json

# Add parent directory to path so manage_sheets can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import manage_sheets


class TestCLIParsing(unittest.TestCase):
    def setUp(self):
        self.parser = manage_sheets.build_argument_parser()

    def test_render_default_layout(self):
        args = self.parser.parse_args(["render"])
        self.assertEqual(args.layout, "table")

    def test_render_explicit_table_layout(self):
        args = self.parser.parse_args(["render", "--layout", "table"])
        self.assertEqual(args.layout, "table")

    def test_render_explicit_vertical_layout(self):
        args = self.parser.parse_args(["render", "--layout", "vertical"])
        self.assertEqual(args.layout, "vertical")

    def test_render_invalid_layout(self):
        with self.assertRaises(SystemExit):
            self.parser.parse_args(["render", "--layout", "invalid"])

    def test_all_default_layout(self):
        args = self.parser.parse_args(["all"])
        self.assertEqual(args.layout, "table")

    def test_all_explicit_vertical_layout(self):
        args = self.parser.parse_args(["all", "--layout", "vertical"])
        self.assertEqual(args.layout, "vertical")


class TestPreambleGeneration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_data_file = os.path.join(self.temp_dir.name, "sample_data.json")
        sample_data = {
            "global_reading_row_spacing": "4pt",
            "lessons": [
                {
                    "lesson_number": 1,
                    "lesson_title": "Lesson 1",
                    "pages": [
                        {
                            "reading_title": "1.1 Reading",
                            "vocab_subtitle": "Vocabulary",
                            "vocab": [],
                            "reading_columns": ["子曰。"],
                        }
                    ],
                }
            ],
        }
        with open(self.sample_data_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_table_preamble_contains_xecjk(self):
        out_tex = os.path.join(self.temp_dir.name, "table.tex")
        manage_sheets.render_latex(self.sample_data_file, out_tex, layout="table")
        with open(out_tex, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\usepackage{xeCJK}", content)
        self.assertIn(r"\setCJKmainfont{SimSun.ttf}", content)
        self.assertIn(r"\newcommand{\cjkvertchar}", content)
        self.assertIn(r"\newcommand{\readingPunc}", content)
        self.assertNotIn(r"\usepackage{luatexja}", content)

    def test_vertical_preamble_contains_luatexja(self):
        out_tex = os.path.join(self.temp_dir.name, "vertical.tex")
        manage_sheets.render_latex(self.sample_data_file, out_tex, layout="vertical")
        with open(out_tex, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(r"\usepackage{luatexja}", content)
        self.assertIn(r"\usepackage{luatexja-fontspec}", content)
        self.assertIn(r"\usepackage{lltjext}", content)
        self.assertIn(r"\setmainjfont{SimSun.ttf}", content)
        self.assertIn(r"TateFeatures = {JFM = {zh_TW/{quanjiao,vert}}}", content)
        self.assertNotIn(r"\usepackage{xeCJK}", content)
        self.assertNotIn(r"\newcommand{\cjkvertchar}", content)
        self.assertNotIn(r"\newcommand{\readingPunc}", content)
        # Sizing macros for the vertical minipage should still be present
        self.assertIn(r"\newcommand{\readingCJKSize}", content)
        self.assertIn(r"\newcommand{\readingCJKLead}", content)

if __name__ == "__main__":
    unittest.main()
