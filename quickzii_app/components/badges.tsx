import type { RiskTier } from "@/lib/mock-data"
import { cn } from "@/lib/utils"

const pillBase =
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"

const riskStyles: Record<RiskTier, { wrap: string; dot: string; label: string }> = {
  LOW: {
    wrap: "bg-[#22c55e]/15 text-[#4ade80] border-[#22c55e]/30",
    dot: "bg-[#4ade80]",
    label: "LOW risk",
  },
  MEDIUM: {
    wrap: "bg-[#f59e0b]/15 text-[#fbbf24] border-[#f59e0b]/30",
    dot: "bg-[#fbbf24]",
    label: "MEDIUM risk",
  },
  HIGH: {
    wrap: "bg-[#ef4444]/15 text-[#f87171] border-[#ef4444]/30",
    dot: "bg-[#f87171]",
    label: "HIGH risk",
  },
}

export function RiskBadge({ tier }: { tier: RiskTier }) {
  const s = riskStyles[tier]
  return (
    <span className={cn(pillBase, s.wrap)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", s.dot)} aria-hidden />
      {s.label}
    </span>
  )
}

type StatTone = "warning" | "info" | "success"

const statStyles: Record<StatTone, { wrap: string; dot: string }> = {
  warning: { wrap: "bg-[#f59e0b]/15 text-[#fbbf24] border-[#f59e0b]/30", dot: "bg-[#fbbf24]" },
  info: { wrap: "bg-[#3b82f6]/15 text-[#60a5fa] border-[#3b82f6]/30", dot: "bg-[#60a5fa]" },
  success: { wrap: "bg-[#22c55e]/15 text-[#4ade80] border-[#22c55e]/30", dot: "bg-[#4ade80]" },
}

export function StatPill({ tone, children }: { tone: StatTone; children: React.ReactNode }) {
  const s = statStyles[tone]
  return (
    <span className={cn(pillBase, s.wrap)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", s.dot)} aria-hidden />
      {children}
    </span>
  )
}

export function IntentBadge({ intent }: { intent: string }) {
  return (
    <span className="inline-flex items-center rounded-md bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary">
      {intent}
    </span>
  )
}
