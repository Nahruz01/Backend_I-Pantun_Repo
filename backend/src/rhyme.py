import re

pantun = [
    "Dua tiga kucing berlari,",
    "Mana nak sama si kucing belang",
    "Dua tiga boleh kucari",
    "Mana nak sama kawanku seorang"
]

pantun2xxxx = [
    "Dua,",
    "Mana nak",
    "Dua tiga boleh kucari",
    "Mana nak sama kawanku se"
]

pantun2AAAA = [
    "aba",
    "cbca", 
    "nba", 
    "abca"
]


# Basic Malay syllable splitter using vowel-based heuristic
def get_last_syllable(word):
    # Simple Malay syllable approximation: split before vowels
    syllables = re.findall(r'[^aeiou]*[aeiou]+(?:ng|[bcdfghjklmnpqrstvwxyz]*)?', word.lower())
    return syllables[-1] if syllables else word.lower()

# Function to extract and clean last word from a line
def get_last_word(line):
    words = line.strip().split()
    return re.sub(r'[^\w]', '', words[-1].lower())

# Function to detect ABAB rhyme using last syllables
def detect_abab_rhyme(pantun):
    last_words = [get_last_word(line) for line in pantun]
    last_syllables = [get_last_syllable(word) for word in last_words]

    a1, b1, a2, b2 = last_syllables
    
    if a1 == a2 and b1 == b2 and a1 != b1:
        return f"ABAB rhyme scheme detected: {last_syllables}"
    elif a1 == a2 == b1 == b2:
        return f"AAAA rhyme detected: {last_syllables}"
    elif a1 == a2 or b1 == b2:
        return f"Partial rhyme: {last_syllables}"
    else:
        return f"No ABAB rhyme: syllables were {last_syllables}"


def compare_rhyme(word1, word2, min_length=2):
    """
    Compare word1 and word2 from the end.
    min_length: minimum letters to consider it a rhyme
    Returns number of matching letters from the end.
    """
    word1 = word1.lower()
    word2 = word2.lower()
    match_len = 0
    for c1, c2 in zip(reversed(word1), reversed(word2)):
        if c1 == c2:
            match_len += 1
        else:
            break
    return match_len >= min_length

def get_shared_ending(word1, word2, min_length=1):
    """
    Return the letters shared at the end of word1 and word2, starting from the last letter.
    Only returns if at least min_length letters match.
    """
    word1 = word1.lower()
    word2 = word2.lower()
    shared = []
    for c1, c2 in zip(reversed(word1), reversed(word2)):
        if c1 == c2:
            shared.append(c1)
        else:
            break
    if len(shared) >= min_length:
        return ''.join(reversed(shared))
    return ''



    
def detect_abab_rhyme_ending(pantun):
    last_words = [get_last_word(line) for line in pantun]
    w1, w2, w3, w4 = last_words

    # ABAB rhyme
    a_shared = get_shared_ending(w1, w3)
    b_shared = get_shared_ending(w2, w4)

    # AAAA rhyme (longest shared ending among all four)
    # We can do it by repeatedly using get_shared_ending pairwise
    temp1 = get_shared_ending(w1, w2)
    temp2 = get_shared_ending(temp1, w3) if temp1 else ''
    common_ending = get_shared_ending(temp2, w4) if temp2 else ''

    if a_shared and b_shared and w1 != w2:
        return f"ABAB rhyme detected: A='{a_shared}', B='{b_shared}'"
    elif common_ending:
        return f"AAAA rhyme detected: '{common_ending}'"
    else:
        return f"No clear rhyme"



print(detect_abab_rhyme(pantun))
print(detect_abab_rhyme(pantun2xxxx))
print(detect_abab_rhyme(pantun2AAAA))
print(detect_abab_rhyme_ending(pantun))
print(detect_abab_rhyme_ending(pantun2xxxx))
print(detect_abab_rhyme_ending(pantun2AAAA))

'''
pantun
pantun2xxxx
pantun2AAAA
'''