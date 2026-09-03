import unittest
import sys
import os

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


if __name__ == "__main__":
    unittest.main()
