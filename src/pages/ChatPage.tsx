import React, { useState, useEffect, useRef } from 'react';
import { Send, Trash2, Download, User, Sparkles, Terminal } from 'lucide-react';
import { ChatMessage } from '../types/assistant';
import { api } from '../services/api';

interface ChatPageProps {
  onExecuteCommand: (text: string) => Promise<void>;
}

export const ChatPage: React.FC<ChatPageProps> = ({ onExecuteCommand }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    loadHistory();
    const interval = setInterval(loadHistory, 3000);
    return () => clearInterval(interval);
  }, []);

  async function loadHistory() {
    try {
      const data = await api.getChatHistory();
      setMessages(data);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || sending) return;
    setSending(true);
    try {
      await onExecuteCommand(input.trim());
      setInput('');
      await loadHistory();
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setSending(false); }
  };

  const handleClear = async () => {
    try { await api.clearChatHistory(); setMessages([]); }
    catch (e) { setError(e instanceof Error ? e.message : String(e)); }
  };

  const handleExport = () => {
    const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(messages, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute('href', dataStr);
    downloadAnchor.setAttribute('download', `oska_chat_history_${Date.now()}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-obsidian p-6 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-cyan/15 mb-4">
        <div>
          <h2 className="text-lg font-bold text-white tracking-wide flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-cyan" />
            <span>AI CONVERSATION & MEMORY</span>
          </h2>
          <p className="text-xs text-muted">
            Local chat logs stored securely on this computer.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExport}
            className="px-3 py-1.5 rounded-xl border border-cyan/20 text-xs text-muted hover:text-white hover:bg-white/5 transition-all flex items-center space-x-1.5"
            title="Export conversation history"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export</span>
          </button>
          <button
            onClick={handleClear}
            className="px-3 py-1.5 rounded-xl border border-red-500/30 text-xs text-red-400 hover:bg-red-500/10 transition-all flex items-center space-x-1.5"
            title="Clear chat history"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear</span>
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-muted text-center space-y-2">
            <Sparkles className="w-8 h-8 text-cyan/30 animate-pulse" />
            <p className="text-sm">No conversation history yet.</p>
            <p className="text-xs text-muted/70">
              Speak with "Hey Oska" or type your command below.
            </p>
          </div>
        ) : (
          messages.map((m) => {
            const isUser = m.role === 'user';
            return (
              <div
                key={m.id}
                className={`flex space-x-3 ${isUser ? 'justify-end' : 'justify-start'}`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-cyan/10 border border-cyan/30 flex items-center justify-center text-cyan shrink-0 mt-1">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={`max-w-[70%] rounded-2xl p-4 text-sm leading-relaxed ${
                    isUser
                      ? 'bg-cyan/15 text-white border border-cyan/30 shadow-cyan-glow'
                      : 'bg-navy/70 text-white/90 border border-cyan/15'
                  }`}
                >
                  <div>{m.content}</div>
                  {m.command_intent && m.command_intent !== 'conversation' && (
                    <div className="mt-2 text-[10px] font-mono text-cyan/70 flex items-center space-x-1">
                      <Terminal className="w-3 h-3" />
                      <span>Action: {m.command_intent}</span>
                    </div>
                  )}
                  <div className="mt-1 text-[9px] font-mono text-muted/70 text-right">
                    {new Date(m.created_at * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-white/10 border border-white/20 flex items-center justify-center text-white shrink-0 mt-1">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && <p role="alert" className="text-red-400 text-xs">{error}</p>}
      {/* Input */}
      <form onSubmit={handleSend} className="mt-4 flex space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message OSKA..."
          className="flex-1 frosted-glass border border-cyan/20 rounded-xl px-4 py-3 text-sm text-white placeholder-muted focus:outline-none focus:border-cyan/50"
        />
        <button
          type="submit"
          disabled={!input.trim() || sending}
          className="px-5 rounded-xl bg-cyan hover:bg-cyan/80 text-obsidian font-bold flex items-center justify-center transition-all disabled:opacity-40"
        >
          <Send className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
