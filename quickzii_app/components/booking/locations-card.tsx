import type { BookingDetail } from "@/lib/booking-data"
import { Card } from "@/components/booking/card"

export function LocationsCard({
  pickup,
  dropoff,
}: {
  pickup: BookingDetail["pickup"]
  dropoff: BookingDetail["dropoff"]
}) {
  return (
    <Card title="Locations">
      <div className="space-y-5">
        {/* Pickup */}
        <div className="flex gap-3">
          <span className="mt-1.5 h-3 w-3 shrink-0 rounded-full bg-[#22c55e] ring-4 ring-[#22c55e]/15" aria-hidden />
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#4ade80]">Pickup</p>
            <p className="mt-1 font-medium text-foreground">{pickup.restaurantName}</p>
            <p className="text-sm text-muted-foreground">{pickup.restaurantId}</p>
            <p className="mt-1 text-sm text-muted-foreground">{pickup.address}</p>
          </div>
        </div>

        <div className="ml-1.5 h-5 border-l border-dashed border-border" aria-hidden />

        {/* Drop-off */}
        <div className="flex gap-3">
          <span className="mt-1.5 h-3 w-3 shrink-0 rounded-full bg-[#ef4444] ring-4 ring-[#ef4444]/15" aria-hidden />
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide text-[#f87171]">Drop-off</p>
            <p className="mt-1 font-medium text-foreground">{dropoff.customerAddress}</p>
            <div className="mt-2 flex gap-4 text-sm text-muted-foreground">
              <span>
                <span className="text-foreground">{dropoff.distanceKm} km</span> distance
              </span>
              <span>
                <span className="text-foreground">{dropoff.estimatedMin} min</span> est.
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  )
}
