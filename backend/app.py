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


from werkzeug.security import generate_password_hash, check_password_hash
#
from src.rhymer_backend import RhymeDetector
from database.database_manager import get_pantun_by_id
from src.pyphen_backend import count_syllables
from src.rater_backend import calculate_rating
from src.rhymer_dictionary import search_same_ending, find_word
from src.all_words import words as ALL_WORDS
#



app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Flask is working with modular DB setup!"

## HOME
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    hashed_password = generate_password_hash(password)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
    except:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    user_id, hashed_password = user

    if check_password_hash(hashed_password, password):
        return jsonify({
            "message": "Login successful",
            "user_id": user_id,
            "username": username
        })

    return jsonify({"error": "Invalid password"}), 401



@app.route("/pantuns/mine", methods=["GET"])
def get_my_pantuns():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            po.post_id,  
            p.pantun_id, p.title, p.tags, p.line1, p.line2, p.line3, p.line4,
            po.visibility,
            (SELECT COUNT(*) FROM likes l WHERE l.post_id = po.post_id) AS likes_count,
            (SELECT COUNT(*) FROM comments c WHERE c.post_id = po.post_id) AS comments_count,
            (SELECT AVG(r.rating) FROM pantun_rating r WHERE r.pantun_id = p.pantun_id) AS rating_avg
        FROM pantun p
        JOIN posts po ON po.pantun_id = p.pantun_id
        WHERE po.user_id = ?
        ORDER BY po.created_at DESC
    """, (user_id,))

    data = cursor.fetchall()
    conn.close()

    result = []
    for row in data:
        result.append({
            "post_id": row[0],  # NEW
            "pantun_id": row[1],
            "title": row[2],
            "tags": row[3],
            "line1": row[4],
            "line2": row[5],
            "line3": row[6],
            "line4": row[7],
            "visibility": row[8],
            "likes_count": row[9],
            "comments_count": row[10],
            "rating_avg": row[11]
        })

    return jsonify(result)

@app.route("/pantuns/public", methods=["GET"])
def get_public_pantuns():
    user_id = request.args.get("user_id", type=int)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            p.pantun_id, p.title, p.tags, p.line1, p.line2, p.line3, p.line4,
            u.username, 
            (SELECT COUNT(*) FROM likes l WHERE l.post_id = po.post_id) AS likes_count,
            (SELECT COUNT(*) FROM comments c WHERE c.post_id = po.post_id) AS comments_count,
            (SELECT AVG(r.rating) FROM pantun_rating r WHERE r.pantun_id = p.pantun_id) AS rating_avg,
            po.post_id,
            EXISTS (
                SELECT 1 FROM favorites f
                WHERE f.post_id = po.post_id AND f.user_id = ?
            ) AS isFav
        FROM pantun p
        JOIN posts po ON po.pantun_id = p.pantun_id
        JOIN users u ON u.user_id = po.user_id
        WHERE po.visibility = 'public'
        ORDER BY po.created_at DESC
    """, (user_id,))
    data = cursor.fetchall()
    conn.close()

    result = []
    for row in data:
        result.append({
            "pantun_id": row[0],
            "title": row[1],
            "tags": row[2],
            "line1": row[3],
            "line2": row[4],
            "line3": row[5],
            "line4": row[6],
            "username": row[7],
            "likes_count": row[8],
            "comments_count": row[9],
            "rating_avg": row[10],
            "post_id": row[11],
            "isFav": bool(row[12])
        })

    return jsonify(result)


@app.route("/posts/<int:post_id>/visibility", methods=["PATCH"])
def update_post_visibility(post_id):
    data = request.get_json()
    visibility = data.get("visibility")
    if visibility not in ["public", "private"]:
        return jsonify({"error": "Invalid visibility"}), 400

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE posts SET visibility=? WHERE post_id=?",
        (visibility, post_id)
    )
    conn.commit()
    conn.close()

    return jsonify({"message": f"Post {post_id} visibility updated to {visibility}"})


@app.route("/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    conn = get_connection()
    c = conn.cursor()

    # 1. Get pantun_id linked to this post
    c.execute(
        "SELECT pantun_id FROM posts WHERE post_id = ?",
        (post_id,)
    )
    row = c.fetchone()

    if not row:
        conn.close()
        return jsonify({"error": "Post not found"}), 404

    pantun_id = row[0]

    # 2. Delete post first
    c.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))

    # 3. Delete pantun
    c.execute("DELETE FROM pantun WHERE pantun_id = ?", (pantun_id,))

    conn.commit()
    conn.close()

    return jsonify({"message": "Post and pantun deleted"})

@app.route("/posts/<int:post_id>/like", methods=["POST"])
def toggle_like(post_id):
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_connection()
    c = conn.cursor()

    # Check if already liked
    c.execute(
        "SELECT 1 FROM likes WHERE user_id = ? AND post_id = ?",
        (user_id, post_id)
    )
    liked = c.fetchone()

    if liked:
        # Unlike
        c.execute(
            "DELETE FROM likes WHERE user_id = ? AND post_id = ?",
            (user_id, post_id)
        )
        action = "unliked"
    else:
        # Like
        c.execute(
            "INSERT INTO likes (user_id, post_id) VALUES (?, ?)",
            (user_id, post_id)
        )
        action = "liked"

    # Get updated count
    c.execute(
        "SELECT COUNT(*) FROM likes WHERE post_id = ?",
        (post_id,)
    )
    likes_count = c.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({
        "action": action,
        "likes_count": likes_count
    })

@app.route("/posts/<int:post_id>/comments", methods=["GET"])
def get_all_comments(post_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT c.comment_id, c.content, c.created_at, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.post_id = ?
        ORDER BY c.created_at DESC
    """, (post_id,))

    rows = c.fetchall()

    # Convert tuples to dict manually
    comments = [
        {
            "comment_id": row[0],
            "content": row[1],
            "created_at": row[2],
            "username": row[3]
        }
        for row in rows
    ]

    conn.close()
    return jsonify(comments)


@app.route("/posts/<int:post_id>/comments", methods=["GET"])
def get_comments(post_id):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT c.comment_id, c.content, c.created_at, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.user_id
        WHERE c.post_id = ?
        ORDER BY c.created_at DESC
    """, (post_id,))

    rows = c.fetchall()

    comments = [
        {
            "comment_id": row[0],
            "content": row[1],
            "created_at": row[2],
            "username": row[3]
        }
        for row in rows
    ]

    conn.close()
    return jsonify(comments)

@app.route("/posts/<int:post_id>/comments/me", methods=["GET"])
def get_my_comment(post_id):
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({"comment": None})

    conn = get_connection()
    c = conn.cursor()

    # Fetch the user's comment (if any)
    c.execute("""
        SELECT comment_id, content, created_at
        FROM comments
        WHERE post_id = ? AND user_id = ?
    """, (post_id, user_id))

    row = c.fetchone()
    conn.close()

    if row:
        # Return the comment as a dict
        return jsonify({
            "comment": {
                "comment_id": row[0],
                "content": row[1],
                "created_at": row[2]
            }
        })
    else:
        return jsonify({"comment": None})



@app.route("/posts/<int:post_id>/comments", methods=["POST"])
def add_comment(post_id):
    data = request.get_json()

    user_id = data.get("user_id")
    content = data.get("content", "").strip()

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 401

    if not content:
        return jsonify({"error": "Comment cannot be empty"}), 400

    conn = get_connection() 
    c = conn.cursor()

    c.execute("""
        SELECT 1 FROM comments
        WHERE post_id = ? AND user_id = ?
    """, (post_id, user_id))

    exists = c.fetchone()

    if exists:
        conn.close()
        return jsonify({"error": "User already commented"}), 409

    c.execute("""
        INSERT INTO comments (post_id, user_id, content)
        VALUES (?, ?, ?)
    """, (post_id, user_id, content))

    conn.commit()
    conn.close()

    return jsonify({"message": "Comment added"}), 201


@app.route("/posts/<int:post_id>/comments/me", methods=["GET"])
def has_commented(post_id):
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({"commented": False})

    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT 1 FROM comments
        WHERE post_id = ? AND user_id = ?
    """, (post_id, user_id))

    exists = c.fetchone() is not None
    conn.close()

    return jsonify({"commented": exists})


@app.route("/posts/<int:post_id>/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(post_id, comment_id):
    user_id = request.args.get("user_id", type=int)

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 401

    conn = get_connection()
    c = conn.cursor()

    # Ensure user owns this comment
    c.execute("""
        SELECT 1 FROM comments
        WHERE comment_id = ? AND user_id = ? AND post_id = ?
    """, (comment_id, user_id, post_id))
    exists = c.fetchone()

    if not exists:
        conn.close()
        return jsonify({"error": "Comment not found or unauthorized"}), 404

    # Delete comment
    c.execute("""
        DELETE FROM comments
        WHERE comment_id = ? AND user_id = ? AND post_id = ?
    """, (comment_id, user_id, post_id))
    conn.commit()
    conn.close()

    return jsonify({"message": "Comment deleted"}), 200

@app.route("/posts/<int:post_id>/favorite", methods=["POST"])
def toggle_favorite(post_id):
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "Missing user_id"}), 400

    conn = get_connection()
    c = conn.cursor()

    # Check if already favorited
    c.execute(
        "SELECT 1 FROM favorites WHERE user_id = ? AND post_id = ?",
        (user_id, post_id)
    )
    favorited = c.fetchone()

    if favorited:
        # Remove from favorites
        c.execute(
            "DELETE FROM favorites WHERE user_id = ? AND post_id = ?",
            (user_id, post_id)
        )
        action = "removed"
    else:
        # Add to favorites
        c.execute(
            "INSERT INTO favorites (user_id, post_id) VALUES (?, ?)",
            (user_id, post_id)
        )
        action = "added"

    # Optional: get updated count
    c.execute(
        "SELECT COUNT(*) FROM favorites WHERE post_id = ?",
        (post_id,)
    )
    fav_count = c.fetchone()[0]

    conn.commit()
    conn.close()

    return jsonify({
        "action": action,
        "favorites_count": fav_count
    })

@app.route("/pantuns/favorites", methods=["GET"])
def get_user_favorites():
    user_id = request.args.get("user_id", type=int)
    if not user_id:
        return jsonify([])

    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT p.pantun_id, p.title, p.tags, p.line1, p.line2, p.line3, p.line4,
               u.username, po.post_id,
               (SELECT COUNT(*) FROM likes l WHERE l.post_id = po.post_id) AS likes_count,
               (SELECT COUNT(*) FROM comments c WHERE c.post_id = po.post_id) AS comments_count,
               (SELECT AVG(r.rating) FROM pantun_rating r WHERE r.pantun_id = p.pantun_id) AS rating_avg
        FROM pantun p
        JOIN posts po ON po.pantun_id = p.pantun_id
        JOIN users u ON u.user_id = po.user_id
        JOIN favorites f ON f.post_id = po.post_id
        WHERE f.user_id = ?
        ORDER BY po.created_at DESC
    """, (user_id,))
    data = c.fetchall()
    conn.close()

    result = []
    for row in data:
        result.append({
            "pantun_id": row[0],
            "title": row[1],
            "tags": row[2],
            "line1": row[3],
            "line2": row[4],
            "line3": row[5],
            "line4": row[6],
            "username": row[7],
            "post_id": row[8],
            "likes_count": row[9],
            "comments_count": row[10],
            "rating_avg": row[11],
            "isFav": True  # always true because they are favorites
        })

    return jsonify(result)













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

# ============================================================
# SUBMIT PANTUN + AUTO ANALYSIS
# ============================================================
@app.route('/add_pantun', methods=['POST'])
def add_pantun_route():
    data = request.get_json()

    title = data.get("title", "")
    tag = data.get("tag", "")
    lines = data.get("lines", ["", "", "", ""])

    if len(lines) != 4:
        return jsonify({"error": "Pantun must have exactly 4 lines."}), 400

    # Prepare DB format
    data["line1"], data["line2"], data["line3"], data["line4"] = lines
    data["tag"] = tag  
    data["user_id"] = data.get("user_id", 0)

    # Insert pantun into DB
    pantun_id = add_pantun_to_db(data)

    # Fetch saved pantun from DB
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT line1, line2, line3, line4 FROM pantun WHERE pantun_id=?",
        (pantun_id,)
    )
    pantun = cursor.fetchone()
    conn.close()

    pantun_lines = [pantun[0], pantun[1], pantun[2], pantun[3]]

    # ----- Analysis -----
    all_filled = int(all(line.strip() for line in pantun_lines))
    rhyme_result = RhymeDetector.detect_abab(pantun_lines)
    syllable_counts = [count_syllables(line) for line in pantun_lines]

    cleaned = re.sub(r"[^\w\s]", "", " ".join(pantun_lines).lower())
    keywords = ["nasihat", "baik", "jangan", "hormat", "bijak"]
    moral_detected = int(any(re.search(rf"\b{k}\b", cleaned) for k in keywords))

    rating, auto_score = calculate_rating(
        syllable_counts,
        rhyme_result,
        moral_detected
    )

    # Insert rating into pantun_rating
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
        data["user_id"],
        rating,
        auto_score,
        rhyme_result,
        *syllable_counts,
        all_filled
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "message": "Pantun saved and analyzed.",
        "pantun_id": pantun_id,
        "rhyme": rhyme_result,
        "syllables": syllable_counts,
        "moral_detected": bool(moral_detected),
        "rating": rating,
        "auto_score": auto_score,
        "all_lines_filled": all_filled
    })

@app.route("/pantun/<int:pantun_id>/rating", methods=["GET"])
def get_pantun_rating(pantun_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rating, auto_score FROM pantun_rating WHERE pantun_id = ?
        ORDER BY rating_id DESC LIMIT 1
    """, (pantun_id,))

    result = cursor.fetchone()
    conn.close()

    if not result:
        return jsonify({"rating": 0, "auto_score": 0})

    return jsonify({
        "rating": result[0],
        "auto_score": result[1]
    })





@app.route("/rhyme/<word>")
def rhyme(word):
    return jsonify({
        "word": word,
        "matches": search_same_ending(word, ALL_WORDS)
    })



if __name__ == "__main__":
    app.run(debug=True)
