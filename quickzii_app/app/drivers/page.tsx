import { DriverDetail } from "@/components/quickzii/driver-detail"
import { mockDriverDetail } from "@/lib/driver-data"

const MT = process.env.MOTIONTOOLS_URL || "http://127.0.0.1:8001"

async function getFirstBusyDriver() {
  try {
    const list = await fetch(`${MT}/drivers?status=busy&limit=1`, { cache: "no-store" }).then(r => r.json())
    if (!list?.length) return mockDriverDetail
    const full = await fetch(`${MT}/drivers/${list[0].id}`, { cache: "no-store" }).then(r => r.json())
    return {
      ...mockDriverDetail,
      driver: {
        ...mockDriverDetail.driver,
        id: full.id.slice(0, 8),
        firstName: full.first_name,
        lastName: full.last_name,
        email: full.email,
        phone: full.phone_number,
        organization: full.organization ?? "-",
        status: (full.status ?? "offline") as "available" | "busy" | "offline" | "invited",
      },
      capabilities: {
        ...mockDriverDetail.capabilities,
        vehicle: full.vehicle_type === "car_small" ? "Car" : "Bike",
        serviceArea: full.service_area ?? "-",
      },
      activeTour: full.active_booking_summary ? {
        bookingId: full.active_booking_summary.external_id ?? full.active_booking_summary.booking_id?.slice(0, 8) ?? "-",
        acceptedAt: new Date().toLocaleString(),
        restaurantName: full.active_booking_summary.restaurant_name ?? "-",
        dropoffAddress: full.active_booking_summary.dropoff_address ?? "-",
      } : null,
    }
  } catch { return mockDriverDetail }
}

export default async function Page() {
  const data = await getFirstBusyDriver()
  return <DriverDetail data={data} />
}
