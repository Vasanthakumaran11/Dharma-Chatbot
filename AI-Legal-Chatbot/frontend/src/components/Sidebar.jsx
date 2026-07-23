const INCIDENTS = [
  { key: 'theft', label: 'Theft / Robbery', color: 'var(--intent-theft)', icon: '🔓' },
  { key: 'cybercrime', label: 'Cybercrime / Fraud', color: 'var(--intent-cybercrime)', icon: '💻' },
  { key: 'domestic_violence', label: 'Domestic Violence', color: 'var(--intent-domestic)', icon: '🏠' },
  { key: 'traffic_accident', label: 'Traffic Accident', color: 'var(--intent-traffic)', icon: '🚗' },
  { key: 'consumer_dispute', label: 'Consumer Dispute', color: 'var(--intent-consumer)', icon: '🛍️' },
  { key: 'missing_person', label: 'Missing Person', color: 'var(--intent-missing)', icon: '👤' },
  { key: 'rti', label: 'RTI / Government', color: 'var(--intent-rti)', icon: '📋' },
];

const QUICK_STARTERS = {
  theft: 'My mobile phone was stolen yesterday. How do I file a police complaint?',
  cybercrime: 'I lost money in a UPI fraud. What legal steps can I take?',
  domestic_violence: 'I am facing domestic violence. What are my rights and how to file a complaint?',
  traffic_accident: 'I was in a road accident and the other driver fled. What should I do?',
  consumer_dispute: 'I bought a defective product and the seller is refusing a refund. What can I do?',
  missing_person: 'My child has been missing since yesterday. How do I report this?',
  rti: 'How do I file an RTI application to get information from a government office?',
};

export default function Sidebar({ onNewChat, ollamaAvailable, health, onQuickAction }) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">⚖️</div>
        <div className="sidebar-logo-text">
          <h1>Dharma</h1>
          <p>Legal Guidance AI</p>
        </div>
      </div>

      {/* New Chat */}
      <button className="new-chat-btn" onClick={onNewChat} id="new-chat-btn">
        <span>✦</span> New Conversation
      </button>

      {/* Incident Categories */}
      <div className="sidebar-section-title">Complaint Categories</div>
      <div className="incident-categories">
        {INCIDENTS.map((inc) => (
          <div
            key={inc.key}
            className="incident-badge"
            onClick={() => onQuickAction(QUICK_STARTERS[inc.key])}
            title={`Start a ${inc.label} query`}
            id={`incident-${inc.key}`}
          >
            <span className="incident-dot" style={{ background: inc.color }} />
            <span>{inc.icon}</span>
            <span>{inc.label}</span>
          </div>
        ))}
      </div>

      <div className="sidebar-divider" />

      {/* Ollama Status */}
      <div className="ollama-status">
        <div className={`status-dot ${ollamaAvailable ? 'online' : 'offline'}`} />
        <div>
          <div style={{ fontWeight: 600, color: 'var(--color-text-primary)', fontSize: '0.78rem' }}>
            {ollamaAvailable ? 'AI Engine Online' : 'AI Engine Offline'}
          </div>
          <div style={{ color: 'var(--color-text-muted)', fontSize: '0.68rem' }}>
            {ollamaAvailable ? 'Ollama connected' : 'Run: ollama serve'}
          </div>
        </div>
      </div>

      {health && (
        <div style={{ fontSize: '0.68rem', color: 'var(--color-text-muted)', textAlign: 'center', marginTop: 4 }}>
          {health.total_vectors.toLocaleString()} legal vectors indexed
        </div>
      )}
    </aside>
  );
}
