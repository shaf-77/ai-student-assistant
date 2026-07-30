"""
summary.py
----------
API endpoint for generating summaries of a note.
"""

from flask import Blueprint, request, jsonify
from models.note import get_note_by_id
from services.ai_service import summarize_note

summary_bp = Blueprint("summary", __name__, url_prefix="/api/summary")

VALID_TYPES = {"short", "detailed", "bullet"}


@summary_bp.route("/generate", methods=["POST"])
def generate_summary():
    """
    Expected JSON body:
    {
        "note_id": 3,
        "summary_type": "short" | "detailed" | "bullet"
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    note_id = data.get("note_id")
    summary_type = data.get("summary_type")

    # ---- Validation ----
    if not note_id:
        return jsonify({"error": "note_id is required"}), 400

    if summary_type not in VALID_TYPES:
        return jsonify({
            "error": f"summary_type must be one of {sorted(VALID_TYPES)}"
        }), 400

    # ---- Fetch the note ----
    note = get_note_by_id(note_id)
    if not note:
        return jsonify({"error": "Note not found"}), 404

    # ---- Generate the summary ----
    try:
        summary_text = summarize_note(note["content"], summary_type)
    except Exception:
        return jsonify({"error": "Failed to generate summary. Please try again."}), 500

    return jsonify({
        "note_id": note_id,
        "note_title": note["title"],
        "summary_type": summary_type,
        "summary": summary_text
    }), 200