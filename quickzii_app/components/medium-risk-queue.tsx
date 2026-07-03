"use client"

import { useState } from "react"
import { Check, RotateCcw, ArrowRight, CheckCircle2 } from "lucide-react"
import type { MediumRiskCase } from "@/lib/mock-data"
import { IntentBadge, RiskBadge } from "@/components/badges"
import { useToast } from "@/components/toast"
import { Button } from "@/components/ui/button"

export function MediumRiskQueue({ cases }: { cases: MediumRiskCase[] }) {
  const [items, setItems] = useState(cases)
  const [removing, setRemoving] = useState<string[]>([])
  const toast = useToast()

  function remove(id: string, message: string) {
    setRemoving((prev) => [...prev, id])
    toast(message)
    setTimeout(() => {
      setItems((prev) => prev.filter((c) => c.id !== id))
      setRemoving((prev) => prev.filter((x) => x !== id))
    }, 220)
  }

  return (
    <div className="space-y-5">
      <p className="text-sm text-muted-foreground">
        The AI has classified these cases as MEDIUM risk and has prepared a suggested reply. Review
        and approve, edit, or reject.
      </p>

      {items.length === 0 ? (
        <EmptyState />
      ) : (
        items.map((c) => (
          <MediumRiskCard
            key={c.id}
            data={c}
            removing={removing.includes(c.id)}
            onApprove={() => remove(c.id, "Reply sent to rider")}
            onReject={() => remove(c.id, "Conversation handed off to you")}
          />
        ))
      )}
    </div>
  )
}

function MediumRiskCard({
  data,
  removing,
  onApprove,
  onReject,
}: {
  data: MediumRiskCase
  removing: boolean
  onApprove: () => void
  onReject: () => void
}) {
  const [reply, setReply] = useState(data.proposedReply)

  return (
    <div
      className="rounded-2xl border border-border bg-card p-5 transition-all duration-200 sm:p-6"
      style={{ opacity: removing ? 0 : 1, transform: removing ? "scale(0.99)" : "none" }}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-foreground">{data.riderName}</span>
          <a href="#" className="text-sm text-primary hover:underline">
            Booking {data.bookingId}
          </a>
        </div>
        <div className="flex-1" />
        <IntentBadge intent={data.intent} />
        <RiskBadge tier={data.riskTier} />
        <span className="text-xs text-muted-foreground">{data.waitingSince}</span>
      </div>

      {/* Conversation context */}
      <div className="mt-4 space-y-3 rounded-lg bg-muted/30 p-4">
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Rider message:</p>
          <div className="space-y-1">
            {data.riderMessages.map((m, i) => (
              <p key={i} className="text-sm text-foreground">
                {`"${m}"`}
              </p>
            ))}
          </div>
        </div>
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Agent reasoning:</p>
          <p className="text-sm text-foreground">{data.agentReasoning}</p>
        </div>
      </div>

      {/* Proposed reply */}
      <div className="mt-4">
        <label
          htmlFor={`reply-${data.id}`}
          className="text-xs text-muted-foreground"
        >
          Proposed reply to rider:
        </label>
        <textarea
          id={`reply-${data.id}`}
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          rows={3}
          className="mt-1.5 w-full resize-y rounded-lg border border-input bg-background px-3 py-2.5 text-sm text-foreground outline-none transition-colors duration-200 placeholder:text-tertiary-foreground focus:border-ring focus:ring-1 focus:ring-ring"
        />
        <div className="mt-1.5 flex items-center justify-between">
          <span className="text-xs text-tertiary-foreground">{reply.length} characters</span>
          <button
            type="button"
            onClick={() => setReply(data.proposedReply)}
            disabled={reply === data.proposedReply}
            className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors duration-200 hover:text-foreground disabled:opacity-40 disabled:hover:text-muted-foreground"
          >
            <RotateCcw className="h-3 w-3" />
            Reset to AI suggestion
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button onClick={onApprove} className="gap-1.5">
          <Check className="h-4 w-4" />
          Approve &amp; Send
        </Button>
        <Button
          onClick={onReject}
          variant="outline"
          className="gap-1.5 border-destructive/40 text-[#f87171] hover:bg-destructive/10 hover:text-[#f87171]"
        >
          Reject &amp; Take Over
        </Button>
        <a
          href="#"
          className="ml-auto inline-flex items-center gap-1 text-sm text-primary hover:underline"
        >
          View full conversation
          <ArrowRight className="h-3.5 w-3.5" />
        </a>
      </div>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-border bg-card px-6 py-16 text-center">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
        <CheckCircle2 className="h-6 w-6 text-muted-foreground" />
      </span>
      <h3 className="mt-4 text-base font-medium text-foreground">No cases waiting for review</h3>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">
        The AI is handling everything in real time. You&apos;ll be notified when something needs your
        attention.
      </p>
    </div>
  )
}
