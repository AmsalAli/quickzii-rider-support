"use client"

import type { QuickReply } from "@/lib/mock-rider-session"

interface QuickRepliesProps {
  replies: QuickReply[]
  onSelect: (reply: string, intent: string) => void
  /** vertical stack for the initial full list, horizontal scroll row otherwise */
  layout: "stack" | "row"
}

export function QuickReplies({ replies, onSelect, layout }: QuickRepliesProps) {
  if (layout === "stack") {
    return (
      <div className="ml-9 flex flex-col gap-2">
        {replies.map((reply) => (
          <button
            key={reply.label}
            type="button"
            onClick={() => onSelect(reply.label, reply.intent)}
            className="rounded-xl border border-border bg-card px-3.5 py-2.5 text-left text-sm text-foreground transition-colors duration-200 hover:border-primary/50 hover:bg-primary/10 active:scale-[0.99]"
          >
            {reply.label}
          </button>
        ))}
      </div>
    )
  }
  return (
    <div className="ml-9 flex gap-2 overflow-x-auto pb-1 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {replies.map((reply) => (
        <button
          key={reply.label}
          type="button"
          onClick={() => onSelect(reply.label, reply.intent)}
          className="shrink-0 whitespace-nowrap rounded-full border border-primary/40 bg-primary/10 px-3.5 py-1.5 text-xsfont-medium text-primary transition-colors duration-200 hover:bg-primary/20 active:scale-[0.98]"
        >
          {reply.label}
        </button>
      ))}
    </div>
  )
}
