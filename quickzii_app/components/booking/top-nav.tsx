import { Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const NAV_LINKS = [
  "Home",
  "Operations",
  "Tours",
  "Bookings",
  "Analytics",
  "Customers",
  "Drivers",
  "Places",
  "Organizations",
]

const ACTIVE = "Bookings"

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1280px] items-center gap-6 px-6">
        <a href="#" className="text-lg font-semibold tracking-tight text-primary">
          Quickzii
        </a>

        <nav className="hidden flex-1 items-center gap-1 lg:flex" aria-label="Primary">
          {NAV_LINKS.map((link) => {
            const isActive = link === ACTIVE
            return (
              <a
                key={link}
                href="#"
                aria-current={isActive ? "page" : undefined}
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm transition-colors",
                  isActive
                    ? "bg-primary/10 font-medium text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {link}
              </a>
            )
          })}
        </nav>

        <div className="ml-auto flex items-center gap-3">
          <button
            type="button"
            aria-label="Settings"
            className="inline-flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Settings className="h-5 w-5" />
          </button>
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground"
            aria-hidden
          >
            JD
          </div>
        </div>
      </div>
    </header>
  )
}
