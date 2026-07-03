import { Bot } from "lucide-react"
import type { ChatMessage as ChatMessageType } from "@/lib/mock-rider-session"

interface ChatMessageProps {
  message: ChatMessageType
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isAi = message.sender === "ai"

  return (
    <div className={`flex items-end gap-2 ${isAi ? "justify-start" : "justify-end"}`}>
      {isAi && (
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent">
          <Bot className="h-4 w-4 text-primary" />
        </div>
      )}

      <div className={`flex max-w-[78%] flex-col ${isAi ? "items-start" : "items-end"}`}>
        <div
          className={`rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
            isAi
              ? "rounded-bl-md bg-card text-card-foreground"
              : "rounded-br-md bg-primary text-primary-foreground"
          }`}
        >
          {message.text}
        </div>
        <span className="mt-1 px-1 text-[11px] text-muted-foreground">{message.timestamp}</span>
      </div>
    </div>
  )
}
