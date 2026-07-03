import { ArrowRight, Store, MapPin } from "lucide-react"
import type { DriverDetail } from "@/lib/driver-data"

export function ActiveTourCard({
  activeTour,
}: {
  activeTour: DriverDetail["activeTour"]
}) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5 sm:p-6">
      <h2 className="text-sm font-semibold text-foreground">Active Tour</h2>

      {activeTour ? (
        <div className="mt-4 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm text-muted-foreground">
              Accepted on {activeTour.acceptedAt}
            </p>
            <a
              href="#"
              className="text-sm font-medium text-primary transition-colors duration-200 hover:text-primary/80"
            >
              View tour details
            </a>
          </div>

          <div className="flex items-center gap-3 rounded-xl border border-border bg-muted/40 p-4">
            <div className="flex items-center gap-2 text-sm text-foreground">
              <Store className="h-4 w-4 text-muted-foreground" />
              {activeTour.restaurantName}
            </div>
            <ArrowRight className="h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="flex items-center gap-2 text-sm text-foreground">
              <MapPin className="h-4 w-4 text-muted-foreground" />
              {activeTour.dropoffAddress}
            </div>
          </div>

          <p className="text-xs text-tertiary-foreground">
            Booking {activeTour.bookingId}
          </p>
        </div>
      ) : (
        <p className="mt-4 text-sm italic text-muted-foreground">No active tour</p>
      )}
    </section>
  )
}
