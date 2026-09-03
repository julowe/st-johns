# Classical Chinese Study Sheets Generator

A modular toolchain to extract reading passages and vocabulary from
Bryan W. van Norden's textbook
**_Classical Chinese for Everyone: A Guide for Absolute Beginners_** (EPUB)
and typeset them into 8.5" $\times$ 11" two-column study and reference sheets.

---

## Purpose & Design

These study sheets condense each lesson into a clean, self-contained single-page companion (13 pages total, 1 page per lesson):

- **Left Column (60–70% width):** Full, verbatim vocabulary definitions, pinyin diacritics, grammatical part-of-speech tags, footnote annotations, and stroke count lookups. (For **Lesson 10**, the textbook's dedicated 4-column Dictionary Practice table—_Character_, _Hint_, _Pronunciation_, _Relevant Meaning_—is faithfully recreated on the left).
- **Right Column (30–40% width, snug fit):** Traditional top-to-bottom, right-to-left vertical character columns matching the textbook's visual layout.
- **Single-Page Perfection:** Spacing and typography are dynamically scaled so that even the longest lessons (e.g. Lesson 8 with 29 vocabulary items) fit comfortably on **one single 8.5" $\times$ 11" page** alongside their complete reading passages.

---

## Architecture & Pipeline

The pipeline is split into independent stages around a **persistent, human-editable intermediate data file** (`lessons_data.json`):

```
                        ┌─────────────────────────────────────────────────┐
                        │ Textbook EPUB (Classical Chinese for Everyone)  │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                           extract stage
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │  lessons_data.json                              │
                        │  (Human-editable; manual page splits/edits safe)│
                        └────────────────────────┬────────────────────────┘
                                                 │
                                            render stage
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │  lessons_all.tex                                │
                        │  (XeLaTeX master document with paracol/xeCJK)   │
                        └────────────────────────┬────────────────────────┘
                                                 │
                                           compile stage
                                                 │
                                                 ▼
                        ┌─────────────────────────────────────────────────┐
                        │  lessons_all.pdf                                │
                        │  (21-page ready-to-print study booklet)         │
                        └─────────────────────────────────────────────────┘
```

---

## Repository & File Structure

| File / Directory                           | Description                                                                                           |
| :----------------------------------------- | :---------------------------------------------------------------------------------------------------- |
| [`manage_sheets.py`](manage_sheets.py)     | Main CLI tool implementing `extract`, `render`, `compile`, and `all` subcommands.                     |
| [`lessons_data.json`](lessons_data.json)   | Persistent intermediate data storing structured lesson titles, reading columns, and vocabulary lists. |
| [`stroke_counts.json`](stroke_counts.json) | Complete offline Unicode Han (`Unihan`) stroke database (100,000+ characters).                        |
| [`lessons_all.tex`](lessons_all.tex)       | Generated XeLaTeX source document.                                                                    |
| [`lessons_all.pdf`](lessons_all.pdf)       | Compiled 21-page PDF study booklet.                                                                   |
| `fonts/`                                   | Publisher fonts extracted directly from the EPUB (`SimSun.ttf`, `CharisSIL.ttf`, `MinionPro-*.otf`).  |

---

## Usage Guide

All operations are driven via [`manage_sheets.py`](manage_sheets.py):

### 1. Compile Current PDF

If you just want to re-render the `.tex` file from `lessons_data.json` and compile the PDF:

```bash
# Render LaTeX from lessons_data.json
python3 manage_sheets.py render

# Compile to PDF using XeLaTeX
python3 manage_sheets.py compile
```

Or run both in one step:

```bash
python3 manage_sheets.py render && python3 manage_sheets.py compile
```

### 2. Extract Data from EPUB

```bash
# Extract EPUB data into lessons_data.json (will NOT overwrite if file already exists)
python3 manage_sheets.py extract

# Force re-extraction from EPUB (WARNING: overwrites lessons_data.json)
python3 manage_sheets.py extract --force
```

### 3. Run Full Pipeline

```bash
# Extracts (only if lessons_data.json is missing), renders .tex, and compiles .pdf
python3 manage_sheets.py all
```

---

## How to Make Manual Edits (Page Splits & Text Tweaks)

The intermediate file [`lessons_data.json`](lessons_data.json) is designed to be edited directly.

### Slicing a Lesson onto Multiple Pages

Each lesson object contains an explicit `pages` array:

```json
{
  "lesson_number": 3,
  "lesson_title": "Lesson 3",
  "reading_title": "3.1. Readings: Analects 12.22, Analects 4.2, and Analects 6.23",
  "reading_columns": [
    "樊遲問仁。子曰。愛人。問知。子曰。知人。",
    "---",
    "子曰。仁者安仁。知者利仁。",
    "---",
    "子曰。知者樂水。仁者樂山。"
  ],
  "pages": [
    {
      "page_index": 1,
      "reading_title": "3.1. Readings: Analects 12.22, Analects 4.2, and Analects 6.23",
      "reading_columns": ["樊遲問仁。子曰。愛人。問知。子曰。知人。", "---", "子曰。仁者安仁。知者利仁。"],
      "vocab_subtitle": "(Part 1 of 2)",
      "vocab": [ ... ]
    },
    {
      "page_index": 2,
      "reading_title": "3.1. Readings: Analects 6.23 (Continued)",
      "reading_columns": ["子曰。知者樂水。仁者樂山。"],
      "vocab_subtitle": "(Part 2 of 2)",
      "vocab": [ ... ]
    }
  ]
}
```

### Page Layout & Formatting Variables (Per Lesson)

Each page object in `lessons_data.json` provides user-editable formatting and layout variables:

- `"vocab_font_size"`: Font size for the definition text (defaults to `"small"`). Can be set to `"normalsize"`, `"small"`, `"footnotesize"`, or `"scriptsize"`.
- `"vocab_item_sep"`: Vertical line spacing between vocabulary entries (defaults to `"2.5pt"`). Can be adjusted to `"2.0pt"`, `"1.5pt"`, `"1.0pt"`, `"0.5pt"`, etc.
- `"vocab_cjk_font_size"`: Independent font size for all Chinese characters in that lesson's vocabulary section (defaults to `"14pt"`). Can be scaled up to `"16pt"`, `"18pt"`, `"20pt"`.
- `"column_ratio"`: The proportion of horizontal page width allocated to the left (vocabulary) column (e.g. `0.75` for 75% vocab / 25% reading, `0.65` for 65% / 35%).

In the generated `.tex` file, all Chinese characters throughout the vocabulary section are wrapped in a concise macro:

```latex
\vocabChar{遠} or \vocabChar{遠} (\vocabChar{远}) yuǎn s.v., to be far \stroketag{[13 strokes]}
```

```json
{
  "page_index": 1,
  "reading_title": "1.1. Reading: Analects 1.1",
  "vocab_font_size": "small",
  "vocab_item_sep": "2.5pt",
  "vocab_cjk_font_size": "14pt",
  "column_ratio": 0.83,
  "reading_columns": [ ... ],
  "vocab": [ ... ]
}
```

### JSON Schema & Vocabulary Fields

Each vocabulary item in `lessons_data.json` contains:

- `text`: Base definition text.
- `footnotes`: Array of attached footnote text strings (`["Nerd note: ..."]`).
- `stroke_tag`: Auto-calculated stroke count badge (e.g. `"[14 strokes]"`).
- `full_line`: The rendered line containing the definition, `{Footnote: <FOOTNOTE TEXT>}`, and stroke count.

To adjust formatting or page breaks, simply edit `lessons_data.json` and recompile:

```bash
python3 chinese/manage_sheets.py render
python3 chinese/manage_sheets.py compile
```

---

## Typography & Fonts

To guarantee exact visual fidelity with Bryan W. van Norden's published textbook, the script extracts and uses the EPUB's embedded fonts:

- **Chinese Characters:** `SimSun.ttf` (Song / Ming style CJK serif).
- **Pinyin & English Text:** `CharisSIL.ttf` / `CharisSIL-Bold.ttf` (full Unicode support for pinyin tone diacritics `ǐ`, `ǒ`, `ǎ`, `ǔ`).
- **LaTeX Packages Used:** `xeCJK`, `fontspec`, `paracol` (for synchronized dual columns), `tcolorbox` (for clean framed boxes), and `geometry` (0.42" margins).

---

## System Requirements

- **Python:** 3.10+ (uses standard library only: `json`, `zipfile`, `xml.etree.ElementTree`, `re`, `argparse`).
- **LaTeX Engine:** `xelatex` (TeX Live 2024 / 2025).

---

## TODO

- [ ] add date to footer
- [ ] make a smaller gap between vocab pinyin and definition
