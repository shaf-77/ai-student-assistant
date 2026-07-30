"""
embedding_service.py
---------------------
Handles chunking, embedding, and FAISS-based vector search.

IMPORTANT CHANGE: the SentenceTransformer model is now loaded LAZILY
(only the first time it's actually needed), not at import time.

Why this matters:
- Previously, `embedding_model = SentenceTransformer(...)` ran the moment
  this file was imported -- which happens during Flask app startup.
- If the Hugging Face download/handshake fails (e.g. due to a dependency
  mismatch), the ENTIRE app crashes before Flask even starts, with no
  chance to serve a helpful error page.
- Lazy loading defers this to the first real embedding request, so:
    1. Flask starts up instantly regardless of model-loading issues
    2. Any failure is caught and reported clearly, in context, instead
       of crashing the whole process at import time
    3. If a route that doesn't need embeddings is hit first, the app
       never even pays the loading cost for that request
"""

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 384

# NOTE: we do NOT instantiate SentenceTransformer here anymore.
# This global starts as None and is filled in on first use.
_embedding_model = None


def get_embedding_model():
    """
    Returns the shared SentenceTransformer instance, loading it on
    first call only. All later calls reuse the same loaded model.
    """
    global _embedding_model

    if _embedding_model is None:
        print("⏳ Loading embedding model (first use)...")
        try:
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            print("✅ Embedding model loaded")
        except Exception as e:
            # Surface a clear, actionable error instead of a raw crash trace
            print(f"❌ Failed to load embedding model: {e}")
            raise RuntimeError(
                "Could not load the embedding model. This is usually a "
                "dependency/version mismatch (see requirements.txt) or a "
                "network issue reaching Hugging Face."
            ) from e

    return _embedding_model


def chunk_text(text, chunk_size=200, overlap=30):
    """
    Splits a long text into overlapping word chunks.
    (Unchanged from before -- no dependency on the model itself.)
    """
    words = text.split()
    chunks = []

    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


class VectorStore:
    """
    Wraps a FAISS index + metadata list together.
    """

    def __init__(self):
        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.metadata = []

    def _embed(self, texts):
        """
        Converts a list of strings into normalized embedding vectors.
        Calls get_embedding_model() instead of using a module-level
        variable directly -- this is what triggers the lazy load.
        """
        model = get_embedding_model()
        vectors = model.encode(texts, convert_to_numpy=True)
        faiss.normalize_L2(vectors)
        return vectors

    def add_note(self, note_id, content):
        chunks = chunk_text(content)
        if not chunks:
            return

        vectors = self._embed(chunks)
        self.index.add(vectors)

        for chunk in chunks:
            self.metadata.append({"note_id": note_id, "chunk_text": chunk})

    def remove_note(self, note_id):
        """
        Removes all chunks belonging to a specific note, rebuilding the
        index from the remaining chunks (IndexFlatIP has no direct delete).
        """
        remaining_metadata = [m for m in self.metadata if m["note_id"] != note_id]

        self.index = faiss.IndexFlatIP(EMBEDDING_DIM)
        self.metadata = []

        if remaining_metadata:
            texts = [m["chunk_text"] for m in remaining_metadata]
            vectors = self._embed(texts)
            self.index.add(vectors)
            self.metadata = remaining_metadata

    def search(self, query, top_k=5, note_id=None):
        if self.index.ntotal == 0:
            return []

        query_vector = self._embed([query])

        search_k = min(top_k * 4, self.index.ntotal)
        scores, indices = self.index.search(query_vector, search_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue

            meta = self.metadata[idx]

            if note_id is not None and meta["note_id"] != note_id:
                continue

            results.append({
                "note_id": meta["note_id"],
                "chunk_text": meta["chunk_text"],
                "score": float(score)
            })

            if len(results) >= top_k:
                break

        return results


# One single shared vector store instance for the whole app.
# Creating a VectorStore() no longer loads the embedding model --
# that only happens the first time .add_note() or .search() is called.
vector_store = VectorStore()


def rebuild_index_from_db():
    """
    Rebuilds the entire FAISS index from whatever is currently in the database.
    Called once when the Flask app starts up.

    NOTE: if there are zero notes in the database, this function returns
    early WITHOUT touching the embedding model at all -- so on a fresh
    install, Flask can start up without ever loading the model until
    the user actually uploads something or asks a question.
    """
    from models.note import get_all_notes

    global vector_store
    vector_store = VectorStore()

    notes = get_all_notes()
    if not notes:
        print("✅ Vector index ready (0 notes -- embedding model not loaded yet)")
        return

    for note in notes:
        vector_store.add_note(note["id"], note["content"])

    print(f"✅ Vector index rebuilt with {len(notes)} note(s)")