import "./TypingIndicator.css";

export default function TypingIndicator() {
  return (
    <div className="message-row bot">
      <div className="avatar bot-avatar">₹</div>
      <div className="bubble bot-bubble typing-bubble">
        <span className="dot" />
        <span className="dot" />
        <span className="dot" />
      </div>
    </div>
  );
}
