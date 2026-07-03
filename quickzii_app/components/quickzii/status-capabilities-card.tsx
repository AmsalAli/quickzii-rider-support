import { Bike } from "lucide-react"
import type { DriverDetail } from "@/lib/driver-data"
import { DriverStatusBadge } from "./status-badge"

function Field({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 py-2">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-right text-sm font-medium text-foreground">{children}</span>
    </div>
  )
}

export function StatusCapabilitiesCard({
  driver,
  capabilities,
}: {
  driver: DriverDetail["driver"]
  capabilities: DriverDetail["capabilities"]
}) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5 sm:p-6">
      <h2 className="text-sm font-semibold text-foreground">Status &amp; Capabilities</h2>

      <div className="mt-4 grid gap-6 sm:grid-cols-2">
        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-tertiary-foreground">
            Status
          </h3>
          <div className="mt-2 divide-y divide-border/60">
            <Field label="Status">
              <DriverStatusBadge status={driver.status} />
            </Field>
            <Field label="Mute state">{driver.muteState}</Field>
            <Field label="Org change allowed">
              {driver.organizationChangeAllowed ? "Yes" : "No"}
            </Field>
            <Field label="Blocked">{driver.blocked ? "Yes" : "No"}</Field>
          </div>
        </div>

        <div>
          <h3 className="text-xs font-medium uppercase tracking-wide text-tertiary-foreground">
            Capabilities
          </h3>
          <div className="mt-2 divide-y divide-border/60">
            <Field label="Vehicle">
              <span className="inline-flex items-center gap-1.5">
                <Bike className="h-4 w-4 text-muted-foreground" />
                {capabilities.vehicle}
              </span>
            </Field>
            <Field label="Service area">{capabilities.serviceArea}</Field>
            <Field label="Restricted to areas">
              {capabilities.restrictedToServiceAreas ? "Restricted" : "Unrestricted"}
            </Field>
          </div>
        </div>
      </div>
    </section>
  )
}
