import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number): string {
  if (value >= 1e9) return `$${(value / 1e9).toFixed(1)}B`;
  if (value >= 1e6) return `$${(value / 1e6).toFixed(1)}M`;
  if (value >= 1e3) return `$${(value / 1e3).toFixed(0)}K`;
  return `$${value.toFixed(0)}`;
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat().format(value);
}

export function riskColor(score: number): string {
  if (score >= 80) return "text-red-400";
  if (score >= 60) return "text-orange-400";
  if (score >= 40) return "text-yellow-400";
  return "text-green-400";
}

export function riskBgColor(score: number): string {
  if (score >= 80) return "bg-red-500/20 border-red-500/40";
  if (score >= 60) return "bg-orange-500/20 border-orange-500/40";
  if (score >= 40) return "bg-yellow-500/20 border-yellow-500/40";
  return "bg-green-500/20 border-green-500/40";
}
