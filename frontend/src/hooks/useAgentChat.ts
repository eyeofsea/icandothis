'use client';

import { useState, useCallback } from 'react';
import { ChatMessage, AgentStatus } from '@/lib/types';
import { sendChatMessage } from '@/lib/api';
import { useFeedStore } from '@/stores/feedStore';

export function useAgentChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'sys-1',
      role: 'system',
      content: 'SCM Risk Intelligence Agent online. I can analyze disruptions, find alternative suppliers, assess route risks, and provide impact analysis. How can I help?',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({
    name: 'SCM Intelligence Agent',
    status: 'idle',
  });
  const [isLoading, setIsLoading] = useState(false);
  const updateAgentStatus = useFeedStore((s) => s.updateAgentStatus);

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setAgentStatus({ name: 'SCM Intelligence Agent', status: 'thinking', currentTask: 'Analyzing query...' });

    // Update feed store agent statuses
    updateAgentStatus('ImpactAgent', 'analyzing', 'Processing query...');

    try {
      const response = await sendChatMessage(content);

      const reply = typeof response === 'object' && response !== null
        ? (response as { reply?: string }).reply || JSON.stringify(response)
        : String(response);

      // Determine which agents were used based on query content
      const lc = content.toLowerCase();
      if (lc.includes('impact') || lc.includes('risk') || lc.includes('disrupt')) {
        updateAgentStatus('ImpactAgent', 'completed', 'Impact analysis', 'Analysis complete');
      } else {
        updateAgentStatus('ImpactAgent', 'idle');
      }
      if (lc.includes('supplier') || lc.includes('alternative') || lc.includes('vendor')) {
        updateAgentStatus('SupplierAgent', 'completed', 'Supplier search', 'Alternatives found');
      }
      if (lc.includes('route') || lc.includes('ship') || lc.includes('reroute')) {
        updateAgentStatus('RouteAgent', 'completed', 'Route optimization', 'Routes evaluated');
      }
      if (lc.includes('cost') || lc.includes('price') || lc.includes('tco')) {
        updateAgentStatus('CostAgent', 'completed', 'Cost analysis', 'TCO calculated');
      }

      const aiMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: reply,
        timestamp: new Date().toISOString(),
        agentName: 'SCM Intelligence Agent',
      };

      setMessages((prev) => [...prev, aiMsg]);
      setAgentStatus({ name: 'SCM Intelligence Agent', status: 'idle' });
    } catch {
      const fallbackMsg: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please try again or check the backend connection.',
        timestamp: new Date().toISOString(),
        agentName: 'SCM Intelligence Agent',
      };
      setMessages((prev) => [...prev, fallbackMsg]);
      setAgentStatus({ name: 'SCM Intelligence Agent', status: 'idle' });
      updateAgentStatus('ImpactAgent', 'error', 'Connection failed');
    } finally {
      setIsLoading(false);
    }
  }, [updateAgentStatus]);

  return { messages, sendMessage, agentStatus, isLoading };
}
