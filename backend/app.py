"""
app.py — VaaniSetu Flask application factory.

Improvements:
- Structured logging setup
- CORS tightened (configurable via env)
- Request size limit (16 MB)
- 413 handler for oversized requests
- /api/health returns version and uptime
"""

import os
import logging
import time
from flask import Flask, jsonify, request
from flask_cors import CORS
from config import Config
from models.history import init_db
from routes.translate import translate_bp
from routes.ocr import ocr_bp
from routes.document import document_bp
from routes.history import history_bp
from routes.ai import ai_bp
from routes.slang import slang_bp

_START_TIME = time.time()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB global limit

    # CORS — allow configured origins (default: all for local dev)
    allowed_origins = os.getenv("CORS_ORIGINS", "*")
    origins = [o.strip() for o in allowed_origins.split(",")] if "," in allowed_origins else allowed_origins
    CORS(app, resources={r"/api/*": {"origins": origins}})

    init_db()

    app.register_blueprint(translate_bp, url_prefix="/api/translate")
    app.register_blueprint(ocr_bp,       url_prefix="/api/ocr")
    app.register_blueprint(document_bp,  url_prefix="/api/document")
    app.register_blueprint(history_bp,   url_prefix="/api/history")
    app.register_blueprint(ai_bp,        url_prefix="/api/ai")
    app.register_blueprint(slang_bp,     url_prefix="/api/slang")

    @app.route("/api/health")
    def health():
        return jsonify({
            "status": "ok",
            "service": "VaaniSetu API",
            "version": "2.0.0",
            "uptime_seconds": round(time.time() - _START_TIME, 1),
        })

    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({"error": "Bad request", "detail": str(e)}), 400

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Endpoint not found"}), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify({"error": "Request too large. Maximum upload size is 20 MB."}), 413

    @app.errorhandler(500)
    def server_error(e):
        logger.error("Unhandled server error: %s", e)
        return jsonify({"error": "Internal server error"}), 500

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV", "development") == "development"
    logger.info("Starting VaaniSetu API on port %d (debug=%s)", port, debug)
    app.run(host="0.0.0.0", port=port, debug=debug)
