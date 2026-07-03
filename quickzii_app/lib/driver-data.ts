// Shape mirrors what a real Quickzii API response would return for a single
// driver. The same object is served from /api/drivers/[id] so the AI support
// agent and the dispatcher UI read from an identical structure.

export type DriverStatus = "available" | "busy" | "offline" | "invited"

export type TourStatus = "completed" | "cancelled" | "in_progress"

export interface DriverDetail {
  driver: {
    id: string
    firstName: string
    lastName: string
    email: string
    phone: string
    organization: string
    invitedAt: string
    status: DriverStatus
    muteState: "Muted" | "Unmuted"
    organizationChangeAllowed: boolean
    blocked: boolean
  }
  capabilities: {
    vehicle: "Bike" | "Car" | "Van" | "Scooter"
    serviceArea: string
    restrictedToServiceAreas: boolean
  }
  activeTour: {
    bookingId: string
    acceptedAt: string
    restaurantName: string
    dropoffAddress: string
  } | null
  recentTours: {
    dateTime: string
    bookingId: string
    restaurant: string
    status: TourStatus
  }[]
  lastKnownLocation: {
    lat: number
    lng: number
    timestamp: string
  }
}

const baseDriver: Omit<DriverDetail, "activeTour"> = {
  driver: {
    id: "drv_8f2a91",
    firstName: "Ahmed",
    lastName: "Alfaleh",
    email: "ahmed.alfaleh@example.com",
    phone: "+49 152 4821934",
    organization: "FPUD001",
    invitedAt: "2/15/2026",
    status: "busy",
    muteState: "Unmuted",
    organizationChangeAllowed: false,
    blocked: false,
  },
  capabilities: {
    vehicle: "Bike",
    serviceArea: "Wiesbaden",
    restrictedToServiceAreas: false,
  },
  recentTours: [
    {
      dateTime: "2/28/2026, 7:42 PM",
      bookingId: "BKG-20418",
      restaurant: "Saray Grill",
      status: "completed",
    },
    {
      dateTime: "2/28/2026, 6:15 PM",
      bookingId: "BKG-20392",
      restaurant: "Pasta della Nonna",
      status: "completed",
    },
    {
      dateTime: "2/27/2026, 9:03 PM",
      bookingId: "BKG-20355",
      restaurant: "Sushi Yama",
      status: "cancelled",
    },
    {
      dateTime: "2/27/2026, 1:28 PM",
      bookingId: "BKG-20311",
      restaurant: "Green Bowl",
      status: "completed",
    },
    {
      dateTime: "2/26/2026, 8:51 PM",
      bookingId: "BKG-20287",
      restaurant: "Burger Brüder",
      status: "completed",
    },
  ],
  lastKnownLocation: {
    lat: 50.0782,
    lng: 8.2398,
    timestamp: "2/28/2026, 7:58 PM",
  },
}

const activeTour: DriverDetail["activeTour"] = {
  bookingId: "BKG-20431",
  acceptedAt: "2/28/2026 at 8:04 PM",
  restaurantName: "Saray Grill",
  dropoffAddress: "Rheinstraße 12, 65185 Wiesbaden",
}

export const mockDriverDetail: DriverDetail = {
  ...baseDriver,
  activeTour,
}

export const mockDriverDetailNoTour: DriverDetail = {
  ...baseDriver,
  driver: { ...baseDriver.driver, status: "available" },
  activeTour: null,
}
