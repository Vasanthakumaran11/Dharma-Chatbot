// Simple markdown-to-HTML renderer for bold, italic, code, and headings
function renderMarkdown(text) {
  if (!text) return '';

  return text
    // Escape HTML entities first
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Code blocks (``` ... ```)
    .replace(/```[\w]*\n?([\s\S]*?)```/gm, '<pre><code>$1</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h4 style="color:var(--color-primary-light);margin:10px 0 4px;">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="color:var(--color-primary-light);margin:12px 0 6px;">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 style="color:var(--color-primary-light);margin:14px 0 8px;">$1</h2>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid var(--color-border);margin:12px 0;">')
    // Numbered lists
    .replace(/^(\d+)\. (.+)$/gm, '<div style="display:flex;gap:8px;margin:3px 0;"><span style="color:var(--color-accent);font-weight:600;min-width:20px;">$1.</span><span>$2</span></div>')
    // Bullet lists
    .replace(/^[•\-\*] (.+)$/gm, '<div style="display:flex;gap:8px;margin:3px 0;"><span style="color:var(--color-primary);font-weight:600;min-width:14px;">•</span><span>$1</span></div>')
    // Line breaks
    .replace(/\n/g, '<br />');
}

function formatTime(iso) {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch {
    return '';
  }
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;
  const isFollowup = message.isFollowup;

  const bubbleClass = [
    'message-bubble',
    isUser ? 'user' : 'assistant',
    isFollowup ? 'followup' : '',
  ].filter(Boolean).join(' ');

  return (
    <div className={`message-row ${isUser ? 'user' : ''}`} id={`msg-${message.id}`}>
      <div className={`message-avatar ${isUser ? 'user' : 'assistant'}`}>
        {isUser ? '👤' : '⚖️'}
      </div>
      <div className="message-content">
        {isUser ? (
          <div className={bubbleClass}>
            {message.content}
          </div>
        ) : (
          <div
            className={bubbleClass}
            style={isError ? { borderColor: 'rgba(239,68,68,0.3)', background: 'rgba(239,68,68,0.05)' } : {}}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(message.content) }}
          />
        )}
        <div className={`message-timestamp ${isUser ? 'right' : ''}`} style={isUser ? { textAlign: 'right' } : {}}>
          {formatTime(message.timestamp)}
        </div>
      </div>
    </div>
  );
}
