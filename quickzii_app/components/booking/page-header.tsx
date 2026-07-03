import { ArrowLeft, ChevronRight } from "lucide-react"
import type { BookingStatus } from "@/lib/booking-data"
import { StatusBadge } from "@/components/booking/status-badge"

export function PageHeader({
  bookingId,
  status,
}: {
  bookingId: string
  status: BookingStatus
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div>
        <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground">
          <a href="#" className="transition-colors hover:text-foreground">
            Bookings
          </a>
          <ChevronRight className="h-4 w-4 text-tertiary-foreground" />
          <span className="text-foreground">{bookingId}</span>
        </nav>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-balance">
          Booking {bookingId}
        </h1>
      </div>

      <div className="flex items-center gap-3">
        <StatusBadge status={status} />
        <a
          href="#"
          className="inline-flex items-center gap-2 rounded-lg border border-primary/50 px-3.5 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Bookings
        </a>
      </div>
    </div>
  )
}
