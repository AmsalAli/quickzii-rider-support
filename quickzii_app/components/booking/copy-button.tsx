"use client"

import { useState } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"
import { showToast } from "@/components/booking/toaster"

export function CopyButton({
  value,
  label,
  onCopied,
}: {
  value: string
  label: string
  onCopied?: () => void
}) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      showToast("Copied")
      onCopied?.()
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard unavailable; silently ignore.
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={`Copy ${label}`}
      className={cn(
        "inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-md border border-border text-muted-foreground transition-colors",
        "hover:border-primary/50 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
      )}
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-[#4ade80]" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
    </button>
  )
}
