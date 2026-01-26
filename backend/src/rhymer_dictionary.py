def find_word(word: str, word_list) -> bool:
    if not word:
        return False
    return word.lower().strip() in word_list


def search_same_ending(word: str, word_list):
    word = word.lower().strip()
    return [w for w in word_list if w.lower().endswith(word)]
