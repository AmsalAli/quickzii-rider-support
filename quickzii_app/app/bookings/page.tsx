import { TopNav } from "@/components/booking/top-nav"
import { PageHeader } from "@/components/booking/page-header"
import { OrderDetailsCard } from "@/components/booking/order-details-card"
import { LocationsCard } from "@/components/booking/locations-card"
import { CustomerRiderCard } from "@/components/booking/customer-rider-card"
import { ActivityTimeline } from "@/components/booking/activity-timeline"
import { ActionsPanel } from "@/components/booking/actions-panel"
import { Toaster } from "@/components/booking/toaster"
import { mockBookingDetail } from "@/lib/booking-data"

const MT = process.env.MOTIONTOOLS_URL || "http://127.0.0.1:8001"

async function getFirstEnRouteBooking() {
  try {
    const list = await fetch(`${MT}/bookings?status=en_route&limit=1`, { cache: "no-store" }).then(r => r.json())
    if (!list?.length) return mockBookingDetail
    const full = await fetch(`${MT}/bookings/${list[0].id}`, { cache: "no-store" }).then(r => r.json())
    return {
      ...mockBookingDetail,
      booking: {
        ...mockBookingDetail.booking,
        id: full.external_id,
        status: full.status,
        createdAt: new Date(full.created_at).toLocaleString(),
        estimatedDelivery: full.scheduled_at ? new Date(full.scheduled_at).toLocaleString() : "-",
        deliveryCode: full.delivery_code,
        retryStatus: full.retry_status ?? "none",
        retryCount: full.retry_count ?? 0,
      },
      pickup: {
        ...mockBookingDetail.pickup,
        restaurantName: full.restaurant?.name ?? "Unknown",
        restaurantId: full.restaurant?.id?.slice(0, 8) ?? "-",
        address: full.pickup_address,
      },
      dropoff: {
        ...mockBookingDetail.dropoff,
        customerAddress: full.dropoff_address,
      },
      customer: {
        ...mockBookingDetail.customer,
        name: `${full.customer_first_name ?? ""} ${full.customer_last_name ?? ""}`.trim() || "Customer",
        phone: full.customer_phone ?? "-",
      },
      rider: full.driver ? {
        id: full.driver.id.slice(0, 8),
        name: `${full.driver.first_name} ${full.driver.last_name}`,
        vehicle: full.driver.vehicle_type === "car_small" ? "Car" : "Bike",
        serviceArea: full.driver.service_area ?? "-",
      } : mockBookingDetail.rider,
    }
  } catch { return mockBookingDetail }
}

export default async function Page() {
  const data = await getFirstEnRouteBooking()
  return (
    <div className="min-h-screen bg-background text-foreground">
      <TopNav />
      <main className="mx-auto max-w-[1280px] px-6 py-8">
        <PageHeader booking={data.booking} />
        <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-[2fr_1.5fr_1.5fr]">
          <OrderDetailsCard booking={data.booking} />
          <LocationsCard pickup={data.pickup} dropoff={data.dropoff} />
          <CustomerRiderCard customer={data.customer} rider={data.rider} />
        </div>
        <ActivityTimeline timeline={data.timeline} />
        <ActionsPanel />
      </main>
      <Toaster />
    </div>
  )
}
