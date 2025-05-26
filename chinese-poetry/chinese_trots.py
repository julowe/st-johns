# # Quick Creation of cribs/trots of Chinese Poems
# 
# Load this Juypter notebook on some Jupyter server - e.g. by clicking the [mybinder.org link from my github](https://mybinder.org/v2/gh/julowe/st-johns/HEAD?urlpath=%2Fdoc%2Ftree%2Fchinese-poetry%2Fchinese_trots.ipynb) or loading the file in [the trial server on Jupyter.org](https://jupyter.org/try-jupyter/lab/) and then hit play (or more specifically 'run this cell and advance') and go through all the cells (usually shift-enter is the shortcut). Or 'restart the kernel and run all cells' should also work.
# 
# Also input your own characters/poem in specified cell below, in format specified. As of now the dictionary entries are not exported, so just copy them from the browser to wherever is convenient for you to save/print. Hopefully a nice formatted export will be made in the future...

# ## To Do
# 
# - [x] Try [PyPi Hanzinpy](https://pypi.org/project/hanzipy/) for decomposition into radicals and multi-character lookup/parsing
#   - Worked pretty well, just some oddness with that one character, see below. It says it is using CC-CEDICT (like pleco and other two modules) but sometimes has additional results? (Not fewer, just more...)
# - [ ] Try [PyPi chinese](https://pypi.org/project/chinese/) for multi-character lookup/parsing

# general requirements
import re
from pprint import pprint

# from https://pypi.org/project/pycccedict/
from pycccedict.cccedict import CcCedict

cccedict = CcCedict()

# from https://pypi.org/project/chinese-english-lookup/
from chinese_english_lookup import Dictionary

cel_d = Dictionary()

#from https://pypi.org/project/hanzipy/
# import dictionary
from hanzipy.decomposer import HanziDecomposer
hDecomposer = HanziDecomposer()
# import decomposer
from hanzipy.dictionary import HanziDictionary
hDictionary = HanziDictionary()

# ## Example function calls
# 
# Use `get_entry` to get all details in a json-y set
# 
# Use `get_definitions` to just return definitions, in a list.
# 
# For other functions etc see [pycccedict's pypi page](https://pypi.org/project/pycccedict/)

cccedict.get_entry("猫")

cccedict.get_definitions("猫")

word_entry = cel_d.lookup("牛油果")
print(word_entry)
word_entry = cel_d.lookup("猫")
print(word_entry)

# ## Getting definitions of all characters in a poem
# 
# Below is Du Fu's "Dreaming of Li Po". [Part 1 from Chapter 7](https://cti.lib.virginia.edu/cll/chinese_literature/watson/CB7.htm) of the larger [300 Tang Poems](https://cti.lib.virginia.edu/frame.htm). [Part 2 from thsi website](https://www.cn-poetry.com/dufu-poetry/li-bai-dream-2.html).
# 
# To use this script edit the below variable or create your own (and then replace it's name in the cell that follows). Put each line in quotes as in the below example. Spaces between characters is ok, it is ignored, but please don't put other roman characters etc.

# 杜 甫 du4 fu3
# 夢 李 白 二 首 meng4 li3 bai2 er4 shou3 - Dreaming of Li Po

poem_du_fu_dreaming_of_li_po = [
    "死別已吞聲",
    "生別常惻惻",
    "江南瘴癘地",
    "逐客無消息",
    "故人入我夢",
    "明我長相憶",
    "恐非平生魂",
    "路遠不可測",
    "魂來楓葉青",
    "魂去關塞黑",
    "君今在羅網",
    "何以有羽翼",
    "落月滿屋梁",
    "猶疑照顏色",
    "水深波浪闊",
    "無使蛟龍得",
    "浮云终日行",
    "游子久不至",
    "三夜频梦君",
    "情亲见君意",
    "告归常局促",
    "苦道来不易",
    "江湖多风波",
    "舟楫恐失坠",
    "出门搔白首",
    "若负平生志",
    "冠盖满京华",
    "斯人独憔悴",
    "孰云网恢恢",
    "将老身反累",
    "千秋万岁名",
    "寂寞身后事",
]

# from https://usavps.com/blog/64481/
# Define a regular expression pattern for Chinese characters
pattern = r"[^\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df]+"

# used to mark position of character in line
count_character = 0

# step through array/poem by line then character
for index, line in enumerate(poem_du_fu_dreaming_of_li_po):
    count_character = 0
    print(" ---------- Line {0} ---------- ".format(index + 1))

    for character in re.sub(pattern, "", line):
        if not character.isspace():
            count_character += 1
            print(
                "{0} ({1}:{2}): {3}".format(
                    character,
                    index + 1,
                    count_character,
                    "; ".join(cccedict.get_definitions(character)),
                )
            )

# Test both packages give same results
# They do.

# used to mark position of character in line
count_character = 0

# step through array/poem by line then character
for index, line in enumerate(poem_du_fu_dreaming_of_li_po):
    count_character = 0
    print(" ---------- Line {0} ---------- ".format(index + 1))
    for character in line:
        if not character.isspace():
            count_character += 1
            # print("{0} ({1}:{2}): {3}".format(
            # character, index+1, count_character, "; ".join(cccedict.get_definitions(character))
            # )
            # )
            print(
                "{0} ({1}:{2}) [pycccedict]: {3}".format(
                    character,
                    index + 1,
                    count_character,
                    "; ".join(cccedict.get_definitions(character)),
                )
            )
            print(
                "{0} ({1}:{2}) [c_e_lookup]: {3}".format(
                    character,
                    index + 1,
                    count_character,
                    "; ".join(cccedict.get_definitions(character)),
                )
            )

## Process using hanzipy

# from https://usavps.com/blog/64481/
# Define a regular expression pattern for Chinese characters
pattern = r"[^\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df]+"

# used to mark position of character in line
count_character = 0

# step through array/poem by line then character
for line_index, line_text in enumerate(poem_du_fu_dreaming_of_li_po):
    count_character = 0
    print("---------- Line {0} ----------".format(line_index + 1))

    for character in re.sub(pattern, "", line_text):
        if not character.isspace():
            count_character += 1

            ## print 'header' to seperate character info
            # print("---- Info for {0}:".format(character))

            ## hmm this failed on "魂" while other two modules did work. This module even worked it just had two entries for this and fails to find it in 'traditional' search mode??
            # character_definitions = hDictionary.definition_lookup(character, "traditional")
            try:
                character_definitions = hDictionary.definition_lookup(
                    character, "traditional"
                )
            except KeyError:
                # print('ugh')
                print(
                    "Unable to find 'traditional' definition for {0}, falling back to more general search, results may vary...".format(
                        character
                    )
                )
                try:
                    character_definitions = hDictionary.definition_lookup(character)
                except KeyError:
                    print("Unable to find any definition for {0} !!".format(character))
                    # TODO: use ccedict as third/last attempt?
            finally:
                # print(character_definitions)

                character_definition_string = ""
                for entry in character_definitions:
                    # TODO: add pinyin (and also trad char?) to start of each definition??
                    if len(character_definition_string) > 0:
                        character_definition_string += "; "

                    character_definition_string += entry["definition"]

                    # character_definition_string += "; ".join(entry['definition'])
                    # print("; ".join(entry['definition']))
                    # print(entry['definition'])

                if len(character_definitions) == 1:
                    character_definition_string_start = "Definition"
                else:
                    character_definition_string_start = "Definitions"

                # print("---- Info for {0}:".format(character))
                print(
                    "{0} for {1}, char#{2}: {3}".format(
                        character_definition_string_start,
                        character,
                        count_character,
                        character_definition_string,
                    )
                )

            # print("{0} ({1}:{2}): {3}".format(
            #    character, line_index+1, count_character, "; ".join(hDictionary.definition_lookup(character, "traditional")['definition'])
            #    )
            # )

            ## Get components of character

            character_decomposition = hDecomposer.decompose(character)
            # print(character_decomposition)
            # no difference, just does not return other values.
            # character_decomposition2 = hDecomposer.decompose(character, 2)
            # print(character_decomposition2)

            radical_decomposition_string = "    Decomposition: "
            for index, radical in enumerate(character_decomposition["radical"]):
                if index > 0:
                    radical_decomposition_string += "; "

                radical_decomposition_string += "Radical ({0}): {1}".format(
                    radical, hDecomposer.get_radical_meaning(radical)
                )

                # print("    Radical ({0}): {1}".format(radical, hDecomposer.get_radical_meaning(radical)))

            print(radical_decomposition_string)

            # hDecomposer = HanziDecomposer()
            # hDictionary = HanziDictionary()

    # then after looking up each character's definition, do whole line at once
    print(
        "---- Possible compound words in {0}: (Note: results are not always for correct ordering of characters)".format(
            line_text
        )
    )

    # TODO: do better printing of this. for result in results: pprint? and only if len(result['traditional']) > 1 ?
    line_text_combo_results = hDictionary.dictionary_search(line_text, "only")

    line_text_combo_results_multicharacter = False
    for result in line_text_combo_results:
        # print("Entry of {0} has length {1}".format(result['traditional'], len(result['traditional'])))
        if len(result["traditional"]) > 1:
            # TODO: this search will often reutrn a 'compound word' if one character is repeated to make that word.
            #  but you get this result even if the character is only in theline once.
            #  so let's search and make sure the result is actually in the line?
            line_text_combo_results_multicharacter = True
            # TODO: print traditional and simple? Maybe not useful
            print(
                "Compound {0}: {1}".format(result["traditional"], result["definition"])
            )

    ## Print userfriendly message of 'no combos found'
    if not line_text_combo_results_multicharacter:
        print("No compound words found.")

    # if you get a weird result in the combos section, uncomment this line to see full info on all returns, but it doesn't always make anything clearer...
    # pprint(line_text_combo_results)
