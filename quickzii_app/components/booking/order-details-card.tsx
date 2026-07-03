import type { BookingDetail } from "@/lib/booking-data"
import { Card, FieldRow } from "@/components/booking/card"
import { StatusBadge } from "@/components/booking/status-badge"
import { CopyButton } from "@/components/booking/copy-button"

export function OrderDetailsCard({ booking }: { booking: BookingDetail["booking"] }) {
  return (
    <Card title="Order Details">
      <div className="divide-y divide-border">
        <FieldRow label="Order ID">{booking.id}</FieldRow>
        <FieldRow label="Order Status">
          <StatusBadge status={booking.status} />
        </FieldRow>
        <FieldRow label="Created At">{booking.createdAt}</FieldRow>
        <FieldRow label="Estimated Delivery">{booking.estimatedDelivery}</FieldRow>
        <FieldRow label="Delivery Confirmation Code">
          <span className="inline-flex items-center gap-2">
            <code className="rounded bg-muted px-2 py-0.5 font-mono text-sm tracking-widest text-foreground">
              {booking.deliveryCode}
            </code>
            <CopyButton value={booking.deliveryCode} label="confirmation code" />
          </span>
        </FieldRow>
        <FieldRow label="Retry Status">{booking.retryStatus}</FieldRow>
        <FieldRow label="Retry Count">{booking.retryCount}</FieldRow>
      </div>
    </Card>
  )
}
