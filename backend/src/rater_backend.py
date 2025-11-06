# rater_backend.py

def calculate_rating(syllable_counts, rhyme_type, moral_detected):
    # Syllable score (ideal 8–12 per line)
    syllable_score = sum(1 for s in syllable_counts if 8 <= s <= 12)

    # Rhyme score
    rhyme_map = {
        "ABAB": 5,
        "AAAA": 4,
        "Partial": 2,
        "None": 0
    }
    rhyme_score = rhyme_map.get(rhyme_type.split()[0], 0)

    # Moral score
    moral_score = 2 if moral_detected else 0

    auto_score = syllable_score + rhyme_score + moral_score  # raw score

    # Convert score to star rating (1–5)
    # Adjust the thresholds as you like
    if auto_score >= 9:       star_rating = 5
    elif auto_score >= 7:     star_rating = 4
    elif auto_score >= 5:     star_rating = 3
    elif auto_score >= 3:     star_rating = 2
    else:                     star_rating = 1

    return star_rating, auto_score
