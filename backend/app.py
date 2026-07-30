"""
app.py
------
Entry point of our Flask backend.
"""
from routes.quiz import quiz_bp
from routes.summary import summary_bp
from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database.db import init_db
from routes.upload import upload_bp
from routes.qa import qa_bp   # NEW
from routes.timetable import timetable_bp
from routes.assignments import assignments_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)

    init_db()

    # NEW: Rebuild the FAISS vector index from whatever notes already
    # exist in the database. Important because the index lives in memory
    # and is wiped every time the server restarts.
    from services.embedding_service import rebuild_index_from_db
    rebuild_index_from_db()

    app.register_blueprint(upload_bp)
    app.register_blueprint(qa_bp)   # NEW
    app.register_blueprint(summary_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(assignments_bp) 
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "ok",
            "message": "AI Student Assistant backend is running 🚀"
        }), 200

    return app


if __name__ == "__main__":
    app = create_app()
    # use_reloader=False: avoids double-loading the embedding model on every save,
    # which was causing confusing duplicate startup logs. We still get debug error
    # pages, just not the auto-restart-on-file-change behavior.
    app.run(debug=True, port=5000, use_reloader=False)