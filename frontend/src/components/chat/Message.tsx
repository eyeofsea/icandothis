'use client';

import { ChatMessage } from '@/lib/types';
import { Bot, User } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface MessageProps {
  message: ChatMessage;
}

function renderMarkdown(content: string) {
  // Simple markdown renderer for chat messages
  const lines = content.split('\n');
  const elements: JSX.Element[] = [];
  let inTable = false;
  let tableRows: string[][] = [];
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let listItems: string[] = [];

  const flushTable = () => {
    if (tableRows.length > 0) {
      elements.push(
        <div key={`table-${elements.length}`} className="overflow-x-auto my-2">
          <table className="w-full text-[10px] border-collapse">
            <thead>
              <tr className="border-b border-[#1e3a5f]">
                {tableRows[0].map((cell, i) => (
                  <th key={i} className="text-left py-1 px-2 text-slate-400 font-medium">{cell.trim()}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableRows.slice(1).map((row, ri) => (
                <tr key={ri} className="border-b border-[#1e3a5f]/30">
                  {row.map((cell, ci) => (
                    <td key={ci} className="py-1 px-2 text-slate-300">{cell.trim()}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
    }
  };

  const flushList = () => {
    if (listItems.length > 0) {
      elements.push(
        <ul key={`list-${elements.length}`} className="list-disc list-inside space-y-0.5 my-1 text-[11px] text-slate-300">
          {listItems.map((item, i) => <li key={i}>{item}</li>)}
        </ul>
      );
      listItems = [];
    }
  };

  lines.forEach((line, idx) => {
    // Code block
    if (line.startsWith('```')) {
      if (inCodeBlock) {
        elements.push(
          <pre key={`code-${elements.length}`} className="bg-[#0a0e1a] rounded p-2 text-[10px] text-green-400 overflow-x-auto my-1.5 font-mono">
            {codeLines.join('\n')}
          </pre>
        );
        codeLines = [];
        inCodeBlock = false;
      } else {
        inCodeBlock = true;
      }
      return;
    }
    if (inCodeBlock) {
      codeLines.push(line);
      return;
    }

    // Table
    if (line.includes('|') && line.trim().startsWith('|')) {
      const cells = line.split('|').filter(Boolean);
      if (cells.some((c) => /^[-:]+$/.test(c.trim()))) return; // separator row
      if (!inTable) inTable = true;
      tableRows.push(cells);
      return;
    } else if (inTable) {
      flushTable();
      inTable = false;
    }

    // List items
    if (line.match(/^[-*]\s/)) {
      flushTable();
      listItems.push(line.replace(/^[-*]\s/, ''));
      return;
    }
    if (line.match(/^\d+\.\s/)) {
      flushTable();
      listItems.push(line.replace(/^\d+\.\s/, ''));
      return;
    }
    flushList();

    // Headers
    if (line.startsWith('## ')) {
      elements.push(<h3 key={idx} className="text-xs font-bold text-white mt-2 mb-1">{line.replace('## ', '')}</h3>);
      return;
    }
    if (line.startsWith('### ')) {
      elements.push(<h4 key={idx} className="text-[11px] font-semibold text-slate-200 mt-1.5 mb-0.5">{line.replace('### ', '')}</h4>);
      return;
    }

    // Bold text
    if (line.trim()) {
      const parts = line.split(/(\*\*[^*]+\*\*)/g);
      elements.push(
        <p key={idx} className="text-[11px] text-slate-300 leading-relaxed">
          {parts.map((part, pi) =>
            part.startsWith('**') && part.endsWith('**') ? (
              <strong key={pi} className="text-white font-semibold">{part.slice(2, -2)}</strong>
            ) : (
              <span key={pi}>{part}</span>
            )
          )}
        </p>
      );
    } else if (line.trim() === '') {
      elements.push(<div key={idx} className="h-1" />);
    }
  });

  flushTable();
  flushList();
  return elements;
}

export default function Message({ message }: MessageProps) {
  if (message.role === 'system') {
    return (
      <div className="flex justify-center">
        <div className="bg-[#1e3a5f]/30 rounded-lg px-3 py-1.5 text-[10px] text-slate-400 text-center max-w-[80%]">
          {message.content}
        </div>
      </div>
    );
  }

  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-2 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center ${isUser ? 'bg-blue-600' : 'bg-slate-700'}`}>
        {isUser ? <User className="w-3 h-3 text-white" /> : <Bot className="w-3 h-3 text-blue-400" />}
      </div>
      <div className={`max-w-[85%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`rounded-lg px-3 py-2 ${
            isUser
              ? 'bg-blue-600/80 text-white'
              : 'bg-[#1a2236] border border-[#1e3a5f]/50'
          }`}
        >
          {isUser ? (
            <p className="text-[11px]">{message.content}</p>
          ) : (
            <div>{renderMarkdown(message.content)}</div>
          )}
        </div>
        <div className="text-[8px] text-slate-600 mt-0.5 px-1">
          {formatDistanceToNow(new Date(message.timestamp), { addSuffix: true })}
          {message.agentName && <span className="ml-1">via {message.agentName}</span>}
        </div>
      </div>
    </div>
  );
}
