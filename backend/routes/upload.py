"""
upload.py
---------
API endpoints related to uploading notes.

We use a Flask 'Blueprint' here instead of adding routes directly
to app.py. A Blueprint is like a mini Flask app for one feature area.
This keeps app.py clean as we add quiz.py, summary.py, timetable.py, etc.
"""
from services.embedding_service import vector_store
from flask import Blueprint, request, jsonify
from services.pdf_service import extract_text_from_pdf
from models.note import create_note, get_all_notes
from models.note import get_all_notes, delete_note

# Every route in this file will be prefixed with /api/notes
upload_bp = Blueprint("upload", __name__, url_prefix="/api/notes")


@upload_bp.route("/upload-pdf", methods=["POST"])
def upload_pdf():
    """
    Accepts a PDF file upload (multipart/form-data), extracts its text,
    and saves it as a note in the database.
    """
    # 1. Validate that a file was actually sent
    if "file" not in request.files:
        return jsonify({"error": "No file was uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # 2. Try extracting text from the PDF
    try:
        extracted_text = extract_text_from_pdf(file)
    except ValueError as e:
        # Known, expected error (e.g. scanned PDF) -> friendly message
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        # Unexpected error -> log it, don't leak internals to the user
        print(f"Unexpected PDF error: {e}")
        return jsonify({"error": "Failed to process this PDF file"}), 500

    # 3. Save the note in the database
    title = file.filename.replace(".pdf", "")
    note_id = create_note(
        title=title,
        content=extracted_text,
        source_type="pdf",
        filename=file.filename
    )
    # Add this note to the searchable vector index immediately
    vector_store.add_note(note_id, extracted_text)
    return jsonify({
        "message": "PDF uploaded and processed successfully",
        "note_id": note_id,
        "title": title,
        "preview": extracted_text[:200] + "..."  # short preview for UI
    }), 201


@upload_bp.route("/upload-text", methods=["POST"])
def upload_text():
    """
    Accepts pasted text directly (JSON body) and saves it as a note.
    Expected JSON body: { "title": "...", "content": "..." }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()

    # Basic validation
    if not title:
        return jsonify({"error": "Title is required"}), 400
    if not content:
        return jsonify({"error": "Note content cannot be empty"}), 400
    if len(content) < 10:
        return jsonify({"error": "Note content is too short to be useful"}), 400

    note_id = create_note(
        title=title,
        content=content,
        source_type="text"
    )
    # Add this note to the searchable vector index immediately
    vector_store.add_note(note_id, content)
    return jsonify({
        "message": "Text note saved successfully",
        "note_id": note_id,
        "title": title
    }), 201


@upload_bp.route("", methods=["GET"])
def list_notes():
    """
    Returns all saved notes (used to populate the notes list in the UI).
    """
    notes = get_all_notes()
    return jsonify({"notes": notes}), 200
@upload_bp.route("/<int:note_id>", methods=["DELETE"])
def remove_note(note_id):
    """
    Deletes a note from both the database and the search index.
    """
    deleted = delete_note(note_id)

    if not deleted:
        return jsonify({"error": "Note not found"}), 404

    # Also remove it from FAISS so Q&A can't reference deleted content
    vector_store.remove_note(note_id)

    return jsonify({"message": "Note deleted successfully"}), 200