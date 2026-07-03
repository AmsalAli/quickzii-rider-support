"use client"

import { useState } from "react"
import { Send } from "lucide-react"

interface ChatInputProps {
  onSend: (text: string) => void
  disabled?: boolean
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [value, setValue] = useState("")

  function submit() {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend(trimmed)
    setValue("")
  }

  return (
    <footer className="sticky bottom-0 z-20 border-t border-border bg-background/95 px-3 py-3 backdrop-blur">
      <div className="flex items-center gap-2">
        <input
          type="text"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.nativeEvent.isComposing && e.keyCode !== 229) {
              e.preventDefault()
              submit()
            }
          }}
          placeholder="Type a message..."
          aria-label="Type a message"
          className="h-11 flex-1 rounded-full border border-border bg-card px-4 text-sm text-foreground outline-none transition-colors duration-200 placeholder:text-muted-foreground focus:border-primary/60"
        />
        <button
          type="button"
          onClick={submit}
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-all duration-200 hover:bg-primary/90 active:scale-95 disabled:opacity-40"
        >
          <Send className="h-4.5 w-4.5" />
        </button>
      </div>
    </footer>
  )
}
