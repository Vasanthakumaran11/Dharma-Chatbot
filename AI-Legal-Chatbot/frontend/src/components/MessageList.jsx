import { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

const QUICK_STARTS = [
  '🔓 My phone was stolen — how do I file an FIR?',
  '💻 I was scammed online via UPI — what are my rights?',
  '🏠 What legal protection do I have against domestic violence?',
  '📋 How do I file an RTI application with the government?',
];

export default function MessageList({ messages, isLoading, onQuickAction }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  if (messages.length === 0) {
    return (
      <div className="messages-container">
        <div className="welcome-screen">
          <div className="welcome-icon">⚖️</div>
          <div>
            <h2 className="welcome-title">Know Your Rights</h2>
            <p className="welcome-subtitle">
              Dharma is your AI-powered guide to Indian law and police complaint procedures.
              Ask about your legal rights, how to file complaints, or what evidence to preserve.
            </p>
          </div>
          <div className="quick-actions">
            {QUICK_STARTS.map((q, i) => (
              <button
                key={i}
                className="quick-action-btn"
                onClick={() => onQuickAction(q.replace(/^[^\s]+ /, ''))}
                id={`quick-action-${i}`}
              >
                {q}
              </button>
            ))}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            ⚠️ For informational purposes only. Not legal advice.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="messages-container" id="messages-container">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {isLoading && (
        <div className="message-row">
          <div className="message-avatar assistant">⚖️</div>
          <div className="message-content">
            <div className="typing-indicator">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}
