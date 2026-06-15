import "./ChatMessage.css";

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/_(.*?)_/g, "<em>$1</em>")
    .replace(/^- (.+)$/gm, "<li>$1</li>")
    .replace(/(<li>[\s\S]*<\/li>)/g, "<ul>$1</ul>")
    .replace(/\n/g, "<br/>");
}

const INTENT_META = {
  emi_calculation:  { label: "EMI Calculator", color: "#22c55e", icon: "🧮" },
  fraud_escalation: { label: "Fraud Alert",    color: "#f59e0b", icon: "⚠️" },
  greeting:         { label: "Welcome",        color: "#8b90a0", icon: "👋" },
  general_banking:  { label: "Banking FAQ",    color: "#4f8ef7", icon: "🏦" },
  rag:              { label: "Banking FAQ",    color: "#4f8ef7", icon: "🏦" },
};

export default function ChatMessage({ msg, showFollowups, onFollowup }) {
  const isUser = msg.role === "user";
  const meta   = msg.intent ? (INTENT_META[msg.intent] || INTENT_META["rag"]) : null;

  return (
    <div className={`message-row ${isUser ? "user" : "bot"}`}>
      {!isUser && <div className="avatar bot-avatar">₹</div>}

      <div className="bubble-col">
        <div className={`bubble ${isUser ? "user-bubble" : "bot-bubble"} ${msg.escalated ? "escalated" : ""}`}>

          {/* Intent badge */}
          {!isUser && meta && (
            <div className="intent-badge" style={{ borderColor: meta.color, color: meta.color }}>
              <span>{meta.icon}</span> {meta.label}
            </div>
          )}

          <div
            className="bubble-text"
            dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
          />

          {/* EMI result card */}
          {msg.params?.emi && (
            <div className="emi-card">
              <div className="emi-highlight">
                <span className="emi-label">Monthly EMI</span>
                <span className="emi-value">Rs. {msg.params.emi.toLocaleString("en-IN")}</span>
              </div>
              <div className="emi-row">
                <span>Total Payment</span>
                <span>Rs. {msg.params.total_payment.toLocaleString("en-IN")}</span>
              </div>
              <div className="emi-row">
                <span>Total Interest</span>
                <span>Rs. {msg.params.total_interest.toLocaleString("en-IN")}</span>
              </div>
              <div className="emi-row">
                <span>Principal</span>
                <span>Rs. {msg.params.principal.toLocaleString("en-IN")}</span>
              </div>
            </div>
          )}

          {/* Escalation banner */}
          {msg.escalated && (
            <div className="escalation-banner">
              <span className="escalation-icon">🚨</span>
              <div>
                <strong>Act immediately</strong>
                <p>Call RBI Helpline: <strong>14440</strong> · Cyber Crime: <strong>1930</strong></p>
              </div>
            </div>
          )}

          {/* Source pills */}
          {msg.sources?.length > 0 && (
            <div className="sources">
              <span className="sources-label">Source:</span>
              {msg.sources.map((s, i) => (
                <span key={i} className="source-pill">{s}</span>
              ))}
            </div>
          )}
        </div>

        {/* Follow-up chips — only on last bot message */}
        {showFollowups && (
          <div className="followups">
            <span className="followups-label">You might also ask:</span>
            <div className="followup-chips">
              {msg.followups.map((q, i) => (
                <button key={i} className="followup-chip" onClick={() => onFollowup(q)}>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {isUser && <div className="avatar user-avatar">S</div>}
    </div>
  );
}