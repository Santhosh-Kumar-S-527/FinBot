import os
import fitz  # PyMuPDF  # type: ignore
import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()

CHROMA_DIR   = os.getenv("CHROMA_PERSIST_DIR", "./vectorstore")
COLLECTION   = "finbot_docs"
CHUNK_SIZE   = 500   # characters per chunk
CHUNK_OVERLAP = 80   # overlap between chunks

# Use sentence-transformers (free, no API key needed for embeddings)
_embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

def _get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(
        name=COLLECTION,
        embedding_function=_embed_fn,
        metadata={"hnsw:space": "cosine"}
    )

def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start  = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end].strip())
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c for c in chunks if len(c) > 50]  # drop tiny leftovers

def ingest_pdf(pdf_path: str) -> dict:
    """
    Extract text from a PDF, chunk it, embed it, and store in ChromaDB.
    Returns a summary dict with doc name and chunk count.
    """
    doc      = fitz.open(pdf_path)
    filename = os.path.basename(pdf_path)
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    doc.close()

    if not full_text.strip():
        return {"file": filename, "chunks": 0, "status": "empty — no text found"}

    chunks     = _chunk_text(full_text)
    collection = _get_collection()

    # Build unique IDs so re-ingesting same file doesn't duplicate
    ids        = [f"{filename}::chunk::{i}" for i in range(len(chunks))]
    metadatas  = [{"source": filename, "chunk_index": i} for i in range(len(chunks))]

    # Upsert (safe to re-run)
    collection.upsert(documents=chunks, ids=ids, metadatas=metadatas)

    return {"file": filename, "chunks": len(chunks), "status": "ok"}

def retrieve_context(query: str, top_k: int = 5) -> list[dict]:
    """
    Embed the query and retrieve top-k relevant chunks from ChromaDB.
    Returns list of {text, source, score}.
    """
    collection = _get_collection()
    results    = collection.query(
        query_texts=[query],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunks.append({
            "text":   doc,
            "source": meta.get("source", "unknown"),
            "score":  round(1 - dist, 3)   # cosine similarity
        })

    return chunks
