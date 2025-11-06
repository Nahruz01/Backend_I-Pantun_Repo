#pyphen or hypene, code for seprating syllable

import re

def syllabify_word(word):
    pattern = r'[^aeiouAEIOU]*[aeiouAEIOU](?:[^aeiouAEIOU]*(?:NG|ng)|[^aeiouAEIOU](?![aeiouAEIOU]))?'
    return re.findall(pattern, word)

def syllabify_line(line):
    words = line.strip().split()
    return ['-'.join(syllabify_word(word)) for word in words]

pantun = [
    "Dua tiga kucing berlari,",
    "Mana nak sama si kucing belang",
    "Dua tiga boleh kucari",
    "Mana nak sama kawanku seorang\n",
    "ababa bbbb babab bbabba bbaabbaa,",
    "Pantai pisau amboi kuih"
]

for line in pantun:
    print(' '.join(syllabify_line(line)))