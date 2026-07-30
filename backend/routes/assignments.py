"""
assignments.py
--------------
API endpoints for managing assignments (create, list, mark complete, delete).
"""

from flask import Blueprint, request, jsonify
from datetime import date
from models.assignment import (
    create_assignment,
    get_all_assignments,
    get_assignment_by_id,
    update_assignment_status,
    delete_assignment
)

assignments_bp = Blueprint("assignments", __name__, url_prefix="/api/assignments")

VALID_STATUSES = {"pending", "completed"}


@assignments_bp.route("", methods=["POST"])
def add_assignment():
    """
    Expected JSON body:
    { "title": "...", "subject": "...", "due_date": "YYYY-MM-DD" }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    title = data.get("title", "").strip()
    subject = data.get("subject", "").strip()
    due_date = data.get("due_date", "").strip()

    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not subject:
        return jsonify({"error": "Subject is required"}), 400

    try:
        date.fromisoformat(due_date)  # validates format is YYYY-MM-DD
    except ValueError:
        return jsonify({"error": "due_date must be in YYYY-MM-DD format"}), 400

    assignment_id = create_assignment(title, subject, due_date)

    return jsonify({
        "message": "Assignment added successfully",
        "assignment_id": assignment_id
    }), 201


@assignments_bp.route("", methods=["GET"])
def list_assignments():
    """
    Returns all assignments, each tagged with a computed 'urgency' field
    (overdue / due_soon / upcoming) so the frontend can highlight them
    without recalculating dates itself.
    """
    assignments = get_all_assignments()
    today = date.today()

    for a in assignments:
        due = date.fromisoformat(a["due_date"])
        days_left = (due - today).days

        if a["status"] == "completed":
            a["urgency"] = "completed"
        elif days_left < 0:
            a["urgency"] = "overdue"
        elif days_left <= 2:
            a["urgency"] = "due_soon"
        else:
            a["urgency"] = "upcoming"

        a["days_left"] = days_left

    return jsonify({"assignments": assignments}), 200


@assignments_bp.route("/<int:assignment_id>/status", methods=["PATCH"])
def change_status(assignment_id):
    """
    Expected JSON body: { "status": "pending" | "completed" }
    Used to mark an assignment complete, or un-complete it.
    """
    data = request.get_json(silent=True)

    if not data or "status" not in data:
        return jsonify({"error": "status is required"}), 400

    status = data["status"]
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {sorted(VALID_STATUSES)}"}), 400

    if not get_assignment_by_id(assignment_id):
        return jsonify({"error": "Assignment not found"}), 404

    update_assignment_status(assignment_id, status)

    return jsonify({"message": f"Assignment marked as {status}"}), 200


@assignments_bp.route("/<int:assignment_id>", methods=["DELETE"])
def remove_assignment(assignment_id):
    if not get_assignment_by_id(assignment_id):
        return jsonify({"error": "Assignment not found"}), 404

    delete_assignment(assignment_id)
    return jsonify({"message": "Assignment deleted"}), 200