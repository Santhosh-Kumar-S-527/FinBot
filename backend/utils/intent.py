"""
intent.py — Query intent classifier + direct tool handlers

Intents:
  emi_calculation   → extract loan params and compute EMI directly
  fraud_escalation  → return hardcoded escalation response
  greeting          → return greeting response
  general_banking   → fall through to RAG pipeline
"""

import re
from typing import Optional

# ── Intent keyword maps ────────────────────────────────────────

EMI_KEYWORDS = [
    "emi", "equated monthly", "loan amount", "interest rate", "tenure",
    "calculate emi", "monthly instalment", "monthly payment", "home loan emi",
    "personal loan emi", "car loan emi", "how much emi", "emi for"
]

FRAUD_KEYWORDS = [
    "fraud", "scam", "stolen", "hacked", "unauthorized transaction",
    "money deducted", "suspicious", "phishing", "otp stolen",
    "account compromised", "card stolen", "lost card", "missing money"
]

GREETING_KEYWORDS = [
    "hi", "hello", "hey", "good morning", "good evening",
    "good afternoon", "howdy", "greetings", "what can you do",
    "what do you know", "help me", "who are you"
]

def classify_intent(query: str) -> str:
    """Return one of: emi_calculation | fraud_escalation | greeting | general_banking"""
    q = query.lower().strip()

    if any(kw in q for kw in FRAUD_KEYWORDS):
        return "fraud_escalation"

    if any(kw in q for kw in EMI_KEYWORDS):
        return "emi_calculation"

    if q in GREETING_KEYWORDS or any(q.startswith(kw) for kw in GREETING_KEYWORDS):
        return "greeting"

    return "general_banking"


# ── EMI Calculator ─────────────────────────────────────────────

def _extract_number(text: str, *patterns) -> Optional[float]:
    """Try multiple regex patterns and return the first match as float."""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Remove commas from Indian number format
            return float(match.group(1).replace(",", ""))
    return None

def _calculate_emi(principal: float, annual_rate: float, months: int) -> dict:
    """Core EMI formula: EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]"""
    if annual_rate == 0:
        emi = principal / months
        return {
            "emi":            round(emi, 2),
            "total_payment":  round(emi * months, 2),
            "total_interest": 0.0,
            "principal":      principal,
            "rate":           0,
            "months":         months
        }

    R = annual_rate / 12 / 100
    N = months
    emi = (principal * R * (1 + R) ** N) / ((1 + R) ** N - 1)
    total = emi * N

    return {
        "emi":            round(emi, 2),
        "total_payment":  round(total, 2),
        "total_interest": round(total - principal, 2),
        "principal":      principal,
        "rate":           annual_rate,
        "months":         months
    }

def _format_inr(amount: float) -> str:
    """Format number in Indian style: 1,00,000"""
    s = str(int(amount))
    if len(s) <= 3:
        return s
    result = s[-3:]
    s = s[:-3]
    while len(s) > 2:
        result = s[-2:] + "," + result
        s = s[:-2]
    if s:
        result = s + "," + result
    return result

def handle_emi(query: str) -> dict:
    """
    Try to extract P, R, N from the query and compute EMI.
    Returns {answer, tool_used, params} or falls back to general_banking.
    """
    q = query.lower()

    # Extract principal (loan amount)
    principal = _extract_number(q,
        r"(?:rs\.?|inr|rupees?)[\s]*([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)?",
        r"([\d,]+(?:\.\d+)?)\s*(?:lakh|lac)\s*(?:loan|rupees?|rs)?",
        r"loan\s+(?:of\s+)?(?:rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)",
        r"([\d,]+(?:\.\d+)?)\s*(?:rs|rupees?)"
    )

    # Convert lakh
    if principal and any(w in q for w in ["lakh", "lac"]):
        if principal < 1000:   # e.g. "20 lakh" → 20,00,000
            principal = principal * 100000

    # Extract interest rate
    rate = _extract_number(q,
        r"([\d.]+)\s*%\s*(?:p\.?a\.?|per\s+annum|interest|rate)?",
        r"(?:rate|interest)\s+(?:of\s+)?([\d.]+)",
        r"@\s*([\d.]+)"
    )

    # Extract tenure (prefer years, convert to months)
    tenure_years = _extract_number(q,
        r"([\d.]+)\s*year",
        r"([\d.]+)\s*yr"
    )
    tenure_months = _extract_number(q,
        r"([\d.]+)\s*month"
    )

    months = None
    if tenure_years:
        months = int(tenure_years * 12)
    elif tenure_months:
        months = int(tenure_months)

    # If we have all 3 params, calculate
    if principal and rate and months:
        result = _calculate_emi(principal, rate, months)
        answer = (
            f"**EMI Calculation Result**\n\n"
            f"Loan Amount: Rs. {_format_inr(result['principal'])}\n"
            f"Interest Rate: {result['rate']}% p.a.\n"
            f"Tenure: {result['months']} months ({result['months']//12} years)\n\n"
            f"**Monthly EMI: Rs. {_format_inr(result['emi'])}**\n\n"
            f"Total Payment: Rs. {_format_inr(result['total_payment'])}\n"
            f"Total Interest: Rs. {_format_inr(result['total_interest'])}\n\n"
            f"_Formula used: EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]_"
        )
        return {
            "answer":     answer,
            "tool_used":  "emi_calculator",
            "escalated":  False,
            "sources":    ["EMI Calculator"],
            "params":     result
        }

    # Partial params — ask for what's missing
    missing = []
    if not principal: missing.append("loan amount (e.g. Rs. 10 lakh)")
    if not rate:      missing.append("interest rate (e.g. 8.5%)")
    if not months:    missing.append("tenure (e.g. 20 years)")

    answer = (
        "I can calculate your EMI! Please provide the following details:\n\n"
        + "\n".join(f"- {m}" for m in missing)
        + "\n\nExample: _Calculate EMI for Rs. 10 lakh loan at 8.5% for 20 years_"
    )

    return {
        "answer":    answer,
        "tool_used": "emi_calculator_prompt",
        "escalated": False,
        "sources":   [],
        "params":    {}
    }


# ── Fraud Escalation ───────────────────────────────────────────

ESCALATION_RESPONSE = {
    "answer": (
        "**⚠️ This sounds like a fraud or security issue — act immediately:**\n\n"
        "1. **Block your card/account** — Call your bank's 24x7 helpline right now\n"
        "2. **Do NOT share OTP, PIN, or passwords** with anyone, including people claiming to be bank officials\n"
        "3. **Report cybercrime** — Call **1930** (Cyber Crime Helpline) or visit www.cybercrime.gov.in\n"
        "4. **RBI Helpline** — Call **14440** for banking fraud complaints\n"
        "5. **File a police complaint** at your nearest station or online at cybercrime.gov.in\n\n"
        "**Zero Liability Rule:** If you report within 3 working days, you are not liable for unauthorized transactions.\n\n"
        "_Please act quickly — every minute matters in fraud cases._"
    ),
    "tool_used":  "fraud_escalation",
    "escalated":  True,
    "sources":    ["RBI Fraud Guidelines"],
    "params":     {}
}


# ── Greeting ───────────────────────────────────────────────────

GREETING_RESPONSE = {
    "answer": (
        "Hello! I'm **FinBot**, your AI-powered banking assistant.\n\n"
        "I can help you with:\n"
        "- **Loans** — home, personal, car loan queries\n"
        "- **EMI calculation** — just tell me the amount, rate, and tenure\n"
        "- **KYC** — documents, process, V-KYC\n"
        "- **Transfers** — NEFT, RTGS, IMPS, UPI limits and charges\n"
        "- **Credit score** — CIBIL score and how to improve it\n"
        "- **FD/RD** — interest, premature withdrawal, taxation\n"
        "- **Fraud** — immediate steps and helpline numbers\n\n"
        "How can I assist you today?"
    ),
    "tool_used":  "greeting",
    "escalated":  False,
    "sources":    [],
    "params":     {}
}