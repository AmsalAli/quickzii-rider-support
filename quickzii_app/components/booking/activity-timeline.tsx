import type { TimelineActor, TimelineEvent } from "@/lib/booking-data"
import { Card } from "@/components/booking/card"
import { cn } from "@/lib/utils"

const ACTOR_STYLES: Record<TimelineActor, { badge: string; dot: string; label: string }> = {
  SYSTEM: { badge: "bg-muted text-muted-foreground border-border", dot: "bg-[#6b7280]", label: "SYSTEM" },
  AI_AGENT: { badge: "bg-primary/15 text-[#c084fc] border-primary/30", dot: "bg-primary", label: "AI_AGENT" },
  HUMAN_AGENT: { badge: "bg-[#3b82f6]/15 text-[#60a5fa] border-[#3b82f6]/30", dot: "bg-[#3b82f6]", label: "HUMAN_AGENT" },
  RIDER: { badge: "bg-[#f59e0b]/15 text-[#fbbf24] border-[#f59e0b]/30", dot: "bg-[#f59e0b]", label: "RIDER" },
}

export function ActivityTimeline({ timeline }: { timeline: TimelineEvent[] }) {
  return (
    <Card title="Activity Timeline">
      <ol className="relative ml-1.5 border-l border-border">
        {timeline.map((event, i) => {
          const style = ACTOR_STYLES[event.actor]
          return (
            <li key={i} className="relative pb-6 pl-6 last:pb-0">
              <span
                className={cn(
                  "absolute -left-[7px] top-1 h-3 w-3 rounded-full ring-4 ring-card",
                  style.dot,
                )}
                aria-hidden
              />
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-mono text-sm text-muted-foreground">{event.timestamp}</span>
                <span
                  className={cn(
                    "rounded-full border px-2 py-0.5 font-mono text-[11px] font-medium",
                    style.badge,
                  )}
                >
                  {style.label}
                </span>
              </div>
              <p className="mt-1 text-sm text-foreground">{event.description}</p>
            </li>
          )
        })}
      </ol>
    </Card>
  )
}
