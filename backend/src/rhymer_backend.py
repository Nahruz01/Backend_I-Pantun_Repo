# backend/src/rhymer_backend.py
import re

class RhymeDetector:

    @staticmethod
    def get_last_syllable(word):
        syllables = re.findall(r'[^aeiou]*[aeiou]+(?:ng|[bcdfghjklmnpqrstvwxyz]*)?', word.lower())
        return syllables[-1] if syllables else word.lower()

    @classmethod
    def get_last_word(cls, line: str) -> str:
        words = line.strip().split()
        if not words:
            return ""  # Return empty string if line is empty
        return re.sub(r'[^\w]', '', words[-1].lower())

    @staticmethod
    def get_shared_ending(word1, word2, min_length=1):
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

    @classmethod
    def detect_abab(cls, pantun):
        last_words = [cls.get_last_word(line) for line in pantun]
        last_syllables = [cls.get_last_syllable(word) for word in last_words]

        if len(last_syllables) != 4:
            return "Invalid pantun: must have 4 lines."

        a1, b1, a2, b2 = last_syllables
        if a1 == a2 and b1 == b2 and a1 != b1:
            return f"ABAB rhyme detected: {last_syllables}"
        elif a1 == a2 == b1 == b2:
            return f"AAAA rhyme detected: {last_syllables}"
        elif a1 == a2 or b1 == b2:
            return f"Partial rhyme: {last_syllables}"
        else:
            return f"No ABAB rhyme: syllables were {last_syllables}"

    @classmethod
    def detect_abab_ending(cls, pantun):
        last_words = [cls.get_last_word(line) for line in pantun]
        if len(last_words) != 4:
            return "Invalid pantun: must have 4 lines."

        w1, w2, w3, w4 = last_words
        a_shared = cls.get_shared_ending(w1, w3)
        b_shared = cls.get_shared_ending(w2, w4)

        temp1 = cls.get_shared_ending(w1, w2)
        temp2 = cls.get_shared_ending(temp1, w3) if temp1 else ''
        common_ending = cls.get_shared_ending(temp2, w4) if temp2 else ''

        if a_shared and b_shared and w1 != w2:
            return f"ABAB rhyme detected: A='{a_shared}', B='{b_shared}'"
        elif common_ending:
            return f"AAAA rhyme detected: '{common_ending}'"
        else:
            return f"No clear rhyme"
