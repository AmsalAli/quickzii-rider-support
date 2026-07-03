import { Smile } from "lucide-react"

export function NoBookingState() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-8 text-center">
      <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/15">
        <Smile className="h-10 w-10 text-primary" />
      </div>
      <h2 className="mt-6 text-lg font-semibold text-foreground text-balance">
        You don&apos;t have an active booking right now
      </h2>
      <p className="mt-2 max-w-xs text-sm leading-relaxed text-muted-foreground text-pretty">
        Is everything OK? Reach out anytime when you&apos;re on a delivery.
      </p>
    </div>
  )
}
