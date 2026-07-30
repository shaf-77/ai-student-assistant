"""
quiz.py
-------
API endpoint for generating quiz questions from a note.
"""

from flask import Blueprint, request, jsonify
from models.note import get_note_by_id
from services.ai_service import generate_quiz

quiz_bp = Blueprint("quiz", __name__, url_prefix="/api/quiz")

VALID_TYPES = {"mcq", "short_answer", "mixed"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}


@quiz_bp.route("/generate", methods=["POST"])
def generate_quiz_route():
    """
    Expected JSON body:
    {
        "note_id": 3,
        "question_type": "mcq" | "short_answer" | "mixed",
        "difficulty": "easy" | "medium" | "hard",
        "num_questions": 5   (optional, defaults to 5)
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    note_id = data.get("note_id")
    question_type = data.get("question_type")
    difficulty = data.get("difficulty")
    num_questions = data.get("num_questions", 5)

    # ---- Validation ----
    if not note_id:
        return jsonify({"error": "note_id is required"}), 400

    if question_type not in VALID_TYPES:
        return jsonify({"error": f"question_type must be one of {sorted(VALID_TYPES)}"}), 400

    if difficulty not in VALID_DIFFICULTIES:
        return jsonify({"error": f"difficulty must be one of {sorted(VALID_DIFFICULTIES)}"}), 400

    if not isinstance(num_questions, int) or not (1 <= num_questions <= 15):
        return jsonify({"error": "num_questions must be an integer between 1 and 15"}), 400

    # ---- Fetch the note ----
    note = get_note_by_id(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404

    # ---- Generate the quiz ----
    try:
        questions = generate_quiz(note["content"], question_type, difficulty, num_questions)
    except ValueError as e:
        # Known error (bad JSON from AI) -> friendly message
        return jsonify({"error": str(e)}), 502
    except Exception:
        return jsonify({"error": "Failed to generate quiz. Please try again."}), 500

    return jsonify({
        "note_id": note_id,
        "note_title": note["title"],
        "difficulty": difficulty,
        "questions": questions
    }), 200