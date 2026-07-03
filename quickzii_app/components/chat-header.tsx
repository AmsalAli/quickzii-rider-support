"use client"

import { ChevronDown, MapPin, Store } from "lucide-react"
import type { ActiveBooking, Rider } from "@/lib/mock-rider-session"

interface ChatHeaderProps {
  rider: Rider
  activeBooking: ActiveBooking | null
  expanded: boolean
  onToggle: () => void
}

export function ChatHeader({ rider, activeBooking, expanded, onToggle }: ChatHeaderProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-background/95 backdrop-blur">
      <div className="flex items-center justify-between gap-2 px-4 py-3">
        {/* Left: rider */}
        <div className="flex min-w-0 items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent text-sm font-semibold text-foreground">
            {rider.initial}
          </div>
          <span className="truncate text-sm font-medium text-muted-foreground">{rider.firstName}</span>
        </div>

        {/* Center: title */}
        <h1 className="absolute left-1/2 -translate-x-1/2 text-base font-semibold text-foreground">Support</h1>

        {/* Right: booking pill */}
        {activeBooking ? (
          <button
            type="button"
            onClick={onToggle}
            aria-expanded={expanded}
            className="flex shrink-0 items-center gap-1 rounded-full border border-primary/40 bg-primary/15 px-3 py-1.5 text-xs font-semibold text-primary transition-colors duration-200 hover:bg-primary/25"
          >
            {activeBooking.id}
            <ChevronDown
              className={`h-3.5 w-3.5 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
            />
          </button>
        ) : (
          <span className="shrink-0 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground">
            No booking
          </span>
        )}
      </div>

      {/* Expandable booking context */}
      {activeBooking && (
        <div
          className={`grid overflow-hidden transition-all duration-200 ease-out ${
            expanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0"
          }`}
        >
          <div className="min-h-0">
            <div className="mx-4 mb-3 space-y-2.5 rounded-xl border border-border bg-card p-3 text-xs">
              <div className="flex items-center gap-2 text-muted-foreground">
                <Store className="h-4 w-4 shrink-0 text-primary" />
                <span className="text-foreground">{activeBooking.restaurant}</span>
              </div>
              <div className="flex items-center gap-2 text-muted-foreground">
                <MapPin className="h-4 w-4 shrink-0 text-primary" />
                <span>{activeBooking.dropoffAddress}</span>
              </div>
              <div className="flex items-center gap-2 pt-0.5">
                <span className="rounded-full bg-primary/15 px-2.5 py-1 text-[11px] font-semibold text-primary">
                  {activeBooking.status}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
