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
        self.assertIn(r"\begin{minipage}<t>[c][][t]{\dimexpr\textheight-0.95in\relax}", content)
        self.assertIn(r"\fontsize{\readingCJKSize}{\readingCJKLead}\selectfont", content)
        self.assertNotIn(r"\begin{tabular}", content)

        # Paragraph breaks preserve column breaks with 0pt parskip and natural kanjiskip
        self.assertIn(r"\setlength{\parskip}{0pt}", content)
        self.assertIn(r"\ltjsetparameter{kanjiskip=1.8pt}", content)
        self.assertIn(r"子曰：\par", content)
        self.assertIn(r"巧言令色，\par", content)
        self.assertIn(r"鮮矣仁。\par", content)

        # Excerpt delimiter '---' produces 0.8em space
        self.assertIn(r"\vspace{0.8em}", content)

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

    def test_vertical_reading_column_converts_spaces_to_hspace(self):
        spaced_data_file = os.path.join(self.temp_dir.name, "spaced_data.json")
        data = {
            "lessons": [
                {
                    "lesson_number": 11,
                    "pages": [
                        {
                            "reading_title": "11.1 Reading",
                            "vocab_subtitle": "Vocabulary",
                            "vocab": [],
                            "reading_columns": [
                                "床前明月光。        處世若大夢。",
                            ],
                        }
                    ],
                }
            ],
        }
        with open(spaced_data_file, "w", encoding="utf-8") as f:
            json.dump(data, f)

        out_tex = os.path.join(self.temp_dir.name, "out_spaced.tex")
        manage_sheets.render_latex(spaced_data_file, out_tex, layout="vertical")
        with open(out_tex, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(r"床前明月光。\hspace{5.20em}處世若大夢。\par", content)

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

class TestEndToEndRendering(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_render_actual_lessons_data_both_modes(self):
        if not os.path.exists(manage_sheets.DATA_FILE):
            self.skipTest(f"{manage_sheets.DATA_FILE} not found")

        table_tex = os.path.join(self.temp_dir.name, "lessons_table.tex")
        vertical_tex = os.path.join(self.temp_dir.name, "lessons_vertical.tex")

        manage_sheets.render_latex(manage_sheets.DATA_FILE, table_tex, layout="table")
        manage_sheets.render_latex(manage_sheets.DATA_FILE, vertical_tex, layout="vertical")

        self.assertTrue(os.path.exists(table_tex))
        self.assertTrue(os.path.exists(vertical_tex))
        self.assertGreater(os.path.getsize(table_tex), 1000)
        self.assertGreater(os.path.getsize(vertical_tex), 1000)

        self.assertEqual(manage_sheets.detect_latex_engine(table_tex), "xelatex")
        self.assertEqual(manage_sheets.detect_latex_engine(vertical_tex), "lualatex")


class TestExportReadingsCLI(unittest.TestCase):
    def setUp(self):
        self.parser = manage_sheets.build_argument_parser()

    def test_export_readings_subparser_defaults(self):
        args = self.parser.parse_args(["export-readings"])
        self.assertEqual(args.input, manage_sheets.DATA_FILE)
        self.assertEqual(args.output, manage_sheets.READINGS_MD)

    def test_export_readings_subparser_custom_args(self):
        args = self.parser.parse_args(["export-readings", "-i", "my_data.json", "-o", "my_readings.md"])
        self.assertEqual(args.input, "my_data.json")
        self.assertEqual(args.output, "my_readings.md")


class TestExportReadings(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_data_file = os.path.join(self.temp_dir.name, "sample_lessons.json")
        self.output_md = os.path.join(self.temp_dir.name, "output.md")

        sample_data = {
            "lessons": [
                {
                    "lesson_number": 1,
                    "lesson_title": "Lesson 1",
                    "reading_title": "1.1. Reading: Analects 17.2",
                    "reading_columns": ["子曰。   性相近也。", "習相遠也。"],
                    "pages": [
                        {
                            "page_index": 1,
                            "reading_columns": ["DO_NOT_USE_PAGE_KEY"],
                        }
                    ],
                },
                {
                    "lesson_number": 3,
                    "lesson_title": "Lesson 3",
                    "reading_title": "3.1. Readings: Analects 12.22, Analects 4.2, and Analects 6.23",
                    "reading_columns": [
                        "樊遲問仁。子曰。愛人。",
                        "---",
                        "子曰。仁者安仁。",
                        "---",
                        "子曰。知者樂水。"
                    ],
                    "pages": [
                        {
                            "page_index": 1,
                            "reading_columns": ["DO_NOT_USE_PAGE_KEY_L3"],
                        }
                    ],
                },
            ]
        }
        with open(self.sample_data_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extract_reading_titles_handles_classic_of_the_way_and_virtue(self):
        title = "4.1. Readings: Analects 2.17, Classic of the Way and Virtue 33"
        titles = manage_sheets.extract_reading_titles(title, 2)
        self.assertEqual(titles, ["Analects 2.17", "Classic of the Way and Virtue 33"])

    def test_extract_reading_titles_handles_three_readings(self):
        title = "3.1. Readings: Analects 12.22, Analects 4.2, and Analects 6.23"
        titles = manage_sheets.extract_reading_titles(title, 3)
        self.assertEqual(titles, ["Analects 12.22", "Analects 4.2", "Analects 6.23"])

    def test_export_readings_generates_correct_markdown(self):
        manage_sheets.export_readings(self.sample_data_file, self.output_md)
        self.assertTrue(os.path.exists(self.output_md))
        with open(self.output_md, "r", encoding="utf-8") as f:
            content = f.read()

        # Check lesson headers
        self.assertIn("## Lesson 1", content)
        self.assertIn("## Lesson 3", content)

        # Check reading sub-headers
        self.assertIn("### Analects 17.2", content)
        self.assertIn("### Analects 12.22", content)
        self.assertIn("### Analects 4.2", content)
        self.assertIn("### Analects 6.23", content)

        # Check content and space collapsing
        self.assertIn("子曰。 性相近也。習相遠也。", content)
        self.assertIn("樊遲問仁。子曰。愛人。", content)
        self.assertIn("子曰。仁者安仁。", content)
        self.assertIn("子曰。知者樂水。", content)

        # Ensure page-level keys are ignored
        self.assertNotIn("DO_NOT_USE_PAGE_KEY", content)
        self.assertNotIn("DO_NOT_USE_PAGE_KEY_L3", content)


class TestFootnoteFormatting(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.sample_data_file = os.path.join(self.temp_dir.name, "sample_fn_data.json")
        sample_data = {
            "lessons": [
                {
                    "lesson_number": 1,
                    "lesson_title": "Lesson 1",
                    "pages": [
                        {
                            "page_index": 1,
                            "reading_title": "1.1 Reading",
                            "vocab_subtitle": "Vocabulary",
                            "vocab_cjk_font_size": "18pt",
                            "vocab": [
                                {
                                    "text": "曰 yuē v., to say",
                                    "footnotes": ["Notice 日 is narrower than 曰."],
                                    "stroke_tag": "[4 strokes]",
                                }
                            ],
                            "reading_columns": ["子曰。"],
                            "is_table_page": False,
                        },
                        {
                            "page_index": 2,
                            "reading_title": "1.2 Reading",
                            "vocab_subtitle": "Vocabulary Table",
                            "vocab_cjk_font_size": "14pt",
                            "vocab": [
                                {
                                    "character": "曰",
                                    "hint": "say",
                                    "pronunciation": "yuē",
                                    "meaning": "to say",
                                    "footnotes": ["Compare with 日."],
                                }
                            ],
                            "reading_columns": ["子曰。"],
                            "is_table_page": True,
                        }
                    ],
                }
            ]
        }
        with open(self.sample_data_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_format_footnote_text_uses_footnote_char(self):
        text = "Notice 日 is narrower than 曰."
        vocab_formatted = manage_sheets.format_vocab_text(text)
        fn_formatted = manage_sheets.format_footnote_text(text)
        self.assertIn(r"\vocabChar{日}", vocab_formatted)
        self.assertIn(r"\vocabChar{曰}", vocab_formatted)
        self.assertIn(r"\footnoteChar{日}", fn_formatted)
        self.assertIn(r"\footnoteChar{曰}", fn_formatted)
        self.assertNotIn(r"\vocabChar", fn_formatted)

    def test_render_latex_defines_and_sizes_footnote_cjk(self):
        out_tex = os.path.join(self.temp_dir.name, "out.tex")
        manage_sheets.render_latex(self.sample_data_file, out_tex)
        with open(out_tex, "r", encoding="utf-8") as f:
            content = f.read()

        # Preamble defaults
        self.assertIn(r"\newcommand{\footnoteCJKSize}{10.5pt}", content)
        self.assertIn(r"\newcommand{\footnoteCJKLead}{13pt}", content)
        self.assertIn(r"\newcommand{\footnoteChar}[1]", content)

        # Page 1: 18pt * 0.75 = 13.5pt
        self.assertIn(r"\renewcommand{\footnoteCJKSize}{13.5pt}", content)
        self.assertIn(r"\renewcommand{\footnoteCJKLead}{16.5pt}", content)

        # Page 2: 14pt * 0.75 = 10.5pt
        self.assertIn(r"\renewcommand{\footnoteCJKSize}{10.5pt}", content)
        self.assertIn(r"\renewcommand{\footnoteCJKLead}{12.8pt}", content)

        # Ensure footnoteChar is actually used in both list and table footnotes
        self.assertIn(r"\footnote{Notice \footnoteChar{日} is narrower than \footnoteChar{曰}.}", content)
        self.assertIn(r"Compare with \footnoteChar{日}.", content)


if __name__ == "__main__":
    unittest.main()


