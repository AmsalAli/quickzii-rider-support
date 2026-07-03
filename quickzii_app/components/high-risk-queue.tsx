"use client"

import { useState } from "react"
import { Send, ArrowRight } from "lucide-react"
import type { HighRiskCase } from "@/lib/mock-data"
import { IntentBadge, RiskBadge } from "@/components/badges"
import { useToast } from "@/components/toast"
import { Button } from "@/components/ui/button"

const QUICK_ACTIONS: Record<string, string> = {
  "Issue refund":
    "Hi, I'm sorry about this. I've issued a full refund for your order — it should appear within 3–5 business days. ",
  "Replace order":
    "Hi, apologies for the trouble. We're preparing a replacement order now and it will be dispatched shortly. ",
  "Cancel + investigate":
    "Hi, I've cancelled this booking and opened an investigation. We'll follow up with you directly with the outcome. ",
  "Compensate rider":
    "Hi, thank you for flagging this. We've added compensation to your account for the inconvenience caused. ",
}

export function HighRiskQueue({ cases }: { cases: HighRiskCase[] }) {
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
        The AI has classified these cases as HIGH risk and has NOT taken action. These require full
        human handling.
      </p>

      {items.map((c) => (
        <HighRiskCard
          key={c.id}
          data={c}
          removing={removing.includes(c.id)}
          onSend={() => remove(c.id, "Reply sent to rider")}
          onCancel={() => remove(c.id, "Booking cancelled")}
        />
      ))}
    </div>
  )
}

function HighRiskCard({
  data,
  removing,
  onSend,
  onCancel,
}: {
  data: HighRiskCase
  removing: boolean
  onSend: () => void
  onCancel: () => void
}) {
  const [reply, setReply] = useState("")

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
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground">Booking context:</p>
          <p className="text-sm text-foreground">{data.bookingContext}</p>
        </div>
      </div>

      {/* Reply composer */}
      <div className="mt-4">
        <div className="mb-2 flex flex-wrap gap-2">
          {Object.keys(QUICK_ACTIONS).map((label) => (
            <button
              key={label}
              type="button"
              onClick={() => setReply(QUICK_ACTIONS[label])}
              className="rounded-full border border-border bg-muted/40 px-3 py-1 text-xs text-muted-foreground transition-colors duration-200 hover:border-primary/40 hover:text-foreground"
            >
              {label}
            </button>
          ))}
        </div>
        <label htmlFor={`reply-${data.id}`} className="sr-only">
          Reply to rider
        </label>
        <textarea
          id={`reply-${data.id}`}
          value={reply}
          onChange={(e) => setReply(e.target.value)}
          rows={3}
          placeholder="Type your reply to the rider..."
          className="w-full resize-y rounded-lg border border-input bg-background px-3 py-2.5 text-sm text-foreground outline-none transition-colors duration-200 placeholder:text-tertiary-foreground focus:border-ring focus:ring-1 focus:ring-ring"
        />
      </div>

      {/* Actions */}
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button onClick={onSend} disabled={reply.trim().length === 0} className="gap-1.5">
          <Send className="h-4 w-4" />
          Send Reply
        </Button>
        <Button
          onClick={onCancel}
          variant="outline"
          className="gap-1.5 border-destructive/40 text-[#f87171] hover:bg-destructive/10 hover:text-[#f87171]"
        >
          Cancel Booking
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
