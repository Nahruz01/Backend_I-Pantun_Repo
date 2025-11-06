#app.py

from flask import Flask, request, jsonify
from flask_cors import CORS
import re

#Custom Backend
from database.database_manager import (
    add_pantun,
    get_all_pantuns,
    delete_pantun,
    get_connection,     
    get_pantun_by_id,
    add_pantun_to_db
)

from src.rhymer_backend import RhymeDetector
from database.database_manager import get_pantun_by_id
from src.pyphen_backend import count_syllables
from src.rater_backend import calculate_rating
#



app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Flask is working with modular DB setup!"

@app.route("/submit-pantun", methods=["POST"])
def submit_pantun():
    data = request.get_json()
    title = data.get("title", "")
    tags = data.get("tags", "")
    lines = data.get("lines", ["", "", "", ""])

    if len(lines) != 4:
        return jsonify({"error": "Pantun must have 4 lines"}), 400

    # Default user = GUEST (id = 0)
    add_pantun(title, tags, lines, user_id=0)
    return jsonify({"message": "Pantun saved successfully!", "user": "GUEST"})

@app.route("/pantuns", methods=["GET"])
def get_pantuns():
    pantuns = get_all_pantuns()
    return jsonify(pantuns)

@app.route("/pantun/<int:pantun_id>", methods=["DELETE"])
def delete_pantun_route(pantun_id):
    delete_pantun(pantun_id)
    return jsonify({"message": f"Pantun {pantun_id} deleted!"})

@app.route("/pantun/<int:pantun_id>/rhyme", methods=["GET"])
def analyze_pantun_rhyme(pantun_id):
    pantun = get_pantun_by_id(pantun_id)
    if not pantun:
        return jsonify({"error": "Pantun not found"}), 404

    # Run analysis using your rhyme engine
    rhyme_result = RhymeDetector.detect_abab(pantun)
    rhyme_ending = RhymeDetector.detect_abab_ending(pantun)

    return jsonify({
        "pantun_id": pantun_id,
        "lines": pantun,
        "rhyme_result": rhyme_result,
        "rhyme_ending": rhyme_ending
    })


# Pantun Rating
@app.route('/add_pantun', methods=['POST'])
def add_pantun_route():
    data = request.get_json()

    # Handle lines list from frontend
    if "lines" in data:
        data["line1"], data["line2"], data["line3"], data["line4"] = data["lines"]

    # Insert pantun into main table
    pantun_id = add_pantun_to_db(data)

    # Fetch pantun lines from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT line1, line2, line3, line4 FROM pantun WHERE pantun_id=?",
        (pantun_id,)
    )
    pantun = cursor.fetchone()
    conn.close()

    if not pantun:
        return jsonify({"error": "Pantun not found"}), 404

    pantun_lines = [pantun[0], pantun[1], pantun[2], pantun[3]]

    # Check if all lines are filled
    all_filled = int(all(line.strip() for line in pantun_lines))  # 1 = all filled, 0 = not

    # Analyze rhyme
    rhyme_result = RhymeDetector.detect_abab(pantun_lines)

    # Count syllables
    syllable_counts = [count_syllables(line) for line in pantun_lines]

    # Simple moral detection placeholder
    moral_detected = int(any(
        keyword in " ".join(pantun_lines).lower()
        for keyword in ["nasihat", "baik", "jangan", "hormat", "bijak"]
    ))

    # Calculate rating and auto_score
    rating, auto_score = calculate_rating(syllable_counts, rhyme_result, moral_detected)

    # Insert analysis into pantun_rating table
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pantun_rating (
            pantun_id, user_id, rating, auto_score, rhyme_type,
            syllable_line1, syllable_line2, syllable_line3, syllable_line4,
            all_lines_filled
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pantun_id,
        data.get("user_id", 0),
        rating,
        auto_score,
        rhyme_result,
        syllable_counts[0],
        syllable_counts[1],
        syllable_counts[2],
        syllable_counts[3],
        all_filled
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Pantun added, analyzed for rhyme, syllables, moral, and line completeness!",
        "pantun_id": pantun_id,
        "rhyme": rhyme_result,
        "syllables": syllable_counts,
        "moral_detected": bool(moral_detected),
        "rating": rating,
        "auto_score": auto_score,
        "all_lines_filled": all_filled
    })


if __name__ == "__main__":
    app.run(debug=True)
