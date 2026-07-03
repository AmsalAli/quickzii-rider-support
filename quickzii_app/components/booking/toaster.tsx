"use client"

import { useEffect, useState } from "react"
import { Check } from "lucide-react"

const TOAST_EVENT = "quickzii:toast"

export function showToast(message: string) {
  if (typeof window === "undefined") return
  window.dispatchEvent(new CustomEvent<string>(TOAST_EVENT, { detail: message }))
}

export function Toaster() {
  const [toast, setToast] = useState<{ id: number; message: string } | null>(null)

  useEffect(() => {
    function handle(e: Event) {
      const message = (e as CustomEvent<string>).detail
      setToast({ id: Date.now(), message })
    }
    window.addEventListener(TOAST_EVENT, handle)
    return () => window.removeEventListener(TOAST_EVENT, handle)
  }, [])

  useEffect(() => {
    if (!toast) return
    const t = setTimeout(() => setToast(null), 1800)
    return () => clearTimeout(t)
  }, [toast])

  if (!toast) return null

  return (
    <div className="pointer-events-none fixed bottom-6 left-1/2 z-50 -translate-x-1/2">
      <div className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm text-foreground shadow-lg">
        <Check className="h-4 w-4 text-[#4ade80]" />
        {toast.message}
      </div>
    </div>
  )
}
