"""
routes/history.py — Translation history CRUD endpoints.

Improvements:
- clear_all no longer imports get_connection inline
- Consistent JSON responses
- Pagination support (limit/offset)
"""

from flask import Blueprint, request, jsonify
from models.history import (
    get_all_translations,
    toggle_favorite,
    delete_translation,
    save_translation,
    clear_all_translations,
)

history_bp = Blueprint("history", __name__)


@history_bp.route("/", methods=["GET"])
def list_history():
    search = request.args.get("search", "").strip()
    favorite_only = request.args.get("favorite", "false").lower() == "true"
    limit = request.args.get("limit", 100, type=int)
    offset = request.args.get("offset", 0, type=int)
    items = get_all_translations(search, favorite_only, limit, offset)
    return jsonify({"history": items, "count": len(items)})


@history_bp.route("/", methods=["POST"])
def create_history():
    data = request.get_json() or {}
    required = ["original_text", "translated_text", "source_lang", "target_lang"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    row_id = save_translation(data)
    if row_id == 0:
        return jsonify({"id": 0, "message": "Already in history (duplicate skipped)"}), 200
    return jsonify({"id": row_id, "message": "Saved to history"}), 201


@history_bp.route("/<int:item_id>/favorite", methods=["PATCH"])
def favorite(item_id):
    result = toggle_favorite(item_id)
    if result is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"is_favorite": bool(result)})


@history_bp.route("/<int:item_id>", methods=["DELETE"])
def remove(item_id):
    delete_translation(item_id)
    return jsonify({"message": "Deleted"})


@history_bp.route("/clear", methods=["DELETE"])
def clear_all():
    count = clear_all_translations()
    return jsonify({"message": f"Cleared {count} translation(s)"})
