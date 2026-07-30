"""
timetable.py
------------
API endpoint for generating a personalized study timetable.
"""

from flask import Blueprint, request, jsonify
from services.scheduler_service import generate_timetable

timetable_bp = Blueprint("timetable", __name__, url_prefix="/api/timetable")


@timetable_bp.route("/generate", methods=["POST"])
def generate_timetable_route():
    """
    Expected JSON body:
    {
        "subjects": [
            {"name": "Math", "exam_date": "2026-08-15", "priority": "high"},
            {"name": "Physics", "exam_date": "2026-08-20", "priority": "medium"}
        ],
        "hours_per_day": 4
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    subjects = data.get("subjects")
    hours_per_day = data.get("hours_per_day")

    if not subjects or not isinstance(subjects, list):
        return jsonify({"error": "Please add at least one subject"}), 400

    if not hours_per_day or not isinstance(hours_per_day, (int, float)) or hours_per_day <= 0:
        return jsonify({"error": "hours_per_day must be a positive number"}), 400

    try:
        schedule = generate_timetable(subjects, hours_per_day)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Timetable generation error: {e}")
        return jsonify({"error": "Failed to generate timetable"}), 500

    return jsonify({"schedule": schedule}), 200