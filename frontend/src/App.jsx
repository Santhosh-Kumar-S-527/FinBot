import { useState, useRef, useEffect } from "react";
import ChatMessage from "./components/ChatMessage";
import TypingIndicator from "./components/TypingIndicator";
import AdminUpload from "./components/AdminUpload";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

const SIDEBAR_SUGGESTIONS = [
  "What documents are needed for a home loan?",
  "Calculate EMI for 20 lakh at 8.5% for 20 years",
  "What is CIBIL score and how to improve it?",
  "Difference between NEFT, RTGS and IMPS?",
  "How to open a Fixed Deposit?",
];

const FOLLOWUPS = {
  emi_calculation: [
    "What documents are needed for a home loan?",
    "What is the maximum loan amount I can get?",
    "What is a prepayment penalty?",
  ],
  general_banking: [
    "Can you explain this in simpler terms?",
    "What are the RBI guidelines on this?",
    "How does this affect my credit score?",
  ],
  fraud_escalation: [
    "What is the RBI Banking Ombudsman?",
    "How long does the bank have to resolve my complaint?",
    "What is my liability for unauthorized transactions?",
  ],
  greeting: [
    "Calculate EMI for 10 lakh at 9% for 5 years",
    "What is KYC and what documents do I need?",
    "What is the difference between NEFT and IMPS?",
  ],
};

const WELCOME_MSG = {
  role:      "assistant",
  content:   "Hello! I'm **FinBot**, your AI-powered banking assistant.\n\nI can help with loans, KYC, EMI calculations, transfers, credit scores, and more.\n\nHow can I assist you today?",
  sources:   [],
  escalated: false,
  intent:    "greeting",
  followups: FOLLOWUPS.greeting,
};

export default function App() {
  const [messages,     setMessages]     = useState([WELCOME_MSG]);
  const [input,        setInput]        = useState("");
  const [loading,      setLoading]      = useState(false);
  const [sessionId,    setSessionId]    = useState(null);
  const [showAdmin,    setShowAdmin]    = useState(false);
  const [sidebarOpen,  setSidebarOpen]  = useState(false);  // mobile hamburger
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function newSession() {
    setMessages([WELCOME_MSG]);
    setSessionId(null);
    setInput("");
    setSidebarOpen(false);
    inputRef.current?.focus();
  }

  async function sendMessage(text) {
    const query = (text || input).trim();
    if (!query || loading) return;

    setInput("");
    setSidebarOpen(false);
    inputRef.current?.focus();
    setMessages(prev => [...prev, { role: "user", content: query }]);
    setLoading(true);

    try {
      const res  = await fetch(`${API}/chat`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ message: query, session_id: sessionId }),
      });
      const data = await res.json();
      if (!sessionId) setSessionId(data.session_id);

      const intent = data.intent || "general_banking";

      setMessages(prev => [...prev, {
        role:      "assistant",
        content:   data.answer,
        sources:   data.sources   || [],
        escalated: data.escalated || false,
        intent,
        params:    data.params    || null,
        followups: FOLLOWUPS[intent] || FOLLOWUPS.general_banking,
      }]);
    } catch {
      setMessages(prev => [...prev, {
        role:      "assistant",
        content:   "⚠️ Unable to reach the server. Please check your connection and try again.",
        sources:   [],
        escalated: false,
      }]);
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const lastBotIdx = [...messages]
    .map((m, i) => m.role === "assistant" ? i : -1)
    .filter(i => i >= 0).at(-1);

  const SidebarContent = () => (
    <>
      <div className="logo">
        <span className="logo-icon">₹</span>
        <span className="logo-text">FinBot</span>
      </div>
      <p className="logo-sub">AI Banking Assistant</p>

      <div className="sidebar-section">
        <p className="sidebar-label">Quick Questions</p>
        {SIDEBAR_SUGGESTIONS.map((s, i) => (
          <button key={i} className="suggestion-btn" onClick={() => sendMessage(s)}>
            {s}
          </button>
        ))}
      </div>

      <div className="sidebar-section sidebar-bottom">
        <button className="new-session-btn" onClick={newSession}>
          ✦ New Conversation
        </button>
        <button className="admin-btn" onClick={() => setShowAdmin(v => !v)}>
          {showAdmin ? "✕ Close Admin" : "⚙ Admin Upload"}
        </button>
        {showAdmin && <AdminUpload api={API} />}
      </div>
    </>
  );

  return (
    <div className="app">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* Sidebar — desktop always visible, mobile slide-in */}
      <aside className={`sidebar ${sidebarOpen ? "sidebar-mobile-open" : ""}`}>
        <SidebarContent />
      </aside>

      {/* Chat area */}
      <main className="chat-area">
        <header className="chat-header">
          {/* Hamburger — mobile only */}
          <button className="hamburger" onClick={() => setSidebarOpen(v => !v)}>
            <span /><span /><span />
          </button>

          <div className="header-dot" />
          <span className="header-title">FinBot is online</span>

          <div className="header-right">
            <button className="new-chat-btn" onClick={newSession} title="New conversation">
              ✦ New
            </button>
            <span className="session-badge">
              {sessionId ? `Session: ${sessionId.slice(0, 8)}…` : "New session"}
            </span>
          </div>
        </header>

        <div className="messages">
          {messages.map((msg, i) => (
            <ChatMessage
              key={i}
              msg={msg}
              showFollowups={!loading && i === lastBotIdx && msg.followups?.length > 0}
              onFollowup={sendMessage}
            />
          ))}
          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        <div className="input-area">
          <textarea
            ref={inputRef}
            className="chat-input"
            placeholder="Ask about loans, KYC, transfers, credit score…"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            rows={1}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
          >
            ↑
          </button>
        </div>
        <p className="disclaimer">
          FinBot provides general information only. For specific advice, contact your bank directly.
        </p>
      </main>
    </div>
  );
}