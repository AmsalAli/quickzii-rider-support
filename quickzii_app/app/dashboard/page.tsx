import { Dashboard } from "@/components/dashboard"
import type { DashboardState } from "@/lib/mock-data"
import Link from "next/link"

const AGENT = process.env.AGENT_URL || "http://127.0.0.1:8002"

async function getDashboardState(): Promise<DashboardState> {
  try {
    const [medium, high, audit] = await Promise.all([
      fetch(`${AGENT}/escalations/medium`, { cache: "no-store" }).then(r => r.json()),
      fetch(`${AGENT}/escalations/high`,   { cache: "no-store" }).then(r => r.json()),
      fetch(`${AGENT}/audit?limit=100`,    { cache: "no-store" }).then(r => r.json()),
    ])

    const pending = [...medium, ...high].filter((i: any) => i.status === "pending").length
    const inReview = medium.filter((i: any) => i.status === "pending").length

    const closed = audit.filter((r: any) => r.event_type === "conversation_closed")

    return {
      stats: {
        pending,
        inReview,
        resolvedToday: closed.length,
      },
      mediumRiskQueue: medium
        .filter((i: any) => i.status === "pending")
        .map((i: any) => ({
          id: i.id,
          riderName: i.rider_id?.slice(0, 8) ?? "Rider",
          riderId: i.rider_id,
          bookingId: i.booking_id ?? "-",
          intent: i.intent,
          riskTier: "MEDIUM" as const,
          waitingSince: new Date(i.created_at).toLocaleTimeString(),
          riderMessages: i.rider_messages ?? [],
          agentReasoning: i.agent_reasoning ?? "",
          proposedReply: i.proposed_reply ?? "",
        })),
      highRiskQueue: high
        .filter((i: any) => i.status === "pending")
        .map((i: any) => ({
          id: i.id,
          riderName: i.rider_id?.slice(0, 8) ?? "Rider",
          riderId: i.rider_id,
          bookingId: i.booking_id ?? "-",
          intent: i.intent,
          riskTier: "HIGH" as const,
          waitingSince: new Date(i.created_at).toLocaleTimeString(),
          riderMessages: i.rider_messages ?? [],
          agentReasoning: i.agent_reasoning ?? "",
          bookingContext: i.booking_id ? `Booking: ${i.booking_id.slice(0, 8)}` : "No booking",
        })),
      auditLog: closed.slice(0, 50).map((r: any, idx: number) => ({
        id: r.id || String(idx),
        timestamp: new Date(r.timestamp).toLocaleTimeString(),
        bookingId: r.booking_id?.slice(0, 8) ?? "-",
        riderName: r.rider_id?.slice(0, 8) ?? "-",
        intent: r.extra?.intent ?? "-",
        riskTier: (r.extra?.risk_level?.toUpperCase() ?? "LOW") as any,
        outcome:
          r.extra?.outcome === "escalated"
            ? "Escalated, human handled"
            : r.extra?.outcome === "rider_declined_help"
            ? "Rider declined help"
            : "Auto-resolved",
        processingTime: r.extra?.processing_time_ms
          ? `${(r.extra.processing_time_ms / 1000).toFixed(1)}s`
          : "-",
      })),
    }
  } catch (e) {
    console.error("Failed to fetch dashboard state:", e)
    return {
      stats: { pending: 0, inReview: 0, resolvedToday: 0 },
      mediumRiskQueue: [],
      highRiskQueue: [],
      auditLog: [],
    }
  }
}

function TopNav() {
  const links = [
    { href: "/", label: "Rider Chat" },
    { href: "/bookings", label: "Bookings" },
    { href: "/drivers", label: "Drivers" },
    { href: "/dashboard", label: "AI Support", active: true },
  ]
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1280px] items-center justify-between px-6">
        <Link href="/" className="text-lg font-semibold text-primary">
          Quickzii
        </Link>
        <nav className="flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={
                l.active
                  ? "rounded-md bg-primary/10 px-3 py-1.5 text-sm font-medium text-foreground"
                  : "rounded-md px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
              }
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <div className="h-9 w-9 rounded-full bg-primary" />
      </div>
    </header>
  )
}

export default async function Page() {
  const state = await getDashboardState()
  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav />
      <Dashboard state={state} />
    </div>
  )
}
