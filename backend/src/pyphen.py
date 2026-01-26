#pyphen or hypene, code for seprating syllable

import re

def syllabify_word(word):
    pattern = r'[^aeiouAEIOU]*[aeiouAEIOU](?:[^aeiouAEIOU]*(?:NG|ng)|[^aeiouAEIOU](?![aeiouAEIOU]))?'
    return re.findall(pattern, word)

def syllabify_line(line):
    words = line.strip().split()
    return ['-'.join(syllabify_word(word)) for word in words]

pantun = [
    "Kelana bawah langit biru",
    "Kelana jauh dipanggil indung",
    "Rindu aku angin bayu",
    "Dari hulu ke puncak gunung",
]

for line in pantun:
    print(' '.join(syllabify_line(line)))