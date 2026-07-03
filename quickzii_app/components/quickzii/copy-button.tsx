"use client"

import { useState } from "react"
import { Check, Copy } from "lucide-react"
import { cn } from "@/lib/utils"

export function CopyButton({
  value,
  label,
  onCopied,
}: {
  value: string
  label: string
  onCopied?: (label: string) => void
}) {
  const [copied, setCopied] = useState(false)

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(value)
      setCopied(true)
      onCopied?.(label)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      // Clipboard not available — fail silently.
    }
  }

  return (
    <button
      type="button"
      onClick={handleCopy}
      aria-label={`Copy ${label}`}
      className={cn(
        "flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-muted-foreground transition-colors duration-200 hover:bg-muted hover:text-foreground",
        copied && "text-[#4ade80] hover:text-[#4ade80]",
      )}
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
    </button>
  )
}
