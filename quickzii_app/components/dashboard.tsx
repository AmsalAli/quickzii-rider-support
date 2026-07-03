"use client"

import { useState } from "react"
import type { DashboardState } from "@/lib/mock-data"
import { StatPill } from "@/components/badges"
import { ToastProvider } from "@/components/toast"
import { MediumRiskQueue } from "@/components/medium-risk-queue"
import { HighRiskQueue } from "@/components/high-risk-queue"
import { AuditLog } from "@/components/audit-log"
import { cn } from "@/lib/utils"

type Tab = "medium" | "high" | "audit"

const TABS: { id: Tab; label: string }[] = [
  { id: "medium", label: "Medium Risk Queue" },
  { id: "high", label: "High Risk Queue" },
  { id: "audit", label: "Audit Log" },
]

export function Dashboard({ state }: { state: DashboardState }) {
  const [tab, setTab] = useState<Tab>("medium")

  return (
    <ToastProvider>
      <main className="mx-auto max-w-[1280px] px-6 py-8">
        {/* Page header */}
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <h1 className="text-2xl font-semibold text-foreground text-balance">
              AI Support — Human Review
            </h1>
            <p className="text-sm text-muted-foreground text-pretty">
              Cases escalated by the AI agent for human review or full handling.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatPill tone="warning">{state.stats.pending} Pending</StatPill>
            <StatPill tone="info">{state.stats.inReview} In Review</StatPill>
            <StatPill tone="success">{state.stats.resolvedToday} Resolved today</StatPill>
          </div>
        </div>

        {/* Tab bar */}
        <div className="mt-6 flex gap-6 border-b border-border">
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              aria-current={tab === t.id ? "true" : undefined}
              className={cn(
                "-mb-px border-b-2 pb-3 text-sm transition-colors duration-200",
                tab === t.id
                  ? "border-primary font-medium text-foreground"
                  : "border-transparent text-muted-foreground hover:text-foreground",
              )}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="mt-6">
          {tab === "medium" && <MediumRiskQueue cases={state.mediumRiskQueue} />}
          {tab === "high" && <HighRiskQueue cases={state.highRiskQueue} />}
          {tab === "audit" && <AuditLog entries={state.auditLog} />}
        </div>
      </main>
    </ToastProvider>
  )
}
