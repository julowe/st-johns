import unittest
from unittest.mock import patch
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

class TestReadingColumnRendering(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.multi_excerpt_data_file = os.path.join(self.temp_dir.name, "multi_data.json")
        data = {
            "global_reading_row_spacing": "4pt",
            "lessons": [
                {
                    "lesson_number": 3,
                    "lesson_title": "Lesson 3",
                    "pages": [
                        {
                            "reading_title": "3.1 Reading",
                            "vocab_subtitle": "Vocabulary",
                            "vocab": [],
                            "reading_cjk_font_size": "18pt",
                            "reading_columns": [
                                "子曰：",
                                "巧言令色，",
                                "---",
                                "鮮矣仁。",
                            ],
                        }
                    ],
                }
            ],
        }
        with open(self.multi_excerpt_data_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_vertical_reading_column_uses_minipage_t(self):
        out_tex = os.path.join(self.temp_dir.name, "out_vertical.tex")
        manage_sheets.render_latex(self.multi_excerpt_data_file, out_tex, layout="vertical")
        with open(out_tex, "r", encoding="utf-8") as f:
            content = f.read()

        # Minipage container with <t> direction
        self.assertIn(r"\begin{minipage}<t>[c][][t]{\dimexpr\textheight-1.2in\relax}", content)
        self.assertIn(r"\fontsize{\readingCJKSize}{\readingCJKLead}\selectfont", content)
        self.assertNotIn(r"\begin{tabular}", content)

        # Paragraph breaks preserve column breaks
        self.assertIn(r"子曰：\par", content)
        self.assertIn(r"巧言令色，\par", content)
        self.assertIn(r"鮮矣仁。\par", content)

        # Excerpt delimiter '---' produces 2em space
        self.assertIn(r"\vspace{2em}", content)

        # Font size override updated without punctuation overrides
        self.assertIn(r"\renewcommand{\readingCJKSize}{18pt}", content)
        self.assertNotIn(r"\renewcommand{\readingPuncSize}", content)

    def test_table_reading_column_preserves_tabular(self):
        out_tex = os.path.join(self.temp_dir.name, "out_table.tex")
        manage_sheets.render_latex(self.multi_excerpt_data_file, out_tex, layout="table")
        with open(out_tex, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(r"\begin{tabular}", content)
        self.assertIn(r"\cjkvertchar", content)
        self.assertNotIn(r"\begin{minipage}<t>", content)
        self.assertIn(r"\renewcommand{\readingPuncSize}", content)

class TestCompilerEngineDetection(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_detect_lualatex_when_luatexja_present(self):
        tex_path = os.path.join(self.temp_dir.name, "doc.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write("\\documentclass{article}\n\\usepackage{luatexja}\n\\begin{document}Hi\\end{document}")
        engine = manage_sheets.detect_latex_engine(tex_path)
        self.assertEqual(engine, "lualatex")

    def test_detect_xelatex_when_luatexja_absent(self):
        tex_path = os.path.join(self.temp_dir.name, "doc.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write("\\documentclass{article}\n\\usepackage{xeCJK}\n\\begin{document}Hi\\end{document}")
        engine = manage_sheets.detect_latex_engine(tex_path)
        self.assertEqual(engine, "xelatex")

    @patch("subprocess.run")
    def test_compile_latex_invokes_detected_engine(self, mock_run):
        mock_run.return_value.returncode = 0
        tex_path = os.path.join(self.temp_dir.name, "doc.tex")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write("\\documentclass{article}\n\\usepackage{luatexja}\n\\begin{document}Hi\\end{document}")

        manage_sheets.compile_latex(tex_path)

        # Verify subprocess.run was called with lualatex
        called_cmd = mock_run.call_args_list[0][0][0]
        self.assertEqual(called_cmd[0], "lualatex")
        self.assertEqual(called_cmd[1], "-interaction=nonstopmode")

if __name__ == "__main__":
    unittest.main()


