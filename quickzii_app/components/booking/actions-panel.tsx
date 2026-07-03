"use client"

import { useEffect, useState } from "react"
import { CheckCircle2, RefreshCw, XCircle } from "lucide-react"
import { Card } from "@/components/booking/card"
import { showToast } from "@/components/booking/toaster"
import { cn } from "@/lib/utils"

type ActionKey = "complete" | "cancel" | "redispatch"

interface ActionConfig {
  key: ActionKey
  label: string
  description: string
  confirmLabel: string
  className: string
  confirmClassName: string
}

const ACTIONS: ActionConfig[] = [
  {
    key: "complete",
    label: "Mark as Complete",
    description: "This will mark booking BK-7392 as delivered and close the order.",
    confirmLabel: "Mark Complete",
    className: "bg-[#22c55e] text-[#052e16] hover:bg-[#16a34a]",
    confirmClassName: "bg-[#22c55e] text-[#052e16] hover:bg-[#16a34a]",
  },
  {
    key: "cancel",
    label: "Cancel Booking",
    description: "This will cancel booking BK-7392. The rider and customer will be notified.",
    confirmLabel: "Cancel Booking",
    className: "border border-[#ef4444]/40 text-[#f87171] hover:bg-[#ef4444]/10",
    confirmClassName: "bg-[#ef4444] text-white hover:bg-[#dc2626]",
  },
  {
    key: "redispatch",
    label: "Redispatch",
    description: "This will reassign booking BK-7392 to a new available rider.",
    confirmLabel: "Redispatch",
    className: "bg-primary text-primary-foreground hover:bg-[#9333ea]",
    confirmClassName: "bg-primary text-primary-foreground hover:bg-[#9333ea]",
  },
]

const ICONS: Record<ActionKey, typeof CheckCircle2> = {
  complete: CheckCircle2,
  cancel: XCircle,
  redispatch: RefreshCw,
}

export function ActionsPanel() {
  const [pending, setPending] = useState<ActionConfig | null>(null)

  function confirm() {
    if (!pending) return
    // Placeholder: no real backend call yet.
    showToast(`${pending.label} triggered`)
    setPending(null)
  }

  return (
    <Card title="Actions">
      <div className="flex flex-col gap-3 sm:flex-row">
        {ACTIONS.map((action) => {
          const Icon = ICONS[action.key]
          return (
            <button
              key={action.key}
              type="button"
              onClick={() => setPending(action)}
              className={cn(
                "inline-flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                action.className,
              )}
            >
              <Icon className="h-4 w-4" />
              {action.label}
            </button>
          )
        })}
      </div>
      <p className="mt-4 text-xs text-muted-foreground">
        These actions can also be triggered by the AI agent via the API.
      </p>

      <ConfirmModal
        action={pending}
        onCancel={() => setPending(null)}
        onConfirm={confirm}
      />
    </Card>
  )
}

function ConfirmModal({
  action,
  onCancel,
  onConfirm,
}: {
  action: ActionConfig | null
  onCancel: () => void
  onConfirm: () => void
}) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onCancel()
    }
    if (action) {
      document.addEventListener("keydown", onKey)
      return () => document.removeEventListener("keydown", onKey)
    }
  }, [action, onCancel])

  if (!action) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="confirm-title"
    >
      <div
        className="absolute inset-0 bg-black/60"
        onClick={onCancel}
        aria-hidden
      />
      <div className="relative w-full max-w-md rounded-2xl border border-border bg-card p-6 shadow-xl">
        <h3 id="confirm-title" className="text-lg font-semibold text-foreground">
          {action.label}?
        </h3>
        <p className="mt-2 text-sm text-muted-foreground">{action.description}</p>
        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-border px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className={cn(
              "rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              action.confirmClassName,
            )}
          >
            {action.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  )
}
