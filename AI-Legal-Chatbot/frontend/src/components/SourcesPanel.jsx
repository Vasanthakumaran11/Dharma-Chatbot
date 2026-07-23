import { useState } from 'react';

function SourceCard({ source, index }) {
  const [expanded, setExpanded] = useState(false);
  const scorePercent = Math.round(source.score * 100);

  return (
    <div
      className="source-card"
      onClick={() => setExpanded(!expanded)}
      id={`source-card-${index}`}
    >
      <div className="source-law">
        {source.law_short || source.law_name || 'Unknown Law'}
      </div>
      {source.section_number && (
        <div className="source-section">
          § {source.section_number}
          {source.section_title && ` — ${source.section_title}`}
        </div>
      )}

      {expanded && (
        <>
          {source.chapter_title && (
            <div style={{
              fontSize: '0.7rem',
              color: 'var(--color-text-muted)',
              marginTop: 4,
              fontStyle: 'italic'
            }}>
              Chapter: {source.chapter_title}
            </div>
          )}
          {source.legal_domain && (
            <div style={{
              fontSize: '0.7rem',
              color: 'var(--color-info)',
              marginTop: 2,
            }}>
              Domain: {source.legal_domain}
            </div>
          )}
          <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 4 }}>
            Full law: {source.law_name}
          </div>
        </>
      )}

      <div className="source-score-bar">
        <div
          className="source-score-fill"
          style={{ width: `${scorePercent}%` }}
        />
      </div>
      <div style={{
        fontSize: '0.65rem',
        color: 'var(--color-text-muted)',
        marginTop: 3,
        display: 'flex',
        justifyContent: 'space-between',
      }}>
        <span>Relevance</span>
        <span style={{ color: 'var(--color-accent)' }}>{scorePercent}%</span>
      </div>
    </div>
  );
}

export default function SourcesPanel({ sources }) {
  return (
    <aside className="sources-panel">
      <div className="sources-panel-header">
        <h3>📚 Legal Sources</h3>
        {sources.length > 0 && (
          <span className="sources-count-badge">{sources.length}</span>
        )}
      </div>

      {sources.length === 0 ? (
        <div className="sources-empty">
          <div className="sources-empty-icon">📖</div>
          <div>Legal citations will appear here after your first question.</div>
        </div>
      ) : (
        <div className="sources-list" id="sources-list">
          {sources.map((source, i) => (
            <SourceCard key={i} source={source} index={i} />
          ))}
        </div>
      )}
    </aside>
  );
}
