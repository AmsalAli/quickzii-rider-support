"use client"

import { useEffect, useRef, useState } from "react"
import {
  AI_PLACEHOLDER_RESPONSE,
  QUICK_REPLIES,
  mockRiderSession,
  type ChatMessage as ChatMessageType,
} from "@/lib/mock-rider-session"
import { ChatHeader } from "@/components/chat-header"
import { ChatMessage } from "@/components/chat-message"
import { TypingIndicator } from "@/components/typing-indicator"
import { QuickReplies } from "@/components/quick-replies"
import { ChatInput } from "@/components/chat-input"
import { NoBookingState } from "@/components/no-booking-state"

function nowTime() {
  return new Date().toLocaleTimeString([], { hour: "numeric", minute: "2-digit" })
}

let idCounter = 0
function nextId() {
  idCounter += 1
  return `m_${Date.now()}_${idCounter}`
}

export function RiderSupportChat() {
  const isDev = process.env.NODE_ENV !== "production"

  // Demo toggle: whether the rider has an active booking.
  const [hasBooking, setHasBooking] = useState(true)
  const activeBooking = hasBooking ? mockRiderSession.activeBooking : null

  const [contextExpanded, setContextExpanded] = useState(false)
  const [messages, setMessages] = useState<ChatMessageType[]>([])
  const [isTyping, setIsTyping] = useState(false)
  // Quick replies (full list) only show while this is the first interaction.
  const [showInitialReplies, setShowInitialReplies] = useState(true)

  const scrollRef = useRef<HTMLDivElement>(null)
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Seed the welcome message whenever we (re)enter the active-booking state.
  useEffect(() => {
    if (activeBooking) {
      setMessages([
        {
          id: nextId(),
          sender: "ai",
          text: `Hi ${mockRiderSession.rider.firstName}, how can I help you with booking ${activeBooking.id}?`,
          timestamp: nowTime(),
        },
      ])
      setShowInitialReplies(true)
      setIsTyping(false)
    } else {
      setMessages([])
      setIsTyping(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasBooking])

  // Auto-scroll to newest content.
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" })
  }, [messages, isTyping])

  useEffect(() => {
    return () => {
      if (typingTimer.current) clearTimeout(typingTimer.current)
    }
  }, [])

  async function handleSend(text: string, quickReplyIntent?: string) {
    setShowInitialReplies(false)
    setMessages((prev) => [
      ...prev,
      { id: nextId(), sender: "rider", text, timestamp: nowTime() },
    ])

    setIsTyping(true)
    try {
      const res = await fetch("/api/converse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rider_id: mockRiderSession.rider.id,
          conversation_id: `conv-${mockRiderSession.rider.id}`,
          booking_id: activeBooking?.id ?? null,
          text,
          quick_reply_intent: quickReplyIntent ?? null,
        }),
      })
      const data = await res.json()
      setIsTyping(false)
      setMessages((prev) => [
        ...prev,
        { id: nextId(), sender: "ai", text: data.reply_text ?? "[no reply]", timestamp: nowTime() },
      ])
    } catch {
      setIsTyping(false)
      setMessages((prev) => [
        ...prev,
        { id: nextId(), sender: "ai", text: "Sorry, I could not connect to support right now. Please try again.", timestamp: nowTime() },
      ])
    }
  }

  return (
    <div className="mx-auto flex h-dvh w-full max-w-[480px] flex-col bg-background">
      {isDev && (
        <div className="flex items-center justify-center gap-2 border-b border-border bg-muted px-4 py-1.5 text-[11px] text-muted-foreground">
          <span>Demo:</span>
          <button
            type="button"
            onClick={() => setHasBooking((v) => !v)}
            className="rounded-full border border-border px-2 py-0.5 font-medium text-foreground transition-colors duration-200 hover:border-primary/50"
          >
            {hasBooking ? "Switch to: No active booking" : "Switch to: Has active booking"}
          </button>
        </div>
      )}

      <ChatHeader
        rider={mockRiderSession.rider}
        activeBooking={activeBooking}
        expanded={contextExpanded}
        onToggle={() => setContextExpanded((v) => !v)}
      />

      {activeBooking ? (
        <>
          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
            {messages.map((message, index) => {
              const isLastAi =
                message.sender === "ai" && index === messages.length - 1 && !isTyping
              return (
                <div key={message.id} className="space-y-3">
                  <ChatMessage message={message} />
                  {/* Quick replies render under the triggering AI message */}
                  {isLastAi && showInitialReplies && (
                    <QuickReplies replies={QUICK_REPLIES} layout="stack" onSelect={handleSend} />
                  )}
                </div>
              )
            })}
            {isTyping && <TypingIndicator />}
          </div>

          <ChatInput onSend={handleSend} disabled={isTyping} />
        </>
      ) : (
        <NoBookingState />
      )}
    </div>
  )
}
