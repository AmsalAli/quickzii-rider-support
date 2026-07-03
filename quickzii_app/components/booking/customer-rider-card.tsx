import { Bike, MapPin } from "lucide-react"
import type { BookingDetail } from "@/lib/booking-data"
import { Card } from "@/components/booking/card"
import { CopyButton } from "@/components/booking/copy-button"

export function CustomerRiderCard({
  customer,
  rider,
}: {
  customer: BookingDetail["customer"]
  rider: BookingDetail["rider"]
}) {
  return (
    <Card title="Customer & Rider">
      {/* Customer */}
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Customer</p>
        <p className="font-medium text-foreground">{customer.name}</p>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">{customer.phone}</span>
          <CopyButton value={customer.phone} label="phone number" />
        </div>
      </div>

      <div className="my-5 border-t border-border" />

      {/* Assigned rider */}
      <div className="space-y-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Assigned Rider</p>
        <a
          href={`/drivers/${rider.id}`}
          className="inline-block font-medium text-primary underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded"
        >
          {rider.name}
        </a>
        <p className="text-sm text-muted-foreground">{rider.id}</p>
        <div className="flex items-center gap-2 pt-1 text-sm text-foreground">
          <Bike className="h-4 w-4 text-muted-foreground" />
          {rider.vehicle}
        </div>
        <div className="flex items-center gap-2 text-sm text-foreground">
          <MapPin className="h-4 w-4 text-muted-foreground" />
          {rider.serviceArea}
        </div>
      </div>
    </Card>
  )
}
