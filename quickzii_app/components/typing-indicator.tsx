import { Bot } from "lucide-react"

export function TypingIndicator() {
  return (
    <div className="flex items-end gap-2">
      <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent">
        <Bot className="h-4 w-4 text-primary" />
      </div>
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md bg-card px-4 py-3.5">
        <span
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
          style={{ animation: "typing-bounce 1.2s infinite", animationDelay: "0ms" }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
          style={{ animation: "typing-bounce 1.2s infinite", animationDelay: "200ms" }}
        />
        <span
          className="h-1.5 w-1.5 rounded-full bg-muted-foreground"
          style={{ animation: "typing-bounce 1.2s infinite", animationDelay: "400ms" }}
        />
        <span className="sr-only">AI is typing</span>
      </div>
    </div>
  )
}
