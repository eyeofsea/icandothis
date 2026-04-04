'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Sparkles, MessageSquare, Minimize2, Maximize2, X } from 'lucide-react';
import { useAgentChat } from '@/hooks/useAgentChat';
import Message from './Message';
import QuickActions from './QuickActions';
import { cn } from '@/lib/utils';

export default function ChatPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const { messages, sendMessage, isLoading } = useAgentChat();
  const [inputValue, setInputValue] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = () => {
    if (inputValue.trim()) {
      sendMessage(inputValue);
      setInputValue('');
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 w-14 h-14 rounded-full bg-sky-500 text-white shadow-glow-blue flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-[150] group"
      >
        <MessageSquare className="w-6 h-6 group-hover:rotate-12 transition-transform" />
        <div className="absolute -top-1 -right-1 w-5 h-5 bg-rose-500 rounded-full border-2 border-slate-950 flex items-center justify-center text-[10px] font-black">
          1
        </div>
      </button>
    );
  }

  return (
    <div
      className={cn(
        'fixed bottom-6 right-6 z-[150] flex flex-col transition-all duration-300 ease-in-out origin-bottom-right',
        isMinimized ? 'w-64 h-12' : 'w-[420px] h-[600px] max-h-[85vh]',
        'glass-card-pro shadow-2xl rounded-2xl overflow-hidden flex flex-col'
      )}
    >
      {/* Header */}
      <div className="h-12 flex-shrink-0 flex items-center justify-between px-4 border-b border-white/5 bg-slate-900/60 backdrop-blur-md">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md bg-sky-500/20 border border-sky-400/30 flex items-center justify-center">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <span className="text-xs font-bold text-white tracking-widest uppercase">Nexus AI Agent</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1.5 rounded-md hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-colors"
          >
            {isMinimized ? <Maximize2 className="w-3.5 h-3.5" /> : <Minimize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="p-1.5 rounded-md hover:bg-white/5 text-slate-500 hover:text-slate-300 transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Chat content */}
          <div 
            ref={scrollRef}
            className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth scrollbar-thin"
          >
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-6 space-y-4">
                <div className="w-16 h-16 rounded-3xl bg-slate-900/50 border border-slate-800 flex items-center justify-center shadow-inner">
                  <Sparkles className="w-8 h-8 text-sky-500/30" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">How can I assist you?</h3>
                  <p className="text-[11px] text-slate-500 mt-1 max-w-[200px]">Analyze risks, simulate scenarios, or get mitigation reports instantly.</p>
                </div>
                <QuickActions onAction={sendMessage} />
              </div>
            )}
            
            {messages.map((msg, i) => (
              <Message key={i} message={msg} />
            ))}
            
            {isLoading && (
              <div className="flex items-start gap-3 animate-pulse">
                <div className="w-8 h-8 rounded-lg bg-sky-500/10 flex-shrink-0 border border-sky-400/20" />
                <div className="bg-slate-900/50 rounded-2xl rounded-tl-none px-4 py-3 border border-slate-800 max-w-[80%]">
                  <div className="flex gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-sky-500/40 animate-bounce" />
                    <div className="w-1.5 h-1.5 rounded-full bg-sky-500/40 animate-bounce [animation-delay:0.2s]" />
                    <div className="w-1.5 h-1.5 rounded-full bg-sky-500/40 animate-bounce [animation-delay:0.4s]" />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Input area */}
          <div className="p-4 bg-slate-950/40 border-t border-white/5">
            <div className="relative group">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="Ask Nexus agent..."
                className="w-full h-11 bg-slate-900/80 border border-slate-800 rounded-xl px-4 py-3 pr-12 text-xs text-slate-200 placeholder:text-slate-600 outline-none focus:border-sky-500/50 focus:ring-4 focus:ring-sky-500/5 transition-all resize-none overflow-hidden"
              />
              <button
                onClick={handleSend}
                disabled={!inputValue.trim() || isLoading}
                className={cn(
                  "absolute right-2 top-2 h-7 w-7 rounded-lg flex items-center justify-center transition-all",
                  inputValue.trim() 
                    ? "bg-sky-500 text-white shadow-glow-blue hover:bg-sky-400" 
                    : "bg-slate-800 text-slate-500"
                )}
              >
                <Send className="w-3.5 h-3.5" />
              </button>
            </div>
            <div className="mt-2 flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">System Ready</span>
              </div>
              <span className="text-[9px] text-slate-600">Shift + Enter for new line</span>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
