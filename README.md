# Files collected from or created for St. John's

A collection of various files related to St. John's classes, reading groups,
or just general education in that vein.

## Admin Documents

`admin-docs` will contain miscellaneous useful files that aren't for one
specific course. For example, the Eastern Classics Reading list created in TeX:
[admin-docs/MAEC-Reading-List-2024-2025.pdf](admin-docs/MAEC-Reading-List-2024-2025.pdf)
and it's [source TeX file](admin-docs/MAEC-Reading-List.tex)

## Seminar Readings

### Dhvanyāloka

While writing a paper on the Dhvanyāloka I typeset the original terms sheet
provided in the Eastern Classic Manual - [dhvanyAloka/dhvanyAloka-terms-orig.tex](dhvanyAloka/dhvanyAloka-terms-orig.tex) and [the PDF output](dhvanyAloka/dhvanyAloka-terms-orig.pdf).
And then I converted some of the terms into a table format - [dhvanyAloka/dhvanyAloka-terms.tex](dhvanyAloka/dhvanyAloka-terms.tex) ([PDF output](dhvanyAloka/dhvanyAloka-terms.pdf)).

And then I went pretty overboard with my updated version
[dhvanyAloka/dhvanyAloka-terms-additional.tex](dhvanyAloka/dhvanyAloka-terms-additional.tex)
([and PDF output](dhvanyAloka/dhvanyAloka-terms-additional.pdf))
is very much a rough draft and contains far too many terms,
as well as some incorrect definitions I think. Please see .tex file for the
many, many TODO notes contained.

To remain as consistent as possible, all `definitions' were taken directly from
the text provided in the manual, not a dictionary (unless marked as such).

### Tale of the Heike

I copied the character list from our text along with some maps and diagrams - [heike-ref/heike-ref.tex](heike-ref/heike-ref.tex) ([PDF output](heike-ref/heike-ref.pdf))

### Dōgen

I tried out [https://github.com/moste00/PDF-Indexer](https://github.com/moste00/PDF-Indexer)
on the Dōgen text we read, to see what it would produce.
Typeset results - [.tex file](dogen/heart-dogen-index.tex) and [PDF output](dogen/heart-dogen-index.pdf).
It is marginally useful in class to find a quote you are thinking of,
but way too extensive for easy use. Would be better to create my own word list,
and only return pages for those words. Project for another time...

## Precept Readings

### Tale of Genji

I combined the character list from the Seidensticker translation with the character list and more information from the Tyler translation. Added the genealogical chart that Mr. Venkatesh emailed out, adn made a table of the difference in Chapter name translations between the two translations used by either precept group. [genji-ref/genji-ref.tex](genji-ref/genji-ref.tex) ([PDF output](genji-ref/genji-ref.pdf))

## Sanskrit

### Devanagari Transliteration Schemes and Typing Characters

There are a few transliteration schemes for Sanskrit, see
[Wikipedia's Comparison Table](https://en.wikipedia.org/wiki/Devanagari_transliteration#Transliteration_comparison).

Your textbook will likely teach IAST. This is easy to remember & write but hard
to type, e.g. when searching for words online in the [Monier-Williams dictionary](https://www.sanskrit-lexicon.uni-koeln.de/scans/MWScan/2020/web/webtc1/index.php).
That websites use SLP1 - where every Devanagari character is written in a
single roman alphabet letter - for example:
ड (ḍ in IAST) is typed as 'q',
and ढ (ḍh in IAST) is typed as 'Q'

If you install a devanagari keyboard on your computer, try Right-Alt and Right-Alt+Shift to get the various less common characters. And/or for the 'Sanskrit (KaGaPa, Phonetic)' keyboard see my [sanskrit/devanagari-keyboard-map.txt](sanskrit/devanagari-keyboard-map.txt)

### Sanskrit Dictionaries online or loaded into phone apps

Monier-Williams and other dictionaries are available online at the
[Cologne Digital Sanskrit Dictionaries Site](https://www.sanskrit-lexicon.uni-koeln.de/).
But this can be a bit clunky on a phone.

I found a number of dictionaries available at
[indic-dict/stardict-sanskrit](https://github.com/indic-dict/stardict-sanskrit),
but I found the instructions a bit confusing.

I will do a better write-up soon hopefully, but in the meantime, go to:
[indic-dict/stardict-sanskrit's index of dictionary files](https://raw.githubusercontent.com/indic-dict/stardict-sanskrit/gh-pages/sa-head/en-entries/tars/tars.MD)
(which was copied from : [indic-dict/stardict-index's larger index of indexes](https://raw.githubusercontent.com/indic-dict/stardict-index/master/dictionaryIndices.md))
and download the [Monier-Williams compressed file](https://github.com/indic-dict/stardict-sanskrit/raw/gh-pages/sa-head/en-entries/tars/mw-cologne__2024-01-17_03-14-56Z__14MB.tar.gz),
then get a phone dictionary app that can load in StarDict files
(DictionaryUniversal (?) on iPhone is what I use and is worth the $5,
or Dicty works decently well for free)

### Sanskrit Grammar Reference Tables

I originally copied the tables from the book, or retyped them myself, but after
a while I wanted a more complete reference sheet.

I found the [Sanskrit Garden of Paradigms](https://www.yesvedanta.com/sanskrit/garden/)
to be incredibly useful. Also look at the
[Fancy Sanskrit Grammar Tables](https://www.yesvedanta.com/sanskrit/tenses/)
to remind you of more details. The two tables reference each other.

### Nāgārjuna Chapter 25 packet

In class we used a photocopy of Chapter 25 of Nāgārjuna's Mūlamadhyamakakārikā.

My hope is to have at least some chapters of Nāgārjuna formatted in the
[Scharf/Rāmopākhyāna](https://bookshop.org/p/books/ramopakhyana-the-story-of-rama-in-the-mahabharata-a-sanskrit-independent-study-reader-peter-scharf/10187068)
style. But that hasn't happened yet.

In the meantime a PDF of the scanned packet we used in class is available here:
[nagarjuna-ch25.pdf](sanskrit/nagarjuna-ch25.pdf)

### Scharf's Rāmopākhyāna

A PDF of the quick reference guide I compiled from the Introduction of the
[Scharf's Rāmopākhyāna](https://bookshop.org/p/books/ramopakhyana-the-story-of-rama-in-the-mahabharata-a-sanskrit-independent-study-reader-peter-scharf/10187068),
can be found here:
[sanskrit-grammar-terms-tables-ramopakhyana-full.pdf](sanskrit/sanskrit-grammar-terms-tables-ramopakhyana-full.pdf)

I have taken most of the tables from the Introduction and put them in a one
page spreadsheet to print out as a quick reference guide.
It is currently in an Excel file in OneDrive, but I can't create a publicly
viewable link for more than 60 days, so please contact me if you want to make
edits. Eventually I will probably save it directly here or reformat it in TeX,
or some more reasonable format.

## Kumulipo Reading Group

I am facilitating a reading group on the Kumulipo and have the source text here
[kumulipo/kumulipo-interlinear.md](kumulipo/kumulipo-interlinear.md),
which I am working to further interlinearize.

## Chinese Poetry

I used the MyBinder service to create an online Python/Jupyter notebook that can use dictionary files and generate glosses/cribs/trots of Chinese texts. The example data in the notebook are Chinese Poems. This code was here originally, but I have since split it out into it's own repo here: [julowe/binder-chinese-poetry](https://github.com/julowe/binder-chinese-poetry)
