import logging
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

_model = genai.GenerativeModel(GEMINI_MODEL)

SYSTEM_PROMPT = """You are FinBot, a professional AI assistant for banking and financial queries.
You help customers understand:
- Loan types, eligibility, EMI calculations
- KYC process and documentation
- Account types (savings, current, FD, RD)
- NEFT, RTGS, IMPS transfer rules and limits
- Credit score (CIBIL) information
- Investment basics (mutual funds, SIP)
- Dispute resolution and complaint escalation

RULES:
1. Answer ONLY from the provided context. If the context doesn't have the answer, say:
   "I don't have specific information on that. For accurate details, please contact your bank's helpline or visit the nearest branch."
2. Never give specific financial advice like "You should invest in X."
3. If a query involves legal disputes or fraud, always escalate:
   "For fraud or legal issues, please call RBI Helpline: 14440 or your bank's 24x7 helpline immediately."
4. Keep answers concise, clear, and jargon-free.
5. Always be polite and professional.
"""

def generate_answer(query: str, context_chunks: list[dict], chat_history: list[dict] = None) -> dict:
    """
    Generate a grounded answer using retrieved context.
    Returns {answer, sources, escalated}.
    """
    if not context_chunks:
        return {
            "answer": "I couldn't find relevant information in our knowledge base. "
                      "Please contact your bank's helpline for assistance.",
            "sources": [],
            "escalated": False
        }

    # Build context block
    context_text = "\n\n".join(
        f"[Source: {c['source']}]\n{c['text']}" for c in context_chunks
    )

    # Build conversation history string
    history_text = ""
    if chat_history:
        for msg in chat_history[-6:]:  # last 3 turns
            role = "Customer" if msg["role"] == "user" else "FinBot"
            history_text += f"{role}: {msg['content']}\n"

    prompt = f"""{SYSTEM_PROMPT}

--- KNOWLEDGE BASE CONTEXT ---
{context_text}

--- CONVERSATION SO FAR ---
{history_text}
--- CURRENT QUESTION ---
Customer: {query}

FinBot:"""

    try:
        response = _model.generate_content(prompt)
        answer   = getattr(response, "text", "").strip()
        if not answer:
            raise ValueError("LLM returned empty text")
    except Exception as exc:
        logger.exception("LLM generation failed")
        return {
            "answer": "I'm sorry, I'm having trouble generating an answer right now. Please try again in a moment.",
            "sources": [],
            "escalated": False,
            "error": str(exc)
        }

    # Check if escalation keywords triggered
    escalated = any(kw in answer.lower() for kw in [
        "14440", "helpline", "branch", "fraud", "legal", "rbi"
    ])

    sources = list({c["source"] for c in context_chunks})

    return {
        "answer":    answer,
        "sources":   sources,
        "escalated": escalated
    }
