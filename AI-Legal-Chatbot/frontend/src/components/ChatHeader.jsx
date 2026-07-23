const INTENT_COLORS = {
  theft: 'var(--intent-theft)',
  cybercrime: 'var(--intent-cybercrime)',
  domestic_violence: 'var(--intent-domestic)',
  traffic_accident: 'var(--intent-traffic)',
  consumer_dispute: 'var(--intent-consumer)',
  missing_person: 'var(--intent-missing)',
  rti: 'var(--intent-rti)',
  general_complaint: 'var(--intent-general)',
  general: 'var(--intent-general)',
};

export default function ChatHeader({ intent, intentLabel, onNewChat }) {
  const color = INTENT_COLORS[intent] || 'var(--intent-general)';

  return (
    <header className="chat-header">
      <div className="chat-header-title">
        <h2>Legal Guidance Chat</h2>
        {intent && intent !== 'general' && (
          <span
            className="intent-pill"
            style={{
              background: `${color}22`,
              color,
              border: `1px solid ${color}55`,
            }}
          >
            {intentLabel || intent}
          </span>
        )}
      </div>
      <div className="chat-header-actions">
        <button
          className="icon-btn"
          onClick={onNewChat}
          title="New conversation"
          id="header-new-chat-btn"
        >
          ✦
        </button>
      </div>
    </header>
  );
}
