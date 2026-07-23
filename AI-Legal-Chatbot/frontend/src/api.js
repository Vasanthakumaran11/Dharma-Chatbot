// Centralized API client for the Dharma Chatbot backend
const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function sendMessage(sessionId, message) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export async function checkHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`, { signal: AbortSignal.timeout(5000) });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function clearSession(sessionId) {
  await fetch(`${API_BASE}/api/session/${sessionId}`, { method: 'DELETE' });
}
