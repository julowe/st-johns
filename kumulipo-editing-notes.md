# Kumulipo Editing Notes

A record of what, how, and why behind my edits to original file.

## To Do

- [ ] replace ASDF, make sure `\(\w\)ASDF\s*` gets turned into `\1  \r`
- [ ] Line breaks? keep them and add two spaces? mark explicitly? clarity is usually better.
- [ ] change line numbering so it is not a markdown ordered list (number then a period)
- [ ] standardize _ or * for italics
- [ ] check FIXME

## Regexs for Cleanup

Converted chant/era titles to markdown headers:
`%s/\[\(\d\{1,2\}\)\]\s*\(KA.*\)\n\s*\(CHANT.*\)/## \1 - \2 - \3\r/gc`

Converted VERSE titles to markdown headers:
`%s/\(###\s*\)\?\(\w\)\(.*\) VERSE\(\.\)\?/### \U\2\L\3 Verse/gc`

Inserting note that there was no Beckwith translation supplied
(with 2 trailing spaces to force newlines):
`%s/\(\d\{4\}\..*\)\(\n\)\(\d\{4\}\)/\1  \2_No Beckwith translation supplied\._  \r\3/gc`

Add two trailing spaces to lines ending with a word character, a period, a dash, a comma, a semicolon a number, or a closing bracket:
`%s/\([a-zA-Z\.\-,;0-9\]]\)$/\1  /gc`

Replace Line Numbers:
`%s/\(\d\{4}\)\.\s*/Line \1: /gc`

Replace ASDF placeholders, leaving trailing two spaces:
`%s/\s*ASDF\s*/  \r/gc`