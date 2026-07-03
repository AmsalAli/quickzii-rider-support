"use client"

import { useEffect, useState } from "react"
import { ArrowLeft, Check } from "lucide-react"
import { mockDriverDetail, mockDriverDetailNoTour } from "@/lib/driver-data"
import { TopNav } from "./top-nav"
import { DriverStatusBadge } from "./status-badge"
import { ActiveTourCard } from "./active-tour-card"
import { ProfileCard } from "./profile-card"
import { StatusCapabilitiesCard } from "./status-capabilities-card"
import { RecentToursCard } from "./recent-tours-card"
import { MapPanel } from "./map-panel"

import type { DriverDetail as DriverDetailType } from "@/lib/driver-data"

export function DriverDetail({ data: injected }: { data?: DriverDetailType } = {}) {
  const [hasActiveTour, setHasActiveTour] = useState(true)
  const [toast, setToast] = useState<string | null>(null)
  const isDev = process.env.NODE_ENV !== "production"

  const data = injected ?? (hasActiveTour ? mockDriverDetail : mockDriverDetailNoTour)
  const { driver } = data

  function showToast(label: string) {
    setToast(`${label} copied to clipboard`)
  }

  useEffect(() => {
    if (!toast) return
    const timer = setTimeout(() => setToast(null), 2000)
    return () => clearTimeout(timer)
  }, [toast])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav active="Drivers" />

      <main className="mx-auto max-w-[1280px] px-6 py-8">
        {isDev && (
          <div className="mb-6 flex items-center gap-3 rounded-lg border border-dashed border-border bg-muted/40 px-4 py-2.5">
            <span className="text-xs font-medium text-tertiary-foreground">
              DEV
            </span>
            <span className="text-xs text-muted-foreground">Active tour state</span>
            <button
              type="button"
              role="switch"
              aria-checked={hasActiveTour}
              onClick={() => setHasActiveTour((v) => !v)}
              className={`relative h-5 w-9 rounded-full transition-colors duration-200 ${
                hasActiveTour ? "bg-primary" : "bg-border"
              }`}
            >
              <span
                className={`absolute top-0.5 h-4 w-4 rounded-full bg-foreground transition-transform duration-200 ${
                  hasActiveTour ? "translate-x-4" : "translate-x-0.5"
                }`}
              />
            </button>
            <span className="text-xs text-muted-foreground">
              {hasActiveTour ? "Has active tour" : "No active tour"}
            </span>
          </div>
        )}

        <a
          href="#"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors duration-200 hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </a>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-balance sm:text-3xl">
            {driver.firstName} {driver.lastName}
          </h1>
          <DriverStatusBadge status={driver.status} />
        </div>

        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[3fr_2fr]">
          <div className="flex flex-col gap-6">
            <ActiveTourCard activeTour={data.activeTour} />
            <ProfileCard driver={driver} onCopied={showToast} />
            <StatusCapabilitiesCard
              driver={driver}
              capabilities={data.capabilities}
            />
            <RecentToursCard recentTours={data.recentTours} />
          </div>

          <MapPanel location={data.lastKnownLocation} />
        </div>
      </main>

      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-6 left-1/2 z-50 -translate-x-1/2"
      >
        {toast && (
          <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground shadow-lg">
            <Check className="h-4 w-4 text-[#4ade80]" />
            {toast}
          </div>
        )}
      </div>
    </div>
  )
}
