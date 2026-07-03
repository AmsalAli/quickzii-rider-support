import type { DriverDetail } from "@/lib/driver-data"
import { CopyButton } from "./copy-button"

function Row({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-border/60 py-3 last:border-b-0">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="flex items-center gap-1.5 text-right text-sm font-medium text-foreground">
        {children}
      </dd>
    </div>
  )
}

export function ProfileCard({
  driver,
  onCopied,
}: {
  driver: DriverDetail["driver"]
  onCopied: (label: string) => void
}) {
  return (
    <section className="rounded-2xl border border-border bg-card p-5 sm:p-6">
      <h2 className="text-sm font-semibold text-foreground">Profile</h2>
      <dl className="mt-2">
        <Row label="Full name">
          {driver.firstName} {driver.lastName}
        </Row>
        <Row label="Email">
          <span className="truncate">{driver.email}</span>
          <CopyButton value={driver.email} label="Email" onCopied={onCopied} />
        </Row>
        <Row label="Phone number">
          <span>{driver.phone}</span>
          <CopyButton value={driver.phone} label="Phone number" onCopied={onCopied} />
        </Row>
        <Row label="Organization">
          <a
            href="#"
            className="text-primary transition-colors duration-200 hover:text-primary/80"
          >
            {driver.organization}
          </a>
        </Row>
        <Row label="Invited">{driver.invitedAt}</Row>
      </dl>
    </section>
  )
}
