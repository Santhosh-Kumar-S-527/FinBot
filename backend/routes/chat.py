from flask import Blueprint, request, jsonify
from utils.rag    import retrieve_context
from utils.llm    import generate_answer
from utils.db     import save_message, get_history
from utils.intent import (
    classify_intent,
    handle_emi,
    ESCALATION_RESPONSE,
    GREETING_RESPONSE
)
import uuid

chat_bp = Blueprint("chat", __name__)

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data       = request.get_json(silent=True) or {}
    query      = (data.get("message") or "").strip()
    session_id = data.get("session_id") or str(uuid.uuid4())

    if not query:
        return jsonify({"error": "message is required"}), 400

    # ── Step 1: Classify intent ──────────────────────────────
    intent = classify_intent(query)

    # ── Step 2: Route to the right handler ──────────────────
    if intent == "greeting":
        result = GREETING_RESPONSE

    elif intent == "fraud_escalation":
        result = ESCALATION_RESPONSE

    elif intent == "emi_calculation":
        result = handle_emi(query)
        # If EMI params incomplete, fall through to RAG for context
        if result["tool_used"] == "emi_calculator_prompt":
            pass  # keep the prompt-for-params response

    else:
        # general_banking → RAG pipeline
        history = get_history(session_id)
        chunks  = retrieve_context(query, top_k=5)
        result  = generate_answer(query, chunks, chat_history=history)
        result["tool_used"] = "rag"

    # ── Step 3: Persist to MongoDB (skip greetings) ─────────
    if intent != "greeting":
        save_message(session_id, "user",      query)
        save_message(session_id, "assistant", result["answer"])

    return jsonify({
        "session_id": session_id,
        "answer":     result["answer"],
        "sources":    result.get("sources",   []),
        "escalated":  result.get("escalated", False),
        "intent":     intent,
        "tool_used":  result.get("tool_used", "rag")
    })

@chat_bp.route("/history/<session_id>", methods=["GET"])
def history(session_id):
    messages = get_history(session_id, limit=50)
    return jsonify({"session_id": session_id, "messages": messages})