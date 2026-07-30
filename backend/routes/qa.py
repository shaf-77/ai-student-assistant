"""
qa.py
-----
API endpoint for asking questions about uploaded notes (RAG feature).
"""

from flask import Blueprint, request, jsonify
from services.embedding_service import vector_store
from services.ai_service import answer_question_from_context

qa_bp = Blueprint("qa", __name__, url_prefix="/api/qa")

# Minimum similarity score to consider a chunk "relevant enough".
# Cosine similarity ranges roughly from -1 to 1; below this, the chunk
# is probably unrelated to the question.
RELEVANCE_THRESHOLD = 0.3


@qa_bp.route("/ask", methods=["POST"])
def ask_question():
    """
    Expected JSON body:
    {
        "question": "What is Newton's second law?",
        "note_id": 3          <- optional. If omitted, searches ALL notes.
    }
    """
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400

    question = data.get("question", "").strip()
    note_id = data.get("note_id")  # may be None

    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    # 1. Search FAISS for relevant chunks
    results = vector_store.search(question, top_k=5, note_id=note_id)
    print("Vector count:", vector_store.index.ntotal)
    print("DEBUG - search results:", results)   # TEMPORARY - helps us debug
    # 2. Filter out weak/irrelevant matches
    relevant_chunks = [r["chunk_text"] for r in results if r["score"] >= RELEVANCE_THRESHOLD]

    # 3. Ask Gemini to answer using only those chunks
    try:
        answer = answer_question_from_context(question, relevant_chunks)
    except Exception:
        return jsonify({"error": "Failed to generate an answer. Please try again."}), 500

    return jsonify({
        "question": question,
        "answer": answer,
        "sources_used": len(relevant_chunks)
    }), 200