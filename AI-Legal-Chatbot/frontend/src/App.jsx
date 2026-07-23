import { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';
import Sidebar from './components/Sidebar';
import ChatHeader from './components/ChatHeader';
import MessageList from './components/MessageList';
import MessageInput from './components/MessageInput';
import SourcesPanel from './components/SourcesPanel';
import { sendMessage, checkHealth, clearSession } from './api';

function App() {
  const [sessionId] = useState(() => uuidv4());
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sources, setSources] = useState([]);
  const [currentIntent, setCurrentIntent] = useState(null);
  const [currentIntentLabel, setCurrentIntentLabel] = useState('');
  const [health, setHealth] = useState(null);
  const [ollamaAvailable, setOllamaAvailable] = useState(true);

  // Poll health on mount and every 30 seconds
  useEffect(() => {
    const pollHealth = async () => {
      const h = await checkHealth();
      setHealth(h);
      if (h) setOllamaAvailable(h.ollama_available);
    };
    pollHealth();
    const interval = setInterval(pollHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async (text) => {
    if (!text.trim() || isLoading) return;

    const userMsg = {
      id: uuidv4(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    try {
      const result = await sendMessage(sessionId, text);
      const assistantMsg = {
        id: uuidv4(),
        role: 'assistant',
        content: result.answer,
        timestamp: new Date().toISOString(),
        isFollowup: result.is_followup,
        intent: result.intent,
        intentLabel: result.intent_label,
      };
      setMessages(prev => [...prev, assistantMsg]);
      setSources(result.sources || []);
      setCurrentIntent(result.intent);
      setCurrentIntentLabel(result.intent_label);
      setOllamaAvailable(result.ollama_available);
    } catch (err) {
      const errorMsg = {
        id: uuidv4(),
        role: 'assistant',
        content: `⚠️ **Connection Error**\n\nCould not reach the Dharma backend. Please make sure the API server is running:\n\`\`\`\ncd AI-Legal-Chatbot\npython -m uvicorn src.api.main:app --reload\n\`\`\`\n\nError: ${err.message}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = async () => {
    await clearSession(sessionId).catch(() => {});
    setMessages([]);
    setSources([]);
    setCurrentIntent(null);
    setCurrentIntentLabel('');
  };

  const handleQuickAction = (text) => {
    handleSendMessage(text);
  };

  return (
    <div className="app-shell">
      <Sidebar
        onNewChat={handleNewChat}
        ollamaAvailable={ollamaAvailable}
        health={health}
        onQuickAction={handleQuickAction}
      />
      <div className="chat-main">
        <ChatHeader
          intent={currentIntent}
          intentLabel={currentIntentLabel}
          onNewChat={handleNewChat}
        />
        <MessageList
          messages={messages}
          isLoading={isLoading}
          onQuickAction={handleQuickAction}
        />
        <MessageInput
          onSend={handleSendMessage}
          disabled={isLoading}
        />
      </div>
      <SourcesPanel sources={sources} />
    </div>
  );
}

export default App;
