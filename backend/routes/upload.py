import os
from flask import Blueprint, request, jsonify
from utils.rag import ingest_pdf
from dotenv import load_dotenv

load_dotenv()

upload_bp   = Blueprint("upload", __name__)
UPLOAD_DIR  = os.getenv("UPLOAD_FOLDER", "./data/docs")
ALLOWED_EXT = {"pdf"}

os.makedirs(UPLOAD_DIR, exist_ok=True)

def _allowed(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT

@upload_bp.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not _allowed(file.filename):
        return jsonify({"error": "Only PDF files are accepted"}), 415

    save_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(save_path)

    # Ingest into ChromaDB
    result = ingest_pdf(save_path)

    return jsonify({
        "message": f"Ingested {result['chunks']} chunks from {result['file']}",
        "status":  result["status"]
    })

@upload_bp.route("/docs", methods=["GET"])
def list_docs():
    files = [f for f in os.listdir(UPLOAD_DIR) if f.endswith(".pdf")]
    return jsonify({"documents": files, "count": len(files)})
