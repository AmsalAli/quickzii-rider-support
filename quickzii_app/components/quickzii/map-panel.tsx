import { MapPin } from "lucide-react"
import type { DriverDetail } from "@/lib/driver-data"

export function MapPanel({
  location,
}: {
  location: DriverDetail["lastKnownLocation"]
}) {
  return (
    <div className="lg:sticky lg:top-20">
      <div className="overflow-hidden rounded-2xl border border-border bg-card">
        <div
          className="relative flex h-[420px] items-center justify-center lg:h-[calc(100vh-7rem)]"
          style={{
            backgroundColor: "#1a1a24",
            backgroundImage:
              "linear-gradient(to right, #2a2a35 1px, transparent 1px), linear-gradient(to bottom, #2a2a35 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        >
          <div className="flex flex-col items-center gap-2 text-center">
            <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f59e0b]/15 ring-1 ring-[#f59e0b]/30">
              <MapPin className="h-5 w-5 text-[#fbbf24]" />
            </span>
            <p className="text-sm font-medium text-foreground">Last known location</p>
            <p className="text-sm text-muted-foreground">
              ({location.lat}, {location.lng})
            </p>
          </div>
        </div>
      </div>
      <p className="mt-2 px-1 text-xs text-tertiary-foreground">
        Live tracking available in production · updated {location.timestamp}
      </p>
    </div>
  )
}
