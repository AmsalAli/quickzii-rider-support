import { cn } from "@/lib/utils"
import { STATUS_LABELS, type BookingStatus } from "@/lib/booking-data"

const STATUS_STYLES: Record<BookingStatus, string> = {
  completed: "bg-[#22c55e]/15 text-[#4ade80] border-[#22c55e]/30",
  in_progress: "bg-[#22c55e]/15 text-[#4ade80] border-[#22c55e]/30",
  pending: "bg-[#f59e0b]/15 text-[#fbbf24] border-[#f59e0b]/30",
  cancelled: "bg-[#ef4444]/15 text-[#f87171] border-[#ef4444]/30",
  scheduled: "bg-[#3b82f6]/15 text-[#60a5fa] border-[#3b82f6]/30",
  redispatched: "bg-primary/15 text-[#c084fc] border-primary/30",
}

export function StatusBadge({
  status,
  className,
}: {
  status: BookingStatus
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        STATUS_STYLES[status],
        className,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
      {STATUS_LABELS[status]}
    </span>
  )
}
