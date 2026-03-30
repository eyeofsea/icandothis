'use client';

import { useState, useCallback } from 'react';
import { ChatMessage, AgentStatus } from '@/lib/types';

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

    // Simulate AI response since backend may not be running
    await new Promise((r) => setTimeout(r, 1500));
    setAgentStatus({ name: 'SCM Intelligence Agent', status: 'analyzing', currentTask: 'Processing data...' });
    await new Promise((r) => setTimeout(r, 1000));

    const responses: Record<string, string> = {
      risk: '## Current Risk Assessment\n\n| Category | Count | Risk Level |\n|----------|-------|------------|\n| Critical Equipment | 6 | High |\n| Active Routes | 8 | Medium |\n| Monitored Zones | 5 | High |\n\n**Key Findings:**\n- Strait of Hormuz carries 4 equipment items valued at $87.5M\n- Red Sea / Bab el-Mandeb shows elevated threat levels\n- BOG Compressor (eq-9) is delayed with risk score 78\n\nRecommend immediate review of Hormuz-dependent shipments.',
      alternative: '## Alternative Supplier Analysis\n\nFor **Mitsubishi Heavy Industries** (current supplier):\n\n1. **Siemens Energy** (Germany)\n   - Quality: 96% (+1%)\n   - Lead time: 300 days (-65 days)\n   - Cost delta: +8%\n   - Route: Europe-Suez (lower risk)\n\n2. **Doosan Enerbility** (South Korea)\n   - Quality: 91% (-4%)\n   - Lead time: 420 days (+55 days)\n   - Cost delta: -12%\n   - Route: Korea-Gulf (similar risk)\n\nRecommend Siemens for critical items, Doosan for cost optimization.',
      cost: '## Cost Impact Analysis\n\n**Scenario: Strait of Hormuz Disruption**\n\n- Direct impact: **$87.5M** in delayed equipment\n- Rerouting cost: **$4.2M** additional shipping\n- Project delay penalties: **$12.8M** estimated\n- Total exposure: **$104.5M**\n\n**Mitigation Options:**\n1. Cape of Good Hope rerouting: +15 days, +$3.1M\n2. Alternative supplier sourcing: +45 days, -$1.2M net\n3. Air freight critical items: +$8.5M, -20 days\n\nRecommended: Hybrid approach (option 1 + 3 for critical) saves **$68M** vs no action.',
      reroute: '## Route Alternatives\n\n**Current**: Japan - Hormuz (22 days, $45/ton)\n\n### Option A: Cape of Good Hope\n- Transit: 37 days (+15 days)\n- Cost: $62/ton (+38%)\n- Risk score: 15 (vs 45 current)\n- Avoids: Hormuz, Red Sea\n\n### Option B: Trans-Pacific + Panama\n- Transit: 42 days (+20 days)\n- Cost: $78/ton (+73%)\n- Risk score: 12\n- Avoids: All Asian chokepoints\n\n### Option C: Rail (China-Europe) + Short Sea\n- Transit: 28 days (+6 days)\n- Cost: $95/ton (+111%)\n- Risk score: 25\n- Limited to < 50 ton items\n\nRecommend Option A for heavy equipment, Option C for instrumentation.',
      default: 'I can help you with:\n\n- **Risk Analysis**: Current threat assessment across your supply chain\n- **Alternative Suppliers**: Find backup suppliers for critical equipment\n- **Cost Impact**: Financial impact of disruption scenarios\n- **Route Options**: Alternative shipping routes to avoid risk zones\n- **Full Analysis**: Comprehensive disruption cascade analysis\n\nWhat would you like to explore?',
    };

    let responseKey = 'default';
    const lc = content.toLowerCase();
    if (lc.includes('risk') || lc.includes('at risk')) responseKey = 'risk';
    else if (lc.includes('alternative') || lc.includes('supplier')) responseKey = 'alternative';
    else if (lc.includes('cost') || lc.includes('impact') || lc.includes('financial')) responseKey = 'cost';
    else if (lc.includes('reroute') || lc.includes('route') || lc.includes('ship')) responseKey = 'reroute';
    else if (lc.includes('analysis') || lc.includes('full')) responseKey = 'risk';

    const aiMsg: ChatMessage = {
      id: `ai-${Date.now()}`,
      role: 'assistant',
      content: responses[responseKey],
      timestamp: new Date().toISOString(),
      agentName: 'SCM Intelligence Agent',
    };

    setMessages((prev) => [...prev, aiMsg]);
    setIsLoading(false);
    setAgentStatus({ name: 'SCM Intelligence Agent', status: 'idle' });
  }, []);

  return { messages, sendMessage, agentStatus, isLoading };
}
