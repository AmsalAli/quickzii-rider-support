"use client"

import { useMemo, useState } from "react"
import { Calendar, Search, Download, ChevronLeft, ChevronRight } from "lucide-react"
import {
  type AuditEntry,
  type AuditOutcome,
  INTENT_OPTIONS,
  OUTCOME_OPTIONS,
  RISK_OPTIONS,
} from "@/lib/mock-data"
import { RiskBadge } from "@/components/badges"
import { Button } from "@/components/ui/button"

const outcomeColor: Record<AuditOutcome, string> = {
  "Auto-resolved": "text-[#4ade80]",
  "Human approved (as-is)": "text-[#60a5fa]",
  "Human edited reply": "text-[#fbbf24]",
  "Human rejected": "text-[#f87171]",
  "Escalated, human handled": "text-[#f87171]",
}

const selectClass =
  "h-9 rounded-lg border border-input bg-background px-3 text-sm text-foreground outline-none transition-colors duration-200 focus:border-ring focus:ring-1 focus:ring-ring"

export function AuditLog({ entries }: { entries: AuditEntry[] }) {
  const [search, setSearch] = useState("")
  const [risk, setRisk] = useState("All")
  const [intent, setIntent] = useState("All intents")

  const filtered = useMemo(() => {
    return entries.filter((e) => {
      const matchesSearch =
        search.trim() === "" ||
        e.riderName.toLowerCase().includes(search.toLowerCase()) ||
        e.bookingId.toLowerCase().includes(search.toLowerCase())
      const matchesRisk = risk === "All" || e.riskTier === risk.toUpperCase()
      const matchesIntent =
        intent === "All intents" || e.intent.toLowerCase() === intent.toLowerCase()
      return matchesSearch && matchesRisk && matchesIntent
    })
  }, [entries, search, risk, intent])

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">
        Complete record of all AI agent actions and human interventions. This is the source of truth
        for evaluation and compliance.
      </p>

      {/* Filter bar */}
      <div className="sticky top-14 z-30 -mx-1 flex flex-wrap items-center gap-2 rounded-xl border border-border bg-card/80 px-3 py-3 backdrop-blur">
        <button
          type="button"
          className="inline-flex h-9 items-center gap-2 rounded-lg border border-input bg-background px-3 text-sm text-foreground transition-colors duration-200 hover:border-ring"
        >
          <Calendar className="h-4 w-4 text-muted-foreground" />
          Today
        </button>

        <select
          aria-label="Filter by intent"
          value={intent}
          onChange={(e) => setIntent(e.target.value)}
          className={selectClass}
        >
          {INTENT_OPTIONS.map((o) => (
            <option key={o}>{o}</option>
          ))}
        </select>

        <select
          aria-label="Filter by risk tier"
          value={risk}
          onChange={(e) => setRisk(e.target.value)}
          className={selectClass}
        >
          {RISK_OPTIONS.map((o) => (
            <option key={o}>{o === "All" ? "All risk" : o}</option>
          ))}
        </select>

        <select aria-label="Filter by outcome" className={selectClass} defaultValue="All">
          {OUTCOME_OPTIONS.map((o) => (
            <option key={o}>{o === "All" ? "All outcomes" : o}</option>
          ))}
        </select>

        <div className="relative flex-1 min-w-[180px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search rider or booking ID"
            aria-label="Search rider or booking ID"
            className="h-9 w-full rounded-lg border border-input bg-background pl-9 pr-3 text-sm text-foreground outline-none transition-colors duration-200 placeholder:text-tertiary-foreground focus:border-ring focus:ring-1 focus:ring-ring"
          />
        </div>

        <Button variant="outline" className="ml-auto gap-1.5">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-2xl border border-border bg-card">
        <table className="w-full min-w-[820px] text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs uppercase tracking-wide text-muted-foreground">
              <th className="px-4 py-3 font-medium">Timestamp</th>
              <th className="px-4 py-3 font-medium">Booking</th>
              <th className="px-4 py-3 font-medium">Rider</th>
              <th className="px-4 py-3 font-medium">Intent</th>
              <th className="px-4 py-3 font-medium">Risk</th>
              <th className="px-4 py-3 font-medium">Outcome</th>
              <th className="px-4 py-3 font-medium">Processing Time</th>
              <th className="px-4 py-3 font-medium text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((e) => (
              <tr
                key={e.id}
                className="border-b border-border/60 transition-colors duration-200 last:border-0 hover:bg-muted/30"
              >
                <td className="px-4 py-3 text-muted-foreground tabular-nums">{e.timestamp}</td>
                <td className="px-4 py-3">
                  <a href="#" className="text-primary hover:underline">
                    {e.bookingId}
                  </a>
                </td>
                <td className="px-4 py-3 text-foreground">{e.riderName}</td>
                <td className="px-4 py-3 text-muted-foreground">{e.intent}</td>
                <td className="px-4 py-3">
                  <RiskBadge tier={e.riskTier} />
                </td>
                <td className={`px-4 py-3 font-medium ${outcomeColor[e.outcome]}`}>{e.outcome}</td>
                <td className="px-4 py-3 text-muted-foreground tabular-nums">{e.processingTime}</td>
                <td className="px-4 py-3 text-right">
                  <button
                    type="button"
                    className="rounded-md px-2 py-1 text-xs font-medium text-primary transition-colors duration-200 hover:bg-primary/10"
                  >
                    View
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-10 text-center text-muted-foreground">
                  No matching records.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted-foreground">Showing 1–9 of 247</span>
        <div className="flex items-center gap-1">
          <button
            type="button"
            disabled
            aria-label="Previous page"
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors duration-200 hover:bg-accent disabled:opacity-40"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          {["1", "2", "3"].map((p, i) => (
            <button
              key={p}
              type="button"
              className={
                i === 0
                  ? "flex h-8 w-8 items-center justify-center rounded-md bg-primary/10 text-sm font-medium text-foreground"
                  : "flex h-8 w-8 items-center justify-center rounded-md text-sm text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
              }
            >
              {p}
            </button>
          ))}
          <span className="px-1 text-muted-foreground">…</span>
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-md text-sm text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
          >
            28
          </button>
          <button
            type="button"
            aria-label="Next page"
            className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors duration-200 hover:bg-accent hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  )
}
