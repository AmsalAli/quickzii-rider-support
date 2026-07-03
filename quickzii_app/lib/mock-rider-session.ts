export type MessageSender = "ai" | "rider"

export interface ChatMessage {
  id: string
  sender: MessageSender
  text: string
  timestamp: string
}

export interface ActiveBooking {
  id: string
  restaurant: string
  dropoffAddress: string
  status: string
}

export interface Rider {
  id: string
  firstName: string
  initial: string
}

export interface RiderSession {
  rider: Rider
  activeBooking: ActiveBooking | null
  messages: ChatMessage[]
}

export interface QuickReply {
  label: string
  intent: string
}

export const QUICK_REPLIES: QuickReply[] = [
  { label: "The order is not available in restaurant", intent: "order_not_in_restaurant" },
  { label: "Order is not ready yet", intent: "order_not_ready" },
  { label: "I can't reach out to the customer", intent: "customer_unreachable" },
  { label: "Order is damaged", intent: "order_damaged" },
  { label: "I can't do the delivery", intent: "cannot_deliver" },
  { label: "I forgot to finish the order on the app", intent: "forgot_to_finish" },
  { label: "Customer refused to accept the order", intent: "customer_refused" },
  { label: "Vehicle breakdown", intent: "vehicle_breakdown" },
  { label: "Other", intent: "other" },
]

export const AI_PLACEHOLDER_RESPONSE = "[AI response will be generated here]"

export const mockRiderSession: RiderSession = {
  rider: {
    id: "76c532ce-31af-4a32-8950-92809a189ccd",
    firstName: "Mirja",
    initial: "M",
  },
  activeBooking: {
    id: "4b46e142-8835-4c81-9c24-d0e0ff4eaa83",
    restaurant: "Sakura Ramen House",
    dropoffAddress: "48 Maple Street, Apt 12B, Brooklyn",
    status: "Picked up",
  },
  messages: [],
}
