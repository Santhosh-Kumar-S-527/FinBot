from flask import Blueprint, jsonify
from utils.rag import _get_collection

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    try:
        col   = _get_collection()
        count = col.count()
        return jsonify({
            "status":      "ok",
            "vectorstore": "connected",
            "doc_chunks":  count
        })
    except Exception as e:
        return jsonify({"status": "degraded", "error": str(e)}), 500
