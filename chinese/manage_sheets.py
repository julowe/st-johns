#!/usr/bin/env python3
"""
manage_sheets.py

Modular CLI pipeline for extracting, editing, and generating Classical Chinese
study sheets from Bryan W. van Norden's textbook EPUB.

Commands:
  extract   Extract data from EPUB to intermediate JSON (lessons_data.json)
  render    Render intermediate JSON to LaTeX master document (lessons_all.tex)
  compile   Compile LaTeX document to PDF (lessons_all.pdf) via xelatex or lualatex (auto-detected)
  worksheet Generate stroke-order practice worksheets via chinese-worksheet-generator
  all       Run full pipeline (extract if missing, render, compile)
"""

import os
import re
import sys
import json
import shutil
import argparse
import subprocess
import zipfile
import xml.etree.ElementTree as ET

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPUB_PATH = os.path.join(
    BASE_DIR,
    "Classical Chinese for Everyone_ A Guide for Absolute Beginners - Bryan W. van Norden.epub",
)
FONTS_DIR = os.path.join(BASE_DIR, "fonts")
DATA_FILE = os.path.join(BASE_DIR, "lessons_data.json")
STROKES_FILE = os.path.join(BASE_DIR, "stroke_counts.json")
TEX_FILE = os.path.join(BASE_DIR, "lessons_all.tex")
PDF_FILE = os.path.join(BASE_DIR, "lessons_all.pdf")
READINGS_MD = os.path.join(BASE_DIR, "readings.md")
WORKSHEET_GENERATOR_DIR = os.environ.get("WORKSHEET_GENERATOR_DIR")
WORKSHEETS_DIR = os.path.join(BASE_DIR, "worksheets")

NS = {"xhtml": "http://www.w3.org/1999/xhtml"}


def latex_escape(text: str) -> str:
    """Escape LaTeX special characters while preserving CJK and Unicode text."""
    if not text:
        return ""
    # Map special LaTeX characters
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("~", r"\textasciitilde{}"),
        ("^", r"\textasciicircum{}"),
    ]
    # Handle backslash first
    text = text.replace("\\", r"\textbackslash{}")
    for orig, repl in replacements[1:]:
        text = text.replace(orig, repl)
    return text


def load_stroke_map() -> dict:
    """Load stroke counts mapping from stroke_counts.json."""
    if os.path.exists(STROKES_FILE):
        try:
            with open(STROKES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Could not load {STROKES_FILE}: {e}")
    return {}


def compute_stroke_tag(text: str, stroke_map: dict) -> str:
    """Compute stroke count tag for CJK characters at the start of a definition."""
    # Find initial CJK characters before English / pinyin (e.g. 齊 (齐) or 道 or 文章)
    # Grab the headword portion (before the first Latin letter)
    match = re.match(r"^([\u4e00-\u9fff\s\(\)（）]+)", text.strip())
    if not match:
        return ""

    head_chars = [c for c in match.group(1) if "\u4e00" <= c <= "\u9fff"]
    if not head_chars:
        return ""

    # Unique characters while preserving order
    seen = set()
    uniq_chars = []
    for c in head_chars:
        if c not in seen:
            seen.add(c)
            uniq_chars.append(c)

    parts = []
    for c in uniq_chars:
        cnt = stroke_map.get(c)
        if cnt is not None:
            parts.append(f"{c}: {cnt}")

    if not parts:
        return ""
    if len(parts) == 1 and len(uniq_chars) == 1:
        cnt = stroke_map.get(uniq_chars[0])
        return f"[{cnt} strokes]"
    return f"[{', '.join(parts)} strokes]"


def extract_fonts(epub_path: str, fonts_dir: str):
    """Extract embedded fonts from EPUB into fonts directory."""
    os.makedirs(fonts_dir, exist_ok=True)
    with zipfile.ZipFile(epub_path, "r") as z:
        for name in z.namelist():
            if name.startswith("OEBPS/font/"):
                fname = os.path.basename(name)
                if fname:
                    dest = os.path.join(fonts_dir, fname)
                    with open(dest, "wb") as f:
                        f.write(z.read(name))
    print(f"[✓] Extracted publisher fonts to {fonts_dir}")


def extract_epub_data(epub_path: str, force: bool = False) -> dict:
    """Extract all 13 lessons from EPUB and write intermediate JSON."""
    existing_data = {}
    if os.path.exists(DATA_FILE) and not force:
        print(f"[!] {DATA_FILE} already exists.")
        print("    If you want to overwrite and re-extract, pass --force.")
        return {}

    old_global_spacing = "4pt"
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                old_doc = json.load(f)
                old_global_spacing = old_doc.get("global_reading_row_spacing", "4pt")
                for lesson_epub in old_doc.get("lessons", []):
                    lnum = lesson_epub.get("lesson_number")
                    existing_data[lnum] = {
                        p.get("page_index"): p for p in lesson_epub.get("pages", [])
                    }
        except Exception as e:
            print(
                f"[!] Warning: Could not read existing {DATA_FILE} to preserve configs: {e}"
            )

    if not os.path.exists(epub_path):
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")

    extract_fonts(epub_path, FONTS_DIR)
    stroke_map = load_stroke_map()

    lessons_data = []

    with zipfile.ZipFile(epub_path, "r") as z:
        for lesson_num in range(1, 14):
            ch_name = f"OEBPS/DSHPC083-ch{lesson_num:02d}.xhtml"
            root = ET.fromstring(z.read(ch_name))

            # Main lesson title
            lesson_title = f"Lesson {lesson_num}"
            for p in root.iter(f"{{{NS['xhtml']}}}p"):
                if p.attrib.get("class") == "LN":
                    txt = "".join(p.itertext()).strip()
                    txt = re.sub(r"\{\d+\}\s*", "", txt)
                    lesson_title = txt
                    break

            # Prefer the content div that has id="chNN" (Google Play epub structure);
            # fall back to whichever div has the most direct children, then body.
            chapter_id = f"ch{lesson_num:02d}"
            container = root.find(f".//{{{NS['xhtml']}}}div[@id='{chapter_id}']")
            if container is None:
                # pick the div with the most direct children as the content container
                all_divs = root.findall(f".//{{{NS['xhtml']}}}div")
                if all_divs:
                    container = max(all_divs, key=lambda d: len(list(d)))
            if container is None:
                container = root.find(f"{{{NS['xhtml']}}}body")

            # Build chapter footnote definition map
            footnote_map = {}
            for elem in root.iter():
                e_id = elem.attrib.get("id", "")
                if e_id.startswith("footnote-") and not e_id.endswith("-backlink"):
                    txt = "".join(elem.itertext()).strip()
                    txt_clean = re.sub(r"^\d+\.\s*", "", txt)
                    footnote_map[e_id] = txt_clean

            reading_title = ""
            raw_columns = []
            vocab_subtitle = ""
            vocab_items = []

            state = "BEFORE"
            for child in container:
                elem_id = child.attrib.get("id", "")
                cls = child.attrib.get("class", "")
                text = "".join(child.itertext()).strip()
                text_clean = re.sub(r"\{\d+\}\s*", "", text)

                if elem_id == f"sec-{lesson_num}-1" or (
                    cls.startswith("LS") and f"{lesson_num}.1" in text_clean
                ):
                    state = "READING"
                    reading_title = text_clean
                    continue
                elif elem_id == f"sec-{lesson_num}-2" or (
                    cls.startswith("LS") and f"{lesson_num}.2" in text_clean
                ):
                    state = "VOCAB"
                    continue
                elif elem_id == f"sec-{lesson_num}-3" or (
                    cls.startswith("LS") and f"{lesson_num}.3" in text_clean
                ):
                    state = "AFTER"
                    break

                if state == "READING":
                    if child.tag.endswith("table"):
                        for tr in child.iter(f"{{{NS['xhtml']}}}tr"):
                            tds = tr.findall(f"{{{NS['xhtml']}}}td")
                            # Traditional layout progresses Right-to-Left
                            for td in reversed(tds):
                                lines = [
                                    "".join(p.itertext()).strip()
                                    for p in td.findall(f"{{{NS['xhtml']}}}p")
                                ]
                                col_str = "".join(lines)
                                # Keep empty cols as separators if needed or skip
                                if col_str:
                                    raw_columns.append(col_str)
                                elif len(raw_columns) > 0 and raw_columns[-1] != "---":
                                    raw_columns.append("---")
                    elif child.tag.endswith("p") and text_clean:
                        # Extra reading heading or text note if present
                        pass

                elif state == "VOCAB":
                    if child.tag.endswith("p"):
                        if cls == "LS2" and not vocab_subtitle:
                            vocab_subtitle = text_clean
                        elif cls == "POE" or "POE" in cls:
                            v_text = text_clean

                            # Extract any footnote anchor links
                            fn_anchors = [
                                a.attrib.get("href", "").lstrip("#")
                                for a in child.iter(f"{{{NS['xhtml']}}}a")
                                if a.attrib.get("href", "").startswith("#footnote")
                            ]
                            fn_texts = [
                                footnote_map[a] for a in fn_anchors if a in footnote_map
                            ]

                            # Clean trailing footnote digits
                            v_text = re.sub(r"(\d+)$", "", text_clean).strip()
                            stroke_tag = compute_stroke_tag(v_text, stroke_map)
                            full_line = f"{v_text} {stroke_tag}".strip()
                            vocab_items.append(
                                {
                                    "text": v_text,
                                    "footnotes": fn_texts,
                                    "stroke_tag": stroke_tag,
                                    "full_line": full_line,
                                }
                            )
                    elif child.tag.endswith("table"):
                        # Lesson 10 Dictionary practice table
                        for tr in child.iter(f"{{{NS['xhtml']}}}tr"):
                            tds = tr.findall(f"{{{NS['xhtml']}}}td")
                            cells = ["".join(td.itertext()).strip() for td in tds]
                            if any(cells):
                                # Skip header row
                                if cells[0] == "Character" or "Pronunciation" in cells:
                                    continue
                                char_cell = cells[0]
                                hint_cell = cells[1] if len(cells) > 1 else ""
                                pron_cell = cells[2] if len(cells) > 2 else ""
                                mean_cell = cells[3] if len(cells) > 3 else ""

                                # Extract footnote anchor links in this row
                                fn_anchors = []
                                for td in tds:
                                    for a in td.iter(f"{{{NS['xhtml']}}}a"):
                                        href = a.attrib.get("href", "")
                                        if href.startswith("#footnote"):
                                            fn_anchors.append(href.lstrip("#"))
                                fn_texts = [
                                    footnote_map[a]
                                    for a in fn_anchors
                                    if a in footnote_map
                                ]

                                mean_clean = re.sub(r"\d+$", "", mean_cell).strip()

                                vocab_items.append(
                                    {
                                        "is_table_row": True,
                                        "character": char_cell,
                                        "hint": hint_cell,
                                        "pronunciation": pron_cell,
                                        "meaning": mean_clean,
                                        "footnotes": fn_texts,
                                    }
                                )

            # Clean trailing separators from columns
            while raw_columns and raw_columns[-1] == "---":
                raw_columns.pop()

            num_chars_cols = sum(1 for c in raw_columns if c != "---")
            num_sep_cols = sum(1 for c in raw_columns if c == "---")
            default_r_width = min(
                max(num_chars_cols * 0.28 + num_sep_cols * 0.18 + 0.40, 1.4), 3.4
            )  # inches
            default_l_ratio = round(1.0 - (default_r_width / 7.66), 2)

            # Construct explicit pages array (1 page per lesson by default)
            is_table_lesson = any(item.get("is_table_row") for item in vocab_items)
            page_dict = {
                "page_index": 1,
                "reading_title": reading_title,
                "reading_columns": raw_columns,
                "vocab_subtitle": vocab_subtitle,
                "vocab_font_size": "small",
                "vocab_item_sep": "2.5pt",
                "vocab_cjk_font_size": "14pt",
                "reading_cjk_font_size": "14pt",
                "column_ratio": default_l_ratio,
                "is_table_page": is_table_lesson,
                "vocab": vocab_items,
            }

            # Preserve existing user configs if present
            if lesson_num in existing_data and 1 in existing_data[lesson_num]:
                old_p = existing_data[lesson_num][1]
                for key in [
                    "vocab_font_size",
                    "vocab_item_sep",
                    "vocab_cjk_font_size",
                    "reading_cjk_font_size",
                    "column_ratio",
                ]:
                    if key in old_p:
                        page_dict[key] = old_p[key]

            pages = [page_dict]

            lessons_data.append(
                {
                    "lesson_number": lesson_num,
                    "lesson_title": lesson_title,
                    "reading_title": reading_title,
                    "reading_columns": raw_columns,
                    "vocab_subtitle": vocab_subtitle,
                    "is_table_lesson": is_table_lesson,
                    "pages": pages,
                }
            )

    output_doc = {
        "title": "Classical Chinese for Everyone: Study Sheets",
        "author": "Bryan W. van Norden",
        "global_reading_row_spacing": old_global_spacing,
        "lessons": lessons_data,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output_doc, f, ensure_ascii=False, indent=2)

    print(f"[✓] Successfully extracted {len(lessons_data)} lessons to {DATA_FILE}")
    return output_doc


def format_vocab_text(text: str, is_footnote: bool = False) -> str:
    """Escapes text for LaTeX and wraps all CJK characters in \vocabChar{...} or \footnoteChar{...}."""
    if not text:
        return ""
    escaped = latex_escape(text)
    macro = "footnoteChar" if is_footnote else "vocabChar"
    # Wrap all contiguous CJK unified ideographs with \<macro>{...}
    # If the characters are enclosed in parentheses (e.g. `(习)`), include the parentheses inside the macro
    formatted = re.sub(
        r"(\()([\u4e00-\u9fff\u3400-\u4dbf]+)(\))|([\u4e00-\u9fff\u3400-\u4dbf]+)",
        lambda m: (
            rf"\{macro}{{({m.group(2)})}}"
            if m.group(2)
            else rf"\{macro}{{{m.group(4)}}}"
        ),
        escaped,
    )

    return formatted


def format_footnote_text(text: str) -> str:
    """Escapes footnote text for LaTeX and wraps all CJK characters in \footnoteChar{...}."""
    return format_vocab_text(text, is_footnote=True)


def render_latex(data_file: str, output_tex: str, layout: str = "table"):
    """Render intermediate JSON data to a complete master LaTeX document."""
    if not os.path.exists(data_file):
        raise FileNotFoundError(
            f"Data file not found: {data_file}. Run 'extract' first."
        )

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    global_reading_row_spacing = data.get("global_reading_row_spacing", "4pt")

    tex_lines = []
    tex_lines.append(r"\documentclass[10pt,letterpaper]{article}")
    tex_lines.append(
        r"\usepackage[margin=0.42in,footskip=0.2in,top=0.38in,bottom=0.38in]{geometry}"
    )
    if layout == "vertical":
        tex_lines.append(r"\usepackage{luatexja}")
        tex_lines.append(r"\usepackage{luatexja-fontspec}")
        tex_lines.append(r"\usepackage{lltjext}")
    else:
        tex_lines.append(r"\usepackage{fontspec}")
        tex_lines.append(r"\usepackage{xeCJK}")
    tex_lines.append(r"\usepackage{calc}")
    tex_lines.append(r"\usepackage{paracol}")
    tex_lines.append(r"\usepackage{tcolorbox}")
    tex_lines.append(r"\usepackage{enumitem}")
    tex_lines.append(r"\usepackage{tabularx}")
    tex_lines.append(r"\usepackage{array}")
    tex_lines.append(r"\usepackage{fancyhdr}")
    tex_lines.append("")

    # Configure exact publisher fonts extracted from EPUB
    tex_lines.append(r"% Configure Publisher Fonts")
    tex_lines.append(r"\setmainfont{CharisSIL.ttf}[")
    tex_lines.append(r"  Path = fonts/,")
    tex_lines.append(r"  BoldFont = CharisSIL-Bold.ttf,")
    tex_lines.append(r"  ItalicFont = CharisSIL.ttf,")
    tex_lines.append(r"  ItalicFeatures = {FakeSlant=0.2},")
    tex_lines.append(r"  BoldItalicFont = CharisSIL-Bold.ttf,")
    tex_lines.append(r"  BoldItalicFeatures = {FakeSlant=0.2}")
    tex_lines.append(r"]")

    if layout == "vertical":
        tex_lines.append(r"\setmainjfont{SimSun.ttf}[")
        tex_lines.append(r"  Path = fonts/,")
        tex_lines.append(r"  Scale = 1.0,")
        tex_lines.append(r"  TateFont = {SimSun.ttf},")
        tex_lines.append(r"  TateFeatures = {JFM = {zh_TW/{quanjiao,vert}}}")
        tex_lines.append(r"]")
    else:
        tex_lines.append(r"\setCJKmainfont{SimSun.ttf}[")
        tex_lines.append(r"  Path = fonts/")
        tex_lines.append(r"]")
    tex_lines.append("")

    # Page styles
    tex_lines.append(r"\pagestyle{fancy}")
    tex_lines.append(r"\fancyhf{}")
    tex_lines.append(r"\renewcommand{\headrulewidth}{0pt}")
    tex_lines.append(r"\rfoot{\small\textit{Revision 2026-09-03}}")
    tex_lines.append(r"\setlength{\parindent}{0pt}")
    tex_lines.append(r"\setlength{\parskip}{0pt}")
    tex_lines.append(r"\linespread{1.08}")
    tex_lines.append("")

    # Custom environments and styles
    tex_lines.append(r"% Custom styles")
    tex_lines.append(r"\newcommand{\readingCJKSize}{14pt}")
    tex_lines.append(r"\newcommand{\readingCJKLead}{17pt}")
    if layout != "vertical":
        tex_lines.append(r"\newcommand{\readingPuncSize}{9pt}")
        tex_lines.append(r"\newcommand{\readingPuncLead}{11pt}")
        tex_lines.append(
            r"\newcommand{\readingChar}[1]{{\fontsize{\readingCJKSize}{\readingCJKLead}\selectfont #1}}"
        )
        tex_lines.append(
            r"\newcommand{\readingPunc}[1]{\raisebox{0.15em}{{\fontsize{\readingPuncSize}{\readingPuncLead}\selectfont #1}}}"
        )
    tex_lines.append(r"\newcommand{\vocabCJKSize}{14pt}")
    tex_lines.append(r"\newcommand{\vocabCJKLead}{17pt}")
    tex_lines.append(r"\newcommand{\footnoteCJKSize}{10.5pt}")
    tex_lines.append(r"\newcommand{\footnoteCJKLead}{13pt}")
    tex_lines.append(
        r"\newcommand{\vocabChar}[1]{\textbf{{\fontsize{\vocabCJKSize}{\vocabCJKLead}\selectfont #1}}}"
    )
    tex_lines.append(
        r"\newcommand{\footnoteChar}[1]{\textbf{{\fontsize{\footnoteCJKSize}{\footnoteCJKLead}\selectfont #1}}}"
    )

    if layout != "vertical":
        tex_lines.append(
            r"\newcommand{\cjkvertchar}[1]{\makebox[\readingCJKSize][c]{#1}}"
        )
    tex_lines.append(r"\newcommand{\stroketag}[1]{{\scriptsize\color{gray} #1}}")
    tex_lines.append("")

    tex_lines.append(r"\begin{document}")

    total_pages = 0
    lessons = data.get("lessons", [])

    for l_idx, lesson in enumerate(lessons):
        lesson_title = latex_escape(
            lesson.get("lesson_title", f"Lesson {lesson.get('lesson_number')}")
        )
        pages = lesson.get("pages", [])

        for p_idx, page in enumerate(pages):
            total_pages += 1
            if total_pages > 1:
                tex_lines.append(r"")
                tex_lines.append(r"\newpage")
                tex_lines.append(r"")
                tex_lines.append(r"%%%%%%%%%%%%%%%%%%%%%%%%%")
                tex_lines.append(r"% START Lesson " + str(lesson.get("lesson_number")))
                tex_lines.append(r"%%%%%%%%%%%%%%%%%%%%%%%%%")
                tex_lines.append(r"")

            reading_title = latex_escape(page.get("reading_title", ""))
            vocab_subtitle = latex_escape(page.get("vocab_subtitle", ""))
            vocab_list = page.get("vocab", [])
            reading_cols = page.get("reading_columns", [])

            # Header banner
            tex_lines.append(
                r"\begin{tcolorbox}[colback=black!5!white,colframe=black!60!white,boxrule=0.6pt,arc=2pt,left=5pt,right=5pt,top=3pt,bottom=3pt]"
            )
            tex_lines.append(
                r"  \textbf{\large "
                + lesson_title
                + r"} \hfill \textit{\normalsize "
                + reading_title
                + r"}"
            )
            tex_lines.append(r"\end{tcolorbox}")
            tex_lines.append(r"\vspace{-0.2em}")

            # Filter out separator tokens to calculate number of vertical columns
            real_cols = [c for c in reading_cols if c != "---"]
            num_v_cols = max(len(real_cols), 1)

            # Determine column ratio: check user override from page object in lessons_data.json
            col_ratio_val = page.get("column_ratio")
            if col_ratio_val is not None:
                try:
                    l_col_ratio = f"{float(col_ratio_val):.2f}"
                except (ValueError, TypeError):
                    l_col_ratio = str(col_ratio_val)
            else:
                num_chars_cols = sum(1 for c in reading_cols if c != "---")
                num_sep_cols = sum(1 for c in reading_cols if c == "---")
                r_col_width = min(
                    max(num_chars_cols * 0.28 + num_sep_cols * 0.18 + 0.40, 1.4), 3.4
                )
                l_col_ratio = f"{1.0 - (r_col_width / 7.66):.2f}"

            # Read user-configurable formatting variables from page
            vocab_font_size_name = page.get("vocab_font_size", "small").lstrip("\\")
            vocab_font_cmd = f"\\{vocab_font_size_name}"
            vocab_item_sep = page.get("vocab_item_sep", "2.5pt")
            vocab_cjk_size = page.get("vocab_cjk_font_size", "14pt")

            cjk_pt_match = re.search(r"(\d+)", str(vocab_cjk_size))
            if cjk_pt_match:
                pt_val = int(cjk_pt_match.group(1))
                lead_val = int(pt_val * 1.22)
                fn_pt = round(pt_val * 0.75, 1)
                fn_pt_str = f"{int(fn_pt)}pt" if fn_pt.is_integer() else f"{fn_pt}pt"
                fn_lead = round(fn_pt * 1.22, 1)
                fn_lead_str = (
                    f"{int(fn_lead)}pt" if fn_lead.is_integer() else f"{fn_lead}pt"
                )
                tex_lines.append(
                    r"\renewcommand{\vocabCJKSize}{" + f"{pt_val}pt" + r"}"
                )
                tex_lines.append(
                    r"\renewcommand{\vocabCJKLead}{" + f"{lead_val}pt" + r"}"
                )
                tex_lines.append(r"\renewcommand{\footnoteCJKSize}{" + fn_pt_str + r"}")
                tex_lines.append(
                    r"\renewcommand{\footnoteCJKLead}{" + fn_lead_str + r"}"
                )
            else:
                tex_lines.append(r"\renewcommand{\vocabCJKSize}{14pt}")
                tex_lines.append(r"\renewcommand{\vocabCJKLead}{17pt}")
                tex_lines.append(r"\renewcommand{\footnoteCJKSize}{10.5pt}")
                tex_lines.append(r"\renewcommand{\footnoteCJKLead}{13pt}")

            reading_cjk_size = page.get("reading_cjk_font_size", "14pt")
            read_pt_match = re.search(r"(\d+)", str(reading_cjk_size))
            if read_pt_match:
                r_pt = int(read_pt_match.group(1))
                r_lead = int(r_pt * 1.22)
                tex_lines.append(
                    r"\renewcommand{\readingCJKSize}{" + f"{r_pt}pt" + r"}"
                )
                tex_lines.append(
                    r"\renewcommand{\readingCJKLead}{" + f"{r_lead}pt" + r"}"
                )
                if layout != "vertical":
                    p_pt = max(int(r_pt * 0.65), 5)
                    p_lead = int(p_pt * 1.22)
                    tex_lines.append(
                        r"\renewcommand{\readingPuncSize}{" + f"{p_pt}pt" + r"}"
                    )
                    tex_lines.append(
                        r"\renewcommand{\readingPuncLead}{" + f"{p_lead}pt" + r"}"
                    )
            else:
                tex_lines.append(r"\renewcommand{\readingCJKSize}{14pt}")
                tex_lines.append(r"\renewcommand{\readingCJKLead}{17pt}")
                if layout != "vertical":
                    tex_lines.append(r"\renewcommand{\readingPuncSize}{9pt}")
                    tex_lines.append(r"\renewcommand{\readingPuncLead}{11pt}")

            tex_lines.append(r"\columnratio{" + l_col_ratio + r"}")
            # tex_lines.append(r"\setlength{\columnsep}{0.20in}")
            tex_lines.append(r"\setlength{\columnsep}{0.10in}")
            tex_lines.append(r"\begin{paracol}{2}")

            # --- Left Column: Vocabulary ---
            tex_lines.append(r"% ---")
            tex_lines.append(r"% --- Left Column: Vocabulary ---")
            tex_lines.append(
                r"\begin{tcolorbox}[colback=white,colframe=black!30!white,boxrule=0.4pt,arc=1pt,left=3pt,right=3pt,top=4pt,bottom=4pt,height=\textheight-0.7in]"
            )
            tex_lines.append(r"\renewcommand{\thempfootnote}{\arabic{mpfootnote}}")
            if vocab_subtitle:
                tex_lines.append(
                    r"\textbf{\small "
                    + latex_escape("Vocabulary")
                    + r"} \hfill \textit{\footnotesize "
                    + vocab_subtitle
                    + r"}"
                )
                tex_lines.append(r"\vspace{0.3em}\hrule\vspace{0.4em}")
            else:
                tex_lines.append(r"\textbf{\small " + latex_escape("Vocabulary") + r"}")
                tex_lines.append(r"\vspace{0.3em}\hrule\vspace{0.4em}")

            if page.get("is_table_page"):
                # Render exact textbook table using tabularx with clean proportional widths
                tex_lines.append(r"\vspace{-0.2em}")
                tex_lines.append(r"\renewcommand{\tabularxcolumn}[1]{m{#1}}")
                tex_lines.append(r"\renewcommand{\arraystretch}{0.85}")
                tex_lines.append(
                    r"\noindent\begin{tabularx}{\linewidth}{|>{\raggedright\arraybackslash}m{0.60in}|>{\raggedright\arraybackslash}m{0.55in}|>{\raggedright\arraybackslash}m{0.56in}|>{\raggedright\arraybackslash}X|}"
                )
                tex_lines.append(r"\hline")
                tex_lines.append(
                    r"\textbf{"
                    + vocab_font_cmd
                    + r" Character} & \textbf{"
                    + vocab_font_cmd
                    + r" Hint} & \textbf{"
                    + vocab_font_cmd
                    + r" Pronun\-ciation} & \textbf{"
                    + vocab_font_cmd
                    + r" Relevant Meaning} \\"
                )
                tex_lines.append(r"\hline")
                table_footnotes = []
                for item in vocab_list:
                    c_cell = item.get("character", "")
                    h_cell = latex_escape(item.get("hint", ""))
                    p_cell = latex_escape(item.get("pronunciation", ""))
                    m_cell = format_vocab_text(item.get("meaning", ""))
                    footnotes = item.get("footnotes", [])
                    for fn in footnotes:
                        table_footnotes.append(fn)
                        fn_idx = len(table_footnotes)
                        m_cell += r"\textsuperscript{" + str(fn_idx) + r"}"

                    c_fmt = format_vocab_text(c_cell)
                    raw_meaning = item.get("meaning", "")
                    raw_hint = item.get("hint", "")
                    if len(raw_meaning) < 40 and len(raw_hint) < 25:
                        c_fmt += r" \rule[-1.5ex]{0pt}{4.5ex}"

                    row_tex = f"{c_fmt} & {vocab_font_cmd} {h_cell} & {vocab_font_cmd} {p_cell} & {vocab_font_cmd} {m_cell} \\\\"
                    tex_lines.append(r"  " + row_tex)
                    tex_lines.append(r"\hline")
                tex_lines.append(r"\end{tabularx}")
                if table_footnotes:
                    tex_lines.append(r"\vspace{0.4em}\hrule\vspace{0.3em}")
                    for idx, fn in enumerate(table_footnotes, start=1):
                        tex_lines.append(
                            r"\noindent\footnotesize\textsuperscript{"
                            + str(idx)
                            + r"}"
                            + format_footnote_text(fn)
                            + r"\par"
                        )
            else:
                # Vocabulary items list - user-configured font size and itemsep
                tex_lines.append(
                    r"\begin{itemize}[leftmargin=*,itemsep="
                    + vocab_item_sep
                    + r",parsep=0pt,topsep=0pt]"
                )
                for item in vocab_list:
                    v_text = item.get("text", "")
                    stroke_tag = item.get("stroke_tag", "")
                    footnotes = item.get("footnotes", [])

                    fmt_line = format_vocab_text(v_text)
                    for fn in footnotes:
                        fmt_line += r"\footnote{" + format_footnote_text(fn) + r"}"

                    if stroke_tag:
                        fmt_line += r" \stroketag{" + latex_escape(stroke_tag) + r"}"

                    tex_lines.append(r"  \item " + vocab_font_cmd + " " + fmt_line)
                tex_lines.append(r"\end{itemize}")
            tex_lines.append(r"\end{tcolorbox}")

            # Switch to right column
            tex_lines.append(r"\switchcolumn")

            # --- Right Column: Vertical Reading Text ---
            tex_lines.append(r"% ---")
            tex_lines.append(r"% --- Right Column: Vertical Reading Text ---")
            tex_lines.append(
                r"\begin{tcolorbox}[colback=black!2!white,colframe=black!40!white,boxrule=0.4pt,arc=1pt,left=2pt,right=2pt,top=4pt,bottom=4pt,height=\textheight-0.7in]"
            )
            tex_lines.append(r"\centering")
            tex_lines.append(r"\textbf{\small " + latex_escape("Reading") + r"}")
            tex_lines.append(r"\vspace{0.3em}\hrule\vspace{0.5em}")
            tex_lines.append(r"\vspace*{\fill}")

            # Group reading columns into excerpt blocks separated by '---'
            blocks = []
            curr_block = []
            for c in reading_cols:
                if c == "---":
                    if curr_block:
                        blocks.append(curr_block)
                        curr_block = []
                else:
                    curr_block.append(c)
            if curr_block:
                blocks.append(curr_block)

            if layout == "vertical":
                tex_lines.append(
                    r"\begin{minipage}<t>[c][][t]{\dimexpr\textheight-0.95in\relax}"
                )
                tex_lines.append(
                    r"  \fontsize{\readingCJKSize}{\readingCJKLead}\selectfont"
                )
                tex_lines.append(r"  \setlength{\parindent}{0pt}")
                tex_lines.append(r"  \setlength{\parskip}{0pt}")
                tex_lines.append(r"  \ltjsetparameter{kanjiskip=1.8pt}")

                for b_idx, block in enumerate(blocks):
                    if b_idx > 0:
                        tex_lines.append(r"  \vspace{0.8em}")
                    for col_str in block:

                        def _replace_space_gap(match):
                            n = len(match.group(0))
                            return f"\\hspace{{{n * 0.65:.2f}em}}"

                        formatted_col = re.sub(r" +", _replace_space_gap, col_str)
                        tex_lines.append(r"  " + formatted_col + r"\par")

                tex_lines.append(r"\end{minipage}")
            else:
                tex_lines.append(r"\setlength{\tabcolsep}{4pt}")

                # Typeset vertical columns in LaTeX tabular

                # Right-to-Left: Excerpt 0 is on the far right, Excerpt N-1 on the far left
                # Within each excerpt, Column 0 is on the right, Column K-1 on the left
                display_blocks = []
                for blk in reversed(blocks):
                    display_blocks.append(list(reversed(blk)))

                # Column specs: natural column spacing between columns, with additional 2.4em between excerpts
                block_specs = [" ".join(["c" for _ in blk]) for blk in display_blocks]
                col_specs = r" @{\hspace{2\tabcolsep + 2.4em}} ".join(block_specs)

                # Flatten columns from left to right for row rendering
                flat_display_cols = []
                for blk in display_blocks:
                    for col_str in blk:
                        flat_display_cols.append([ch for ch in col_str])

                tex_lines.append(r"\begin{tabular}{" + col_specs + r"}")

                max_rows = max([len(c) for c in flat_display_cols], default=1)

                for row_idx in range(max_rows):
                    row_cells = []
                    for col_idx in range(len(flat_display_cols)):
                        char_list = flat_display_cols[col_idx]
                        if row_idx < len(char_list):
                            ch = char_list[row_idx]
                            if ch == "。":
                                cell_tex = r"\cjkvertchar{\readingPunc{。}}"
                            elif ch in ["，", ","]:
                                cell_tex = r"\cjkvertchar{\readingPunc{，}}"
                            else:
                                cell_tex = r"\cjkvertchar{\readingChar{" + ch + r"}}"
                        else:
                            cell_tex = r"\cjkvertchar{}"
                        row_cells.append(cell_tex)
                    tex_lines.append(
                        "  "
                        + " & ".join(row_cells)
                        + r" \\["
                        + global_reading_row_spacing
                        + r"]"
                    )

                tex_lines.append(r"\end{tabular}")
            tex_lines.append(r"\vspace*{\fill}")
            tex_lines.append(r"\end{tcolorbox}")

            tex_lines.append(r"\end{paracol}")

    tex_lines.append(r"\end{document}")

    with open(output_tex, "w", encoding="utf-8") as f:
        f.write("\n".join(tex_lines))

    print(f"[✓] Rendered master LaTeX document to {output_tex}")


def detect_latex_engine(tex_path: str) -> str:
    """Detect the required TeX engine ('lualatex' or 'xelatex') by inspecting the preamble."""
    with open(tex_path, "r", encoding="utf-8") as f:
        head = f.read(2000)
    if r"\usepackage{luatexja}" in head:
        return "lualatex"
    return "xelatex"


def compile_latex(tex_path: str):
    """Compile LaTeX document to PDF via xelatex or lualatex (auto-detected)."""
    if not os.path.exists(tex_path):
        raise FileNotFoundError(
            f"LaTeX file not found: {tex_path}. Run 'render' first."
        )

    work_dir = os.path.dirname(os.path.abspath(tex_path))
    base_name = os.path.basename(tex_path)

    engine = detect_latex_engine(tex_path)
    engine_label = "LuaLaTeX" if engine == "lualatex" else "XeLaTeX"

    cmd = [engine, "-interaction=nonstopmode", base_name]
    print(f"[*] Compiling {base_name} with {engine_label}...")

    # Run once
    res1 = subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)
    if res1.returncode != 0:
        print(f"[!] {engine_label} compilation error output:")
        print(res1.stdout[-1500:] if len(res1.stdout) > 1500 else res1.stdout)
        raise RuntimeError(f"{engine_label} failed to compile the document.")

    # Run second time for layout stabilization
    subprocess.run(cmd, cwd=work_dir, capture_output=True, text=True)

    out_pdf = os.path.splitext(tex_path)[0] + ".pdf"
    if os.path.exists(out_pdf):
        print(f"[✓] Successfully generated PDF: {out_pdf}")
    else:
        print(f"[!] Compilation finished but {out_pdf} was not found.")


def extract_reading_titles(title: str, num_excerpts: int) -> list[str]:
    """Extract individual excerpt titles from a lesson's reading_title."""
    cleaned = re.sub(r"^\d+\.\d+\.\s*Readings?:\s*", "", title).strip()
    if num_excerpts <= 1:
        return [cleaned]
    if ":" in cleaned:
        cleaned = cleaned.split(":", 1)[1].strip()
    cleaned = cleaned.replace("Analects, 15.24", "Analects 15.24")
    placeholder = "___CLASSIC_WAY_VIRTUE___"
    temp = cleaned.replace("Classic of the Way and Virtue", placeholder)
    parts = re.split(r",\s*(?:and\s+)?|\s+and\s+", temp)
    parts = [
        p.replace(placeholder, "Classic of the Way and Virtue").strip()
        for p in parts
        if p.strip()
    ]
    if len(parts) == num_excerpts:
        return parts
    return [f"{cleaned} (Part {i+1})" for i in range(num_excerpts)]


def export_readings(data_file: str = DATA_FILE, output_file: str = READINGS_MD):
    """Export readings from the top-level reading_columns of each lesson as Markdown."""
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    lines = []
    for lesson in data.get("lessons", []):
        cols = lesson.get("reading_columns", [])
        if not cols:
            continue

        excerpts = []
        curr = []
        for c in cols:
            if c == "---":
                if curr:
                    excerpts.append(curr)
                    curr = []
            else:
                curr.append(c)
        if curr:
            excerpts.append(curr)

        if not excerpts:
            continue

        lesson_title = lesson.get(
            "lesson_title", f"Lesson {lesson.get('lesson_number', '')}"
        ).strip()
        lines.append(f"## {lesson_title}")
        lines.append("")

        titles = extract_reading_titles(lesson.get("reading_title", ""), len(excerpts))

        for title, exc in zip(titles, excerpts):
            lines.append(f"### {title}")
            lines.append("")
            text = "".join(exc)
            text = re.sub(r" +", " ", text).strip()
            lines.append(text)
            lines.append("")

    content = "\n".join(lines).strip() + "\n"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[✓] Exported readings to {output_file}")


def generate_worksheets(
    data_file: str = DATA_FILE,
    lesson_filter: list[int] | None = None,
    worksheets_dir: str = WORKSHEETS_DIR,
    guide: str = "star",
    stroke_order_color: str = "black",
    save_info: bool = True,
    info_only: bool = False,
    sheet_only: bool = False,
    force_info: bool = False,
    hide_name_score: bool = False,
    character_guide_color: str | None = None,
) -> None:
    """
    Generate stroke-order practice worksheets (PDF) for lessons in data_file.

    Workflow per lesson:
      1. Parse vocab items into characters and multi-character words with their
         corresponding textbook pinyin and definitions.
      2. If JSON info files already exist in worksheets_dir (and not force_info),
         use them directly so user adjustments are preserved.
      3. Otherwise, call `chinese-worksheet-generator --characters ... --info` to generate
         stroke-order path data and radicals from makemeahanzi.
      4. Patch character_infos.json and word_infos.json with the textbook's
         pinyin, definition, and traditional character shapes.
      5. Save `lesson_NN_character_infos.json` (and `lesson_NN_word_infos.json`) to
         worksheets_dir for user inspection / editing if save_info is True.
      6. Unless info_only, call `chinese-worksheet-generator --title ... --guide ... --sheet`
         to render the final PDF.
      7. Move sheet.pdf to worksheets_dir/lesson_{N:02d}.pdf and clean up temp files.
    """
    if not os.path.exists(data_file):
        print(
            f"[!] Error: Data file not found: {data_file}. Run 'extract' first.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not os.path.isdir(WORKSHEET_GENERATOR_DIR):
        print(
            f"[!] Error: Worksheet generator directory not found at: {WORKSHEET_GENERATOR_DIR}",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(worksheets_dir, exist_ok=True)

    with open(data_file, "r", encoding="utf-8") as f:
        doc = json.load(f)

    lessons = doc.get("lessons", [])
    if lesson_filter:
        lessons = [l for l in lessons if l.get("lesson_number") in lesson_filter]
        if not lessons:
            print(
                f"[!] Warning: No lessons found matching filter {lesson_filter}.",
                file=sys.stderr,
            )
            return

    CJK_CHAR = r"[\u4e00-\u9fff\u3400-\u4dbf]"
    VOCAB_LINE_RE = re.compile(
        r"^(?P<trad>" + CJK_CHAR + r"+)"
        r"(?:\s+or\s+" + CJK_CHAR + r"+)?"
        r"(?:\s+\((?P<simp>" + CJK_CHAR + r"+)\))?"
        r"\s+(?P<pinyin>\S+)"
        r"\s+(?P<defn>.+)$",
        re.DOTALL,
    )

    # Variant fallback map for rare ancient CJK characters missing in makemeahanzi
    VARIANTS_MAP = {"鯈": "鲦"}

    # Attempt to load makemeahanzi dataset to pre-check character existence
    makemeahanzi_chars = set()
    graphics_txt = os.path.join(WORKSHEET_GENERATOR_DIR, "makemeahanzi", "graphics.txt")
    if not os.path.exists(graphics_txt):
        alt_graphics = os.path.expanduser("~/.local/share/makemeahanzi/graphics.txt")
        if os.path.exists(alt_graphics):
            graphics_txt = alt_graphics

    if os.path.exists(graphics_txt):
        try:
            with open(graphics_txt, "r", encoding="utf-8") as gf:
                for line in gf:
                    if line.startswith('{"character":'):
                        try:
                            item = json.loads(line)
                            makemeahanzi_chars.add(item.get("character"))
                        except Exception:
                            pass
        except Exception:
            pass

    def check_char_available(char_to_check: str) -> bool:
        if not makemeahanzi_chars:
            return True
        return char_to_check in makemeahanzi_chars

    # Helper to format definitions into comma-separated chunks for reportlab text width limits
    def sanitize_definition(defn: str, max_chunk: int = 24) -> str:
        if not defn:
            return ""
        defn = " ".join(defn.split())
        segments = [s.strip() for s in defn.replace(";", ",").split(",") if s.strip()]
        sanitized = []
        for s in segments:
            words = s.split(" ")
            curr = []
            curr_len = 0
            for w in words:
                if curr_len + len(w) + 1 > max_chunk and curr:
                    sanitized.append(" ".join(curr))
                    curr = [w]
                    curr_len = len(w)
                else:
                    curr.append(w)
                    curr_len += len(w) + 1
            if curr:
                sanitized.append(" ".join(curr))
        return ", ".join(sanitized)

    total_lessons = len(lessons)
    generated_count = 0

    for lesson in lessons:
        lesson_num = lesson.get("lesson_number", 1)
        lesson_title = lesson.get("lesson_title", f"Lesson {lesson_num}")
        print(f"[*] Processing {lesson_title} (Lesson {lesson_num})...")

        dst_char_info = os.path.join(
            worksheets_dir, f"lesson_{lesson_num:02d}_character_infos.json"
        )
        dst_word_info = os.path.join(
            worksheets_dir, f"lesson_{lesson_num:02d}_word_infos.json"
        )
        dst_pdf = os.path.join(worksheets_dir, f"lesson_{lesson_num:02d}.pdf")

        # Check if we can render from existing JSON info files directly
        use_existing = sheet_only or (
            os.path.exists(dst_char_info) and not force_info and not info_only
        )

        if use_existing:
            if not os.path.exists(dst_char_info):
                print(
                    f"  [!] Error: {dst_char_info} not found for --sheet-only mode.",
                    file=sys.stderr,
                )
                continue
            print(f"  [*] Using existing {os.path.basename(dst_char_info)}...")
            shutil.copy(
                dst_char_info,
                os.path.join(WORKSHEET_GENERATOR_DIR, "character_infos.json"),
            )
            if os.path.exists(dst_word_info) and os.path.getsize(dst_word_info) > 0:
                shutil.copy(
                    dst_word_info,
                    os.path.join(WORKSHEET_GENERATOR_DIR, "word_infos.json"),
                )
            else:
                with open(
                    os.path.join(WORKSHEET_GENERATOR_DIR, "word_infos.json"),
                    "w",
                    encoding="utf-8",
                ) as wf:
                    pass

            sheet_title = f"{lesson_title} Vocab"[:20]
            cmd_sheet = [
                "uv",
                "run",
                "chinese-worksheet-generator",
                "--title",
                sheet_title,
                "--guide",
                guide,
                "--stroke-order-color",
                stroke_order_color,
                "--sheet",
            ]
            if hide_name_score:
                cmd_sheet.append("--hide-name-score")
            if character_guide_color:
                cmd_sheet.extend(["--character-guide-color", character_guide_color])
            res_sheet = subprocess.run(
                cmd_sheet,
                cwd=WORKSHEET_GENERATOR_DIR,
                capture_output=True,
                text=True,
            )
            if res_sheet.returncode != 0:
                print(
                    f"  [!] Error rendering sheet for Lesson {lesson_num}:\n{res_sheet.stderr.strip()}",
                    file=sys.stderr,
                )
                continue

            src_pdf = os.path.join(WORKSHEET_GENERATOR_DIR, "sheet.pdf")
            if os.path.exists(src_pdf):
                shutil.copy(src_pdf, dst_pdf)
                print(f"  [✓] Generated {dst_pdf}")
                generated_count += 1
            else:
                print(
                    f"  [!] Expected {src_pdf} not found after rendering.",
                    file=sys.stderr,
                )

            for fname in ["character_infos.json", "word_infos.json", "sheet.pdf"]:
                p = os.path.join(WORKSHEET_GENERATOR_DIR, fname)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            continue

        # Otherwise, parse vocab and generate info from scratch
        vocab_tuples = []
        for page in lesson.get("pages", []):
            for v in page.get("vocab", []):
                if v.get("is_table_row"):
                    raw_char = v.get("character", "").strip()
                    pinyin_str = v.get("pronunciation", "").strip()
                    defn_str = v.get("meaning", "").strip()
                    m = re.match(
                        r"^(" + CJK_CHAR + r"[\s" + CJK_CHAR[1:] + r"*)"
                        r"(?:\s+\((" + CJK_CHAR + r"[\s" + CJK_CHAR[1:] + r"*)\))?$",
                        raw_char,
                    )
                    if m:
                        trad = "".join(m.group(1).split())
                        simp = "".join(m.group(2).split()) if m.group(2) else ""
                        if trad:
                            vocab_tuples.append((trad, simp, pinyin_str, defn_str))
                    else:
                        print(
                            f"  [!] Skipped unparseable table row: {raw_char!r}",
                            file=sys.stderr,
                        )
                else:
                    text = v.get("text", "").strip()
                    m = VOCAB_LINE_RE.match(text)
                    if m:
                        trad = m.group("trad")
                        simp = m.group("simp") or ""
                        pinyin = m.group("pinyin")
                        defn = m.group("defn")
                        vocab_tuples.append((trad, simp, pinyin, defn))
                    else:
                        print(
                            f"  [!] Skipped unparseable vocab line: {text[:60]!r}",
                            file=sys.stderr,
                        )

        if not vocab_tuples:
            print(f"  [!] No vocab found for Lesson {lesson_num}, skipping.")
            continue

        char_lookup = {}
        word_lookup = {}
        seen_words = set()
        char_tokens = []
        char_idx = 0

        for trad, simp, pinyin, defn in vocab_tuples:
            if trad in seen_words:
                continue
            seen_words.add(trad)

            sani_defn = sanitize_definition(defn)

            if len(trad) == 1:
                gen_c = trad
                if not check_char_available(trad):
                    if simp and check_char_available(simp):
                        gen_c = simp
                    elif trad in VARIANTS_MAP and check_char_available(
                        VARIANTS_MAP[trad]
                    ):
                        gen_c = VARIANTS_MAP[trad]
                    else:
                        print(
                            f"  [!] Warning: '{trad}' not found in stroke database, will attempt generation.",
                            file=sys.stderr,
                        )

                char_tokens.append(gen_c)
                char_lookup[gen_c] = {
                    "display_char": trad,
                    "pinyin": [pinyin] if pinyin else [],
                    "definition": sani_defn,
                }
                char_idx += 1
            else:
                beg_idx = char_idx
                end_idx = char_idx + len(trad) - 1
                word_lookup[(beg_idx, end_idx)] = [
                    s.strip()
                    for s in sanitize_definition(defn, max_chunk=12).split(",")
                    if s.strip()
                ]

                gen_word = []
                syllables = pinyin.split() if pinyin else []
                for i, c in enumerate(trad):
                    gen_c = c
                    if not check_char_available(c):
                        if simp and i < len(simp) and check_char_available(simp[i]):
                            gen_c = simp[i]
                        elif c in VARIANTS_MAP and check_char_available(
                            VARIANTS_MAP[c]
                        ):
                            gen_c = VARIANTS_MAP[c]
                        else:
                            print(
                                f"  [!] Warning: '{c}' not found in stroke database, will attempt generation.",
                                file=sys.stderr,
                            )
                    gen_word.append(gen_c)

                    syl = syllables[i] if i < len(syllables) else pinyin
                    if gen_c not in char_lookup:
                        char_lookup[gen_c] = {
                            "display_char": c,
                            "pinyin": [syl] if syl else [],
                            "definition": sani_defn,
                        }
                    char_idx += 1
                char_tokens.append("(" + "".join(gen_word) + ")")

        char_arg = "".join(char_tokens)
        if not char_arg:
            print(f"  [!] No valid characters for Lesson {lesson_num}, skipping.")
            continue

        # Clean up any leftover artefacts before running
        for fname in ["character_infos.json", "word_infos.json", "sheet.pdf"]:
            p = os.path.join(WORKSHEET_GENERATOR_DIR, fname)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

        # 1. Run info step
        cmd_info = [
            "uv",
            "run",
            "chinese-worksheet-generator",
            "--characters",
            char_arg,
            "--info",
        ]
        res_info = subprocess.run(
            cmd_info,
            cwd=WORKSHEET_GENERATOR_DIR,
            capture_output=True,
            text=True,
        )
        if res_info.returncode != 0:
            print(
                f"  [!] Error generating info for Lesson {lesson_num}:\n{res_info.stderr.strip()}",
                file=sys.stderr,
            )
            continue

        # 2. Patch character_infos.json
        char_info_path = os.path.join(WORKSHEET_GENERATOR_DIR, "character_infos.json")
        if os.path.exists(char_info_path):
            patched_lines = []
            with open(char_info_path, "r", encoding="utf-8") as cf:
                for line in cf:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    c = obj.get("character")
                    if c in char_lookup:
                        if char_lookup[c].get("definition"):
                            obj["definition"] = char_lookup[c]["definition"]
                        if char_lookup[c].get("pinyin"):
                            obj["pinyin"] = char_lookup[c]["pinyin"]
                        obj["character"] = char_lookup[c]["display_char"]
                    patched_lines.append(json.dumps(obj, ensure_ascii=False))

            with open(char_info_path, "w", encoding="utf-8") as cf:
                if patched_lines:
                    cf.write("\n".join(patched_lines) + "\n")
                else:
                    cf.write("")

        # 2b. Patch word_infos.json
        word_info_path = os.path.join(WORKSHEET_GENERATOR_DIR, "word_infos.json")
        if os.path.exists(word_info_path):
            patched_words = []
            with open(word_info_path, "r", encoding="utf-8") as wf:
                for line in wf:
                    line = line.strip()
                    if not line:
                        continue
                    obj = json.loads(line)
                    key = (
                        obj.get("character_begin_index"),
                        obj.get("character_end_index"),
                    )
                    if key in word_lookup and word_lookup[key]:
                        obj["definition"] = word_lookup[key]
                    else:
                        obj["definition"] = [
                            s.strip()
                            for d in obj.get("definition", [])
                            for s in sanitize_definition(d, max_chunk=12).split(",")
                            if s.strip()
                        ]
                    patched_words.append(json.dumps(obj, ensure_ascii=False))

            with open(word_info_path, "w", encoding="utf-8") as wf:
                if patched_words:
                    wf.write("\n".join(patched_words) + "\n")
                else:
                    wf.write("")

        # Save JSON info files to destination worksheets directory
        if save_info or info_only:
            if os.path.exists(char_info_path):
                shutil.copy(char_info_path, dst_char_info)
            if os.path.exists(word_info_path) and os.path.getsize(word_info_path) > 0:
                shutil.copy(word_info_path, dst_word_info)
            elif os.path.exists(dst_word_info):
                try:
                    os.remove(dst_word_info)
                except Exception:
                    pass

        if info_only:
            print(f"  [✓] Generated intermediate JSON: {dst_char_info}")
            generated_count += 1
            for fname in ["character_infos.json", "word_infos.json", "sheet.pdf"]:
                p = os.path.join(WORKSHEET_GENERATOR_DIR, fname)
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
            continue

        # 3. Run sheet step
        sheet_title = f"{lesson_title} Vocab"[:20]
        cmd_sheet = [
            "uv",
            "run",
            "chinese-worksheet-generator",
            "--title",
            sheet_title,
            "--guide",
            guide,
            "--stroke-order-color",
            stroke_order_color,
            "--sheet",
        ]
        if hide_name_score:
            cmd_sheet.append("--hide-name-score")
        if character_guide_color:
            cmd_sheet.extend(["--character-guide-color", character_guide_color])
        res_sheet = subprocess.run(
            cmd_sheet,
            cwd=WORKSHEET_GENERATOR_DIR,
            capture_output=True,
            text=True,
        )
        if res_sheet.returncode != 0:
            print(
                f"  [!] Error rendering sheet for Lesson {lesson_num}:\n{res_sheet.stderr.strip()}",
                file=sys.stderr,
            )
            continue

        src_pdf = os.path.join(WORKSHEET_GENERATOR_DIR, "sheet.pdf")
        if os.path.exists(src_pdf):
            shutil.copy(src_pdf, dst_pdf)
            print(f"  [✓] Generated {dst_pdf}")
            generated_count += 1
        else:
            print(
                f"  [!] Expected {src_pdf} not found after rendering.",
                file=sys.stderr,
            )

        # Clean up temporary files in generator dir
        for fname in ["character_infos.json", "word_infos.json", "sheet.pdf"]:
            p = os.path.join(WORKSHEET_GENERATOR_DIR, fname)
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception:
                    pass

    mode_str = "JSON info files" if info_only else "worksheets"
    print(
        f"[✓] Worksheet generation complete: {generated_count}/{total_lessons} {mode_str} generated in {worksheets_dir}"
    )


def build_argument_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Classical Chinese Study Sheets Generator"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # extract
    p_extract = subparsers.add_parser(
        "extract", help="Extract raw data and fonts from EPUB to lessons_data.json"
    )
    p_extract.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite existing lessons_data.json",
    )
    p_extract.add_argument(
        "--epub", default=EPUB_PATH, help="Path to textbook EPUB file"
    )

    # render
    p_render = subparsers.add_parser(
        "render", help="Render intermediate JSON to lessons_all.tex"
    )
    p_render.add_argument(
        "--input", "-i", default=DATA_FILE, help="Path to intermediate JSON file"
    )
    p_render.add_argument(
        "--output", "-o", default=TEX_FILE, help="Path to output .tex file"
    )
    p_render.add_argument(
        "--layout",
        choices=["table", "vertical"],
        default="table",
        help="Reading column layout: 'table' (XeLaTeX tabular grid) or 'vertical' (LuaLaTeX native vertical typesetting). Default: table",
    )

    # compile
    p_compile = subparsers.add_parser(
        "compile", help="Compile .tex file to .pdf (auto-detects xelatex or lualatex)"
    )
    p_compile.add_argument("--input", "-i", default=TEX_FILE, help="Path to .tex file")

    # worksheet
    p_worksheet = subparsers.add_parser(
        "worksheet",
        help="Generate stroke-order practice worksheets via chinese-worksheet-generator",
    )
    p_worksheet.add_argument(
        "--lesson",
        "-l",
        type=int,
        action="append",
        dest="lessons",
        metavar="N",
        help="Generate worksheet only for lesson N (repeatable, e.g. -l 1 -l 2; default: all lessons)",
    )
    p_worksheet.add_argument(
        "--input",
        "-i",
        default=DATA_FILE,
        help="Path to lessons_data.json (default: %(default)s)",
    )
    p_worksheet.add_argument(
        "--output-dir",
        "-o",
        default=WORKSHEETS_DIR,
        help="Directory to save generated worksheet PDFs and JSON info files (default: %(default)s)",
    )
    p_worksheet.add_argument(
        "--guide",
        default="star",
        choices=["none", "star", "cross", "cross_star", "character"],
        help="Grid style for practice boxes (default: star)",
    )
    p_worksheet.add_argument(
        "--stroke-order-color",
        default="black",
        help="Color for the stroke order diagrams (default: black)",
    )
    p_worksheet.add_argument(
        "--info-only",
        action="store_true",
        help="Only generate lesson_NN_character_infos.json (and word_infos.json) in output dir without rendering PDFs",
    )
    p_worksheet.add_argument(
        "--sheet-only",
        action="store_true",
        help="Only render PDFs from existing lesson_NN_character_infos.json files in output dir",
    )
    p_worksheet.add_argument(
        "--force-info",
        "-f",
        action="store_true",
        help="Force overwrite existing lesson_NN_character_infos.json files during extraction",
    )
    p_worksheet.add_argument(
        "--no-save-info",
        action="store_false",
        dest="save_info",
        default=True,
        help="Do not save intermediate JSON info files in output directory",
    )
    p_worksheet.add_argument(
        "--hide-name-score",
        action="store_true",
        help="Hide Name and Score fields from the worksheet header",
    )
    p_worksheet.add_argument(
        "--character-guide-color",
        "--character-guide-opacity",
        "--character-opacity",
        dest="character_guide_color",
        default=None,
        help="Color or opacity for character guide outline / upcoming strokes (e.g. 'gray', '0.2', '20%%', '#ccc')",
    )

    # all
    p_all = subparsers.add_parser(
        "all", help="Run extract (if needed), render, compile, and generate worksheets"
    )
    p_all.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force overwrite existing lessons_data.json during extraction",
    )
    p_all.add_argument("--epub", default=EPUB_PATH, help="Path to textbook EPUB file")
    p_all.add_argument(
        "--layout",
        choices=["table", "vertical"],
        default="table",
        help="Reading column layout: 'table' (XeLaTeX tabular grid) or 'vertical' (LuaLaTeX native vertical typesetting). Default: table",
    )
    p_all.add_argument(
        "--with-worksheets",
        action="store_true",
        help="Also generate worksheets when running the 'all' command",
    )
    p_all.add_argument(
        "--hide-name-score",
        action="store_true",
        help="Hide Name and Score fields from generated worksheets",
    )
    p_all.add_argument(
        "--character-guide-color",
        "--character-guide-opacity",
        "--character-opacity",
        dest="character_guide_color",
        default=None,
        help="Color or opacity for character guide outline / upcoming strokes (e.g. 'gray', '0.2', '20%%', '#ccc')",
    )

    # export-readings
    p_export = subparsers.add_parser(
        "export-readings",
        help="Export Classical Chinese readings from the JSON dataset to a clean Markdown file",
    )
    p_export.add_argument(
        "--input",
        "-i",
        default=DATA_FILE,
        help="Path to lessons JSON file. Default: lessons_data.json",
    )
    p_export.add_argument(
        "--output",
        "-o",
        default=READINGS_MD,
        help="Path to output Markdown file. Default: readings.md",
    )

    return parser


def main():
    parser = build_argument_parser()
    args = parser.parse_args()

    if args.command == "extract":
        extract_epub_data(args.epub, force=args.force)
    elif args.command == "render":
        render_latex(args.input, args.output, layout=args.layout)
    elif args.command == "compile":
        compile_latex(args.input)
    elif args.command == "export-readings":
        export_readings(data_file=args.input, output_file=args.output)
    elif args.command == "worksheet":
        generate_worksheets(
            data_file=args.input,
            lesson_filter=args.lessons,
            worksheets_dir=args.output_dir,
            guide=args.guide,
            stroke_order_color=args.stroke_order_color,
            save_info=args.save_info,
            info_only=args.info_only,
            sheet_only=args.sheet_only,
            force_info=args.force_info,
            hide_name_score=args.hide_name_score,
            character_guide_color=args.character_guide_color,
        )
    elif args.command == "all":
        if not os.path.exists(DATA_FILE) or args.force:
            extract_epub_data(args.epub, force=args.force)
        render_latex(DATA_FILE, TEX_FILE, layout=args.layout)
        compile_latex(TEX_FILE)
        if args.with_worksheets:
            generate_worksheets(
                DATA_FILE,
                worksheets_dir=WORKSHEETS_DIR,
                hide_name_score=args.hide_name_score,
                character_guide_color=args.character_guide_color,
            )


if __name__ == "__main__":
    main()
