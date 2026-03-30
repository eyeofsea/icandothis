'use client';

import { useState, useRef, useEffect } from 'react';
import { MessageSquare, X, Send, Bot } from 'lucide-react';
import { useAgentChat } from '@/hooks/useAgentChat';
import Message from './Message';
import QuickActions from './QuickActions';

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const { messages, sendMessage, agentStatus, isLoading } = useAgentChat();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (!input.trim() || isLoading) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleQuickAction = (text: string) => {
    sendMessage(text);
  };

  return (
    <>
      {/* Toggle button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-5 right-5 z-[2000] w-12 h-12 rounded-full bg-blue-600 hover:bg-blue-500 shadow-lg shadow-blue-500/20 flex items-center justify-center transition-all hover:scale-105"
        >
          <MessageSquare className="w-5 h-5 text-white" />
        </button>
      )}

      {/* Chat panel */}
      {isOpen && (
        <div className="fixed bottom-5 right-5 z-[2000] w-[380px] h-[520px] glass-card flex flex-col shadow-2xl shadow-black/40">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-[#1e3a5f]">
            <div className="flex items-center gap-2">
              <Bot className="w-4 h-4 text-blue-400" />
              <div>
                <span className="text-sm font-semibold text-white">SCM Intelligence Agent</span>
                <div className="flex items-center gap-1.5">
                  <div
                    className={`w-1.5 h-1.5 rounded-full ${
                      agentStatus.status === 'idle'
                        ? 'bg-green-400'
                        : agentStatus.status === 'thinking'
                        ? 'bg-yellow-400 animate-pulse'
                        : 'bg-blue-400 animate-pulse'
                    }`}
                  />
                  <span className="text-[9px] text-slate-500">
                    {agentStatus.status === 'idle' ? 'Ready' : agentStatus.currentTask || agentStatus.status}
                  </span>
                </div>
              </div>
            </div>
            <button onClick={() => setIsOpen(false)} className="p-1 hover:bg-white/10 rounded">
              <X className="w-4 h-4 text-slate-400" />
            </button>
          </div>

          {/* Messages */}
          <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
            {messages.map((msg) => (
              <Message key={msg.id} message={msg} />
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-slate-500 text-xs">
                <Bot className="w-3.5 h-3.5 text-blue-400" />
                <div className="flex gap-1">
                  <span className="loading-dot w-1.5 h-1.5 bg-blue-400 rounded-full" />
                  <span className="loading-dot w-1.5 h-1.5 bg-blue-400 rounded-full" />
                  <span className="loading-dot w-1.5 h-1.5 bg-blue-400 rounded-full" />
                </div>
              </div>
            )}
          </div>

          {/* Quick actions */}
          <QuickActions onAction={handleQuickAction} />

          {/* Input */}
          <div className="px-4 py-3 border-t border-[#1e3a5f]">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Ask about risks, routes, suppliers..."
                className="flex-1 bg-[#0a0e1a] border border-[#1e3a5f] rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 outline-none focus:border-blue-500/50 transition-colors"
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 rounded-lg transition-colors"
              >
                <Send className="w-3.5 h-3.5 text-white" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
