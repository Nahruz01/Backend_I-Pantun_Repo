#pyphen_backend.py

# utils.py (or somewhere reusable)
import re

def syllabify_word(word):
    pattern = r'[^aeiouAEIOU]*[aeiouAEIOU](?:[^aeiouAEIOU]*(?:NG|ng)|[^aeiouAEIOU](?![aeiouAEIOU]))?'
    return re.findall(pattern, word)

def syllabify_line(line):
    words = line.strip().split()
    # Join syllables with '-' (optional), count syllables
    syllables = ['-'.join(syllabify_word(word)) for word in words]
    return syllables

def count_syllables(line):
    syllables = syllabify_line(line)
    # Count total number of syllables in the line
    return sum([len(syll.split('-')) for syll in syllables])
