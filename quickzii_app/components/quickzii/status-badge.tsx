import { cn } from "@/lib/utils"
import type { DriverStatus, TourStatus } from "@/lib/driver-data"

const driverStyles: Record<DriverStatus, { label: string; className: string; dot: string }> = {
  available: {
    label: "Available",
    className: "bg-[#22c55e]/15 text-[#4ade80] border-[#22c55e]/30",
    dot: "bg-[#4ade80]",
  },
  busy: {
    label: "Busy",
    className: "bg-[#f59e0b]/15 text-[#fbbf24] border-[#f59e0b]/30",
    dot: "bg-[#fbbf24]",
  },
  offline: {
    label: "Offline",
    className: "bg-muted text-muted-foreground border-border",
    dot: "bg-muted-foreground",
  },
  invited: {
    label: "Invited",
    className: "bg-[#3b82f6]/15 text-[#60a5fa] border-[#3b82f6]/30",
    dot: "bg-[#60a5fa]",
  },
}

const tourStyles: Record<TourStatus, { label: string; className: string; dot: string }> = {
  completed: {
    label: "Completed",
    className: "bg-[#22c55e]/15 text-[#4ade80] border-[#22c55e]/30",
    dot: "bg-[#4ade80]",
  },
  cancelled: {
    label: "Cancelled",
    className: "bg-[#ef4444]/15 text-[#f87171] border-[#ef4444]/30",
    dot: "bg-[#f87171]",
  },
  in_progress: {
    label: "In progress",
    className: "bg-[#3b82f6]/15 text-[#60a5fa] border-[#3b82f6]/30",
    dot: "bg-[#60a5fa]",
  },
}

const pillBase =
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium"

export function DriverStatusBadge({
  status,
  className,
}: {
  status: DriverStatus
  className?: string
}) {
  const style = driverStyles[status]
  return (
    <span className={cn(pillBase, style.className, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", style.dot)} aria-hidden />
      {style.label}
    </span>
  )
}

export function TourStatusBadge({
  status,
  className,
}: {
  status: TourStatus
  className?: string
}) {
  const style = tourStyles[status]
  return (
    <span className={cn(pillBase, style.className, className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", style.dot)} aria-hidden />
      {style.label}
    </span>
  )
}
