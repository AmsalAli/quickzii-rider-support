import type { DriverDetail } from "@/lib/driver-data"
import { TourStatusBadge } from "./status-badge"

export function RecentToursCard({
  recentTours,
}: {
  recentTours: DriverDetail["recentTours"]
}) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5 sm:p-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">Recent Tours</h2>
        <a
          href="#"
          className="text-sm font-medium text-primary transition-colors duration-200 hover:text-primary/80"
        >
          View all
        </a>
      </div>

      <div className="mt-4 overflow-x-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs font-medium uppercase tracking-wide text-tertiary-foreground">
              <th className="py-2 pr-4 font-medium">Date/Time</th>
              <th className="py-2 pr-4 font-medium">Booking ID</th>
              <th className="py-2 pr-4 font-medium">Restaurant</th>
              <th className="py-2 font-medium">Status</th>
            </tr>
          </thead>
          <tbody>
            {recentTours.map((tour) => (
              <tr
                key={tour.bookingId}
                className="border-b border-border/60 last:border-b-0"
              >
                <td className="whitespace-nowrap py-3 pr-4 text-muted-foreground">
                  {tour.dateTime}
                </td>
                <td className="whitespace-nowrap py-3 pr-4 font-medium text-foreground">
                  {tour.bookingId}
                </td>
                <td className="py-3 pr-4 text-foreground">{tour.restaurant}</td>
                <td className="py-3">
                  <TourStatusBadge status={tour.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
