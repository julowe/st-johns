# Quick Creation of cribs/trots of Chinese Poems
# 
# Load this Juypter notebook on some Jupyter server - e.g. [the trial server on Jupyter.org](https://jupyter.org/try-jupyter/lab/) and then hit play (or more specifically 'run this cell and advance') and go through all the cells (usually shift-enter is the shortcut). Or 'restart the kernel and run all cells' should also work.
# 
# Also input your own characters/poem in specified cell below, in format specified. As of now the dictionary entries are not exported, so just copy them from the browser to wherever is convenient for you to save/print. Hopefully a nice formatted export will be made in the future...


## To Do
# - [ ] Try [PyPi Hanzinpy](https://pypi.org/project/hanzipy/) for decomposition into radicals and multi-character lookup/parsing
# - [ ] Try [PyPi chinese](https://pypi.org/project/chinese/) for multi-character lookup/parsing


# general requirements
import re

# from https://pypi.org/project/pycccedict/
from pycccedict.cccedict import CcCedict
cccedict = CcCedict()


# from https://pypi.org/project/chinese-english-lookup/
from chinese_english_lookup import Dictionary
cel_d = Dictionary()

# ## Example function calls
# 
# Use `get_entry` to get all details in a json-y set
# 
# Use `get_definitions` to just return definitions, in a list.
# 
# For other functions etc see [pycccedict's pypi page](https://pypi.org/project/pycccedict/)

cccedict.get_entry('猫')

cccedict.get_definitions('猫')

word_entry = cel_d.lookup('牛油果')
print(word_entry)
word_entry = cel_d.lookup('猫')
print(word_entry)

# ## Getting definitions of all characters in a poem
# 
# Below is Du Fu's "Dreaming of Li Po". [Part 1 from Chapter 7](https://cti.lib.virginia.edu/cll/chinese_literature/watson/CB7.htm) of the larger [300 Tang Poems](https://cti.lib.virginia.edu/frame.htm). [Part 2 from thsi website](https://www.cn-poetry.com/dufu-poetry/li-bai-dream-2.html).
# 
# To use this script edit the below variable or create your own (and then replace it's name in the cell that follows). Put each line in quotes as in the below example. Spaces between characters is ok, it is ignored, but please don't put other roman characters etc.

#杜 甫 du4 fu3
#夢 李 白 二 首 meng4 li3 bai2 er4 shou3 - Dreaming of Li Po

poem_du_fu_dreaming_of_li_po = [
"死 別 已 吞 聲",
"生 別 常 惻 惻",
"江 南 瘴 癘 地",
"逐 客 無 消 息",
"故 人 入 我 夢",
"明 我 長 相 憶",
"恐 非 平 生 魂",
"路 遠 不 可 測",
"魂 來 楓 葉 青",
"魂 去 關 塞 黑",
"君 今 在 羅 網",
"何 以 有 羽 翼",
"落 月 滿 屋 梁",
"猶 疑 照 顏 色",
"水 深 波 浪 闊",
"無 使 蛟 龍 得",
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
pattern = r'[^\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df]+'

#used to mark position of character in line
count_character = 0

#step through array/poem by line then character
for index, line in enumerate(poem_du_fu_dreaming_of_li_po):
    count_character = 0
    print(" ---------- Line {0} ---------- ".format(index+1))
    
    for character in re.sub(pattern, '', line):
        if not character.isspace():
            count_character += 1
            print("{0} ({1}:{2}): {3}".format(
                character, index+1, count_character, "; ".join(cccedict.get_definitions(character))
                )
            )

# Test both packages give same results
# They do.

#used to mark position of character in line
count_character = 0

#step through array/poem by line then character
for index, line in enumerate(poem_du_fu_dreaming_of_li_po):
    count_character = 0
    print(" ---------- Line {0} ---------- ".format(index+1))
    for character in line:
        if not character.isspace():
            count_character += 1
            #print("{0} ({1}:{2}): {3}".format(
                #character, index+1, count_character, "; ".join(cccedict.get_definitions(character))
                #)
            #)
            print("{0} ({1}:{2}) [pycccedict]: {3}".format(
                character, index+1, count_character, "; ".join(cccedict.get_definitions(character))
                )
            )
            print("{0} ({1}:{2}) [c_e_lookup]: {3}".format(
                character, index+1, count_character, "; ".join(cccedict.get_definitions(character))
                )  
            )
