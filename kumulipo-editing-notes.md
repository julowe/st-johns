# Kumulipo Editing Notes

A record of what, how, and why behind my edits to original file.

## Regexs for Cleanup

Converted chant/era titles to markdown headers:
`%s/\[\(\d\{1,2\}\)\]\s*\(KA.*\)\n\s*\(CHANT.*\)/## \1 - \2 - \3\r/gc`

Inserting note that there was no Beckwith translation supplied
(with 2 trailing spaces to force newlines):
`%s/\(\d\{4\}\..*\)\(\n\)\(\d\{4\}\)/\1  \2_No Beckwith translation supplied\._  \r\3/gc`
