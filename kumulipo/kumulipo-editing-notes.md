# Kumulipo Editing Notes

A record of what, how, and why behind my edits to original file.

## Notes/Decisions

The original interlinearization I am going off of does not always number lines (ref: Line 643.2 vs Line 672)
so I have added the X.2 convention in order to keep all following lines with same numbers as original interlinearization.

I originally used Markdown (`.md`) files for the individual chants,
but due to use of brackets eg: `[?]` and others quirks
I think I will switch to plain text for now.

## To Do

- [x] in chant11.txt move lines into two columns before pasting files together
- [ ] check `NOTE: This word does not seem to have a matching word` in various printings to see if all editions are missing it
- [ ] in Era 11, from line 1209 to 1210, the pattern of pairings seems to change?
See Line 1205: Polo‘ula -- ‘Ula
vs now the 2nd word of a pair seems to have a similarity to the first word of the next pair
See Line 1213: Polohi-pakaka -- Lahiki & Line 1214: Polohi-helehele-lahiki -- Kahiki -
change of the concept of the paired relationships, or process of creation?
- [ ] replace ASDF, make sure `\(\w\)ASDF\s*` gets turned into `\1  \r`
- [ ] Line breaks? keep them and add two spaces? mark explicitly? clarity is usually better.
- [ ] change line numbering so it is not a markdown ordered list (number then a period)
- [ ] standardize \_ or \* for italics
- [ ] check FIXME

## Process

1. `paste` in the queen's transtation to `...interlinear...` file:
like so `paste -d "\n" kumulipo-interlinear-chantX.md kumulipo-Liliʻuokalani-chantX.md > temp`
NB: do not `paste` directly to `kumulipo-interlinear-chantX.md`, only the last file will be pasted in :-/
check `temp` one last time, then `mv` into place
2. Convert original line number style to new style with
3. Remove ASDF placeholders and add newlines
4. Add two trailing spaces to end of lines?

## Regexs for Cleanup

Converted chant/era titles to markdown headers:
`%s/\[\(\d\{1,2\}\)\]\s*\(KA.*\)\n\s*\(CHANT.*\)/## \1 - \2 - \3\r/gc`

Converted VERSE titles to markdown headers:
`%s/\(###\s*\)\?\(\w\)\(.*\) VERSE\(\.\)\?/### \U\2\L\3 Verse/gc`

Inserting note that there was no Beckwith translation supplied
(with 2 trailing spaces to force newlines):
`%s/\(\d\{4\}\..*\)\(\n\)\(\d\{4\}\)/\1  \2_No Beckwith translation supplied\._  \r\3/gc`

Add two trailing spaces to lines ending with a word character, a period, a dash, a comma, a semicolon, a number, an underscore, a double quote, a closing parentheses, or a closing bracket:
`%s/\([a-zA-Z\.\-,;0-9_"\)\]]\)\s\?$/\1  /gc`

Replace multiple trailing spaces with two:
`%s/\s\{3,\}$/  /gc`

Replace Line Numbers:
`%s/\(\d\{4}\)\.\s*/Line \1: /gc`

Replace ASDF placeholders, leaving trailing two spaces:
`%s/\s*ASDF\s*/  \r/gc`
