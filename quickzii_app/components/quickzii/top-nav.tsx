import { Settings } from "lucide-react"
import { cn } from "@/lib/utils"

const navLinks = [
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

export function TopNav({ active = "Drivers" }: { active?: string }) {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-[1280px] items-center justify-between px-6">
        <div className="flex items-center gap-8">
          <span className="text-lg font-semibold text-primary">Quickzii</span>
          <nav className="hidden items-center gap-1 lg:flex">
            {navLinks.map((link) => {
              const isActive = link === active
              return (
                <a
                  key={link}
                  href="#"
                  aria-current={isActive ? "page" : undefined}
                  className={cn(
                    "rounded-md px-3 py-1.5 text-sm transition-colors duration-200",
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
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            aria-label="Settings"
            className="flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors duration-200 hover:bg-muted hover:text-foreground"
          >
            <Settings className="h-5 w-5" />
          </button>
          <div
            className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-medium text-primary-foreground"
            aria-label="User avatar"
          >
            AA
          </div>
        </div>
      </div>
    </header>
  )
}
