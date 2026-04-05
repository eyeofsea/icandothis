"use client";

import { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from "recharts";
import { useDisruptionStore } from "@/stores/disruptionStore";
import type { HedgingReport, HedgingScenario, TCOBreakdown } from "@/lib/types";
import { fetchHedgingReport } from "@/lib/api";

function formatCurrency(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  if (abs >= 1_000_000) return `${sign}$${(abs / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `${sign}$${(abs / 1_000).toFixed(0)}K`;
  return `${sign}$${abs.toFixed(0)}`;
}

function SeverityBadge({ severity }: { severity: number }) {
  const colors = ["", "bg-blue-500", "bg-yellow-500", "bg-orange-500", "bg-red-500", "bg-red-700"];
  return (
    <span className={`${colors[severity]} text-white text-xs px-2 py-0.5 rounded`}>
      Severity {severity}/5
    </span>
  );
}

function BaselineTCOCard({ tco }: { tco: TCOBreakdown }) {
  const pieData = [
    { name: "Shipping", value: tco.shipping_cost, fill: "#3b82f6" },
    { name: "Insurance", value: tco.insurance_cost, fill: "#06b6d4" },
    { name: "Delay Penalties", value: tco.delay_penalties, fill: "#ef4444" },
    { name: "Site Overhead", value: tco.site_overhead, fill: "#f59e0b" },
    { name: "Workforce", value: tco.idle_workforce, fill: "#8b5cf6" },
    { name: "Storage", value: tco.storage_cost, fill: "#64748b" },
  ].filter((d) => d.value > 0);

  return (
    <div className="bg-[#111827]/80 border border-white/10 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-1">Baseline TCO (No Action)</h3>
      <p className="text-3xl font-bold text-red-400 mb-4">{formatCurrency(tco.total)}</p>
      <p className="text-xs text-gray-500 mb-3">{tco.delay_days} days delay</p>
      <ResponsiveContainer width="100%" height={200}>
        <PieChart>
          <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%"
            innerRadius={50} outerRadius={80} paddingAngle={2}>
            {pieData.map((entry, i) => (
              <Cell key={i} fill={entry.fill} />
            ))}
          </Pie>
          <Tooltip formatter={(v) => formatCurrency(Number(v))} />
          <Legend iconSize={8} wrapperStyle={{ fontSize: 11 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

function ScenarioComparisonChart({ scenarios, baselineTotal }: {
  scenarios: HedgingScenario[];
  baselineTotal: number;
}) {
  const data = scenarios.map((s) => ({
    name: s.name.length > 25 ? s.name.slice(0, 22) + "..." : s.name,
    "Total TCO": s.total,
    "Net Savings": Math.max(0, s.net_savings),
    rank: s.rank,
  }));

  return (
    <div className="bg-[#111827]/80 border border-white/10 rounded-xl p-5">
      <h3 className="text-sm font-medium text-gray-400 mb-4">TCO Comparison by Scenario</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ left: 120 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis type="number" tickFormatter={formatCurrency} stroke="#6b7280" />
          <YAxis type="category" dataKey="name" stroke="#6b7280" width={120} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v) => formatCurrency(Number(v))} />
          <Legend />
          <Bar dataKey="Total TCO" fill="#ef4444" radius={[0, 4, 4, 0]} />
          <Bar dataKey="Net Savings" fill="#22c55e" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
        <span className="inline-block w-3 h-3 bg-red-400/30 border border-red-400 rounded" />
        <span>Baseline: {formatCurrency(baselineTotal)}</span>
      </div>
    </div>
  );
}

function ScenarioTable({ scenarios }: { scenarios: HedgingScenario[] }) {
  return (
    <div className="bg-[#111827]/80 border border-white/10 rounded-xl p-5 overflow-x-auto">
      <h3 className="text-sm font-medium text-gray-400 mb-4">Decision Matrix</h3>
      <table className="w-full text-sm">
        <thead>
          <tr className="text-gray-500 border-b border-white/10">
            <th className="text-left py-2 px-2">#</th>
            <th className="text-left py-2 px-2">Scenario</th>
            <th className="text-right py-2 px-2">Total TCO</th>
            <th className="text-right py-2 px-2">Net Savings</th>
            <th className="text-right py-2 px-2">Savings %</th>
            <th className="text-right py-2 px-2">BCR</th>
            <th className="text-right py-2 px-2">Impl. Cost</th>
            <th className="text-right py-2 px-2">Residual Delay</th>
          </tr>
        </thead>
        <tbody>
          {scenarios.map((s) => (
            <tr key={s.rank} className={`border-b border-white/5 ${s.rank === 1 ? "bg-green-500/10" : ""}`}>
              <td className="py-2 px-2 text-gray-400">{s.rank}</td>
              <td className="py-2 px-2 text-white font-medium">
                {s.name}
                {s.rank === 1 && (
                  <span className="ml-2 text-xs bg-green-500/20 text-green-400 px-1.5 py-0.5 rounded">
                    Recommended
                  </span>
                )}
              </td>
              <td className="py-2 px-2 text-right text-white">{formatCurrency(s.total)}</td>
              <td className={`py-2 px-2 text-right ${s.net_savings > 0 ? "text-green-400" : "text-red-400"}`}>
                {s.net_savings > 0 ? "+" : ""}{formatCurrency(s.net_savings)}
              </td>
              <td className="py-2 px-2 text-right text-gray-300">{s.savings_pct.toFixed(1)}%</td>
              <td className="py-2 px-2 text-right text-gray-300">{s.benefit_cost_ratio}x</td>
              <td className="py-2 px-2 text-right text-yellow-400">{formatCurrency(s.implementation_cost)}</td>
              <td className="py-2 px-2 text-right text-gray-300">{s.residual_delay_days}d</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function HedgingReportView() {
  const { activeDisruptions } = useDisruptionStore();
  const [report, setReport] = useState<HedgingReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedDisruption, setSelectedDisruption] = useState<string>("");
  const [delayDays, setDelayDays] = useState(30);

  useEffect(() => {
    if (activeDisruptions.length > 0 && !selectedDisruption) {
      setSelectedDisruption(activeDisruptions[0].id);
    }
  }, [activeDisruptions, selectedDisruption]);

  const handleGenerate = async () => {
    if (!selectedDisruption) return;
    setLoading(true);
    try {
      const data = await fetchHedgingReport(selectedDisruption, delayDays);
      setReport(data);
    } catch (err) {
      console.error("Failed to generate hedging report:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 p-6 overflow-y-auto h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Hedging & TCO Report</h2>
          <p className="text-sm text-gray-400 mt-1">
            Compare alternative routes and suppliers with full TCO breakdown
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-end gap-4 bg-[#111827]/80 border border-white/10 rounded-xl p-4">
        <div className="flex-1">
          <label className="text-xs text-gray-400 block mb-1">Disruption Event</label>
          <select
            value={selectedDisruption}
            onChange={(e) => setSelectedDisruption(e.target.value)}
            className="w-full bg-[#0a0e1a] border border-white/20 rounded px-3 py-2 text-sm text-white"
          >
            <option value="">Select disruption...</option>
            {activeDisruptions.map((d) => (
              <option key={d.id} value={d.id}>{d.name} (Sev. {d.severity})</option>
            ))}
          </select>
        </div>
        <div className="w-32">
          <label className="text-xs text-gray-400 block mb-1">Delay (days)</label>
          <input
            type="number"
            value={delayDays}
            onChange={(e) => setDelayDays(parseInt(e.target.value) || 30)}
            min={1}
            max={365}
            className="w-full bg-[#0a0e1a] border border-white/20 rounded px-3 py-2 text-sm text-white"
          />
        </div>
        <button
          onClick={handleGenerate}
          disabled={loading || !selectedDisruption}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white px-6 py-2 rounded text-sm font-medium"
        >
          {loading ? "Generating..." : "Generate Report"}
        </button>
      </div>

      {/* Report Content */}
      {report && (
        <>
          {/* Executive Summary */}
          <div className="bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/20 rounded-xl p-5">
            <div className="flex items-center gap-3 mb-3">
              <h3 className="text-sm font-medium text-white">Executive Summary</h3>
              <SeverityBadge severity={report.severity} />
            </div>
            <pre className="text-sm text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
              {report.executive_summary}
            </pre>
            <div className="flex gap-4 mt-3 text-xs text-gray-500">
              <span>{report.affected_equipment_count} equipment affected</span>
              <span>{report.affected_project_count} projects at risk</span>
            </div>
          </div>

          {/* TCO Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <BaselineTCOCard tco={report.baseline_tco} />
            <div className="lg:col-span-2">
              <ScenarioComparisonChart
                scenarios={report.scenarios}
                baselineTotal={report.baseline_tco.total}
              />
            </div>
          </div>

          {/* Decision Matrix */}
          <ScenarioTable scenarios={report.scenarios} />
        </>
      )}

      {/* Empty state */}
      {!report && !loading && (
        <div className="text-center py-20 text-gray-500">
          <p className="text-lg mb-2">No report generated yet</p>
          <p className="text-sm">Select a disruption event and click Generate Report</p>
        </div>
      )}
    </div>
  );
}
