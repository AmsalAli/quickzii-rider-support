// Shape mirrors what the real backend API will return for a single booking.
// The detail page reads exclusively from this object.

export type BookingStatus =
  | "in_progress"
  | "completed"
  | "pending"
  | "cancelled"
  | "scheduled"
  | "redispatched"

export type TimelineActor = "SYSTEM" | "AI_AGENT" | "HUMAN_AGENT" | "RIDER"

export interface TimelineEvent {
  timestamp: string
  actor: TimelineActor
  description: string
}

export interface BookingDetail {
  booking: {
    id: string
    status: BookingStatus
    createdAt: string
    estimatedDelivery: string
    deliveryCode: string
    retryStatus: string
    retryCount: number
  }
  pickup: {
    restaurantName: string
    restaurantId: string
    address: string
  }
  dropoff: {
    customerAddress: string
    distanceKm: number
    estimatedMin: number
  }
  customer: {
    name: string
    phone: string
  }
  rider: {
    id: string
    name: string
    vehicle: string
    serviceArea: string
  }
  timeline: TimelineEvent[]
}

export const mockBookingDetail: BookingDetail = {
  booking: {
    id: "BK-7392",
    status: "in_progress",
    createdAt: "30 Jun 2026, 14:32",
    estimatedDelivery: "30 Jun 2026, 15:15",
    deliveryCode: "7392",
    retryStatus: "None",
    retryCount: 0,
  },
  pickup: {
    restaurantName: "Pizza Hut Wiesbaden",
    restaurantId: "RES-2104",
    address: "Hauptstrasse 12, 65183 Wiesbaden",
  },
  dropoff: {
    customerAddress: "Bahnhofstrasse 45, 65185 Wiesbaden",
    distanceKm: 3.19,
    estimatedMin: 17,
  },
  customer: {
    name: "Jan Müller",
    phone: "+49 152 1234567",
  },
  rider: {
    id: "RIDER-4821",
    name: "Ahmed Alfaleh",
    vehicle: "Bike",
    serviceArea: "Wiesbaden",
  },
  timeline: [
    {
      timestamp: "14:52",
      actor: "AI_AGENT",
      description: "Wait period expired, rider did not re-approach, conversation closed",
    },
    { timestamp: "14:42", actor: "RIDER", description: "Agreed to wait" },
    { timestamp: "14:41", actor: "AI_AGENT", description: "Suggested 10-minute wait" },
    {
      timestamp: "14:41",
      actor: "RIDER",
      description: 'Pressed quick reply: "Order is not ready yet"',
    },
    {
      timestamp: "14:35",
      actor: "SYSTEM",
      description: "Dispatched to rider Ahmed Alfaleh",
    },
    { timestamp: "14:32", actor: "SYSTEM", description: "Booking created" },
  ],
}

export const STATUS_LABELS: Record<BookingStatus, string> = {
  in_progress: "In Progress",
  completed: "Completed",
  pending: "Pending",
  cancelled: "Cancelled",
  scheduled: "Scheduled",
  redispatched: "Redispatched",
}
