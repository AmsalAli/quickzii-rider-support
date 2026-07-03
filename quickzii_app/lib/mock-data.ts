export type RiskTier = "LOW" | "MEDIUM" | "HIGH"

export type AuditOutcome =
  | "Auto-resolved"
  | "Human approved (as-is)"
  | "Human edited reply"
  | "Human rejected"
  | "Escalated, human handled"

export interface MediumRiskCase {
  id: string
  riderName: string
  riderId: string
  bookingId: string
  intent: string
  riskTier: RiskTier
  waitingSince: string
  riderMessages: string[]
  agentReasoning: string
  proposedReply: string
}

export interface HighRiskCase {
  id: string
  riderName: string
  riderId: string
  bookingId: string
  intent: string
  riskTier: RiskTier
  waitingSince: string
  riderMessages: string[]
  agentReasoning: string
  bookingContext: string
}

export interface AuditEntry {
  id: string
  timestamp: string
  bookingId: string
  riderName: string
  intent: string
  riskTier: RiskTier
  outcome: AuditOutcome
  processingTime: string
}

export interface DashboardState {
  stats: {
    pending: number
    inReview: number
    resolvedToday: number
  }
  mediumRiskQueue: MediumRiskCase[]
  highRiskQueue: HighRiskCase[]
  auditLog: AuditEntry[]
}

export const mockDashboardState: DashboardState = {
  stats: {
    pending: 12,
    inReview: 3,
    resolvedToday: 47,
  },
  mediumRiskQueue: [
    {
      id: "mr-1",
      riderName: "Ahmed Alfaleh",
      riderId: "RDR-2041",
      bookingId: "BK-7388",
      intent: "Vehicle Breakdown",
      riskTier: "MEDIUM",
      waitingSince: "Waiting 2m 14s",
      riderMessages: [
        "My bike chain just snapped, I can't pedal at all.",
        "I'm stuck on Schillerstrasse, what should I do?",
      ],
      agentReasoning:
        "Rider reports bike chain broken. Suggesting they attempt nearby repair shop and continue delivery. Distance to drop-off: 1.2 km.",
      proposedReply:
        "Hi Ahmed, sorry to hear about the breakdown. There's a bike repair shop 200m from you at Schillerstrasse 14 — could you try a quick fix and continue? The drop-off is just 1.2 km away. Let me know if that won't work.",
    },
    {
      id: "mr-2",
      riderName: "Mohammad Demyati",
      riderId: "RDR-1987",
      bookingId: "BK-7378",
      intent: "Can't Do Delivery",
      riskTier: "MEDIUM",
      waitingSince: "Waiting 1m 48s",
      riderMessages: [
        "I don't think I can take this one, the address is too far out.",
        "It's 9km and I'm already running late on another order.",
      ],
      agentReasoning:
        "Rider unable to complete due to distance and existing load. Suggesting reassignment to a closer rider while keeping the customer informed.",
      proposedReply:
        "No problem, Mohammad. I'll reassign this order to a rider closer to the drop-off so you can focus on your current delivery. You won't be penalized for this. Thanks for letting us know early.",
    },
    {
      id: "mr-3",
      riderName: "Musa Al Ali",
      riderId: "RDR-2210",
      bookingId: "BK-7365",
      intent: "Schedule conflict",
      riskTier: "MEDIUM",
      waitingSince: "Waiting 3m 05s",
      riderMessages: [
        "My shift was supposed to end 20 minutes ago.",
        "Can someone else finish this delivery? I have to leave.",
      ],
      agentReasoning:
        "Rider flagged shift overrun (classified from 'Other'). Order is picked up and 0.8 km from drop-off. Suggesting rider completes final leg with a small bonus, with reassignment as fallback.",
      proposedReply:
        "Hi Musa, I see your shift just ended — sorry about the overrun. You're only 0.8 km from the drop-off. Could you complete this last leg? We'll add a late-completion bonus to your payout. If not, reply here and I'll reassign it.",
    },
  ],
  highRiskQueue: [
    {
      id: "hr-1",
      riderName: "Karim Radwan",
      riderId: "RDR-1820",
      bookingId: "BK-7381",
      intent: "Order Damaged",
      riskTier: "HIGH",
      waitingSince: "Waiting 4m 02s",
      riderMessages: [
        "The bag fell off my rack and the food is completely ruined.",
        "Drinks spilled everywhere, I don't think this is deliverable.",
      ],
      agentReasoning:
        "Rider reports order damaged in transit. AI cannot determine appropriate compensation or refund — requires human judgement.",
      bookingContext:
        "Restaurant: Habibi Grill · Customer: L. Fischer · Order value: €34.50",
    },
    {
      id: "hr-2",
      riderName: "Qamar Rehman",
      riderId: "RDR-2098",
      bookingId: "BK-7370",
      intent: "Customer Refused Order",
      riskTier: "HIGH",
      waitingSince: "Waiting 5m 21s",
      riderMessages: [
        "Customer says they never ordered this and won't take it.",
        "They're refusing at the door, what do I do with the food?",
      ],
      agentReasoning:
        "Customer refused delivery at door, disputes the order. AI cannot resolve a billing/fraud dispute or authorize disposal — requires human handling.",
      bookingContext:
        "Restaurant: Tokyo Bowl · Customer: M. Schneider · Order value: €52.20",
    },
  ],
  auditLog: [
    {
      id: "al-1",
      timestamp: "14:32",
      bookingId: "BK-7392",
      riderName: "Ahmed Alfaleh",
      intent: "Order not ready",
      riskTier: "LOW",
      outcome: "Auto-resolved",
      processingTime: "1.4s",
    },
    {
      id: "al-2",
      timestamp: "14:31",
      bookingId: "BK-7388",
      riderName: "Wissam Karimeh",
      intent: "Vehicle breakdown",
      riskTier: "MEDIUM",
      outcome: "Human approved (as-is)",
      processingTime: "2m 14s",
    },
    {
      id: "al-3",
      timestamp: "14:28",
      bookingId: "BK-7385",
      riderName: "Inayat Ullah",
      intent: "Customer unreachable",
      riskTier: "LOW",
      outcome: "Auto-resolved",
      processingTime: "0.9s",
    },
    {
      id: "al-4",
      timestamp: "14:25",
      bookingId: "BK-7381",
      riderName: "Karim Radwan",
      intent: "Order damaged",
      riskTier: "HIGH",
      outcome: "Escalated, human handled",
      processingTime: "4m 02s",
    },
    {
      id: "al-5",
      timestamp: "14:22",
      bookingId: "BK-7378",
      riderName: "Mohammad Demyati",
      intent: "Can't do delivery",
      riskTier: "MEDIUM",
      outcome: "Human edited reply",
      processingTime: "1m 48s",
    },
    {
      id: "al-6",
      timestamp: "14:20",
      bookingId: "BK-7375",
      riderName: "Maher Tanoura",
      intent: "Forgot to finish",
      riskTier: "LOW",
      outcome: "Auto-resolved",
      processingTime: "1.1s",
    },
    {
      id: "al-7",
      timestamp: "14:18",
      bookingId: "BK-7370",
      riderName: "Qamar Rehman",
      intent: "Customer refused",
      riskTier: "HIGH",
      outcome: "Escalated, human handled",
      processingTime: "5m 21s",
    },
    {
      id: "al-8",
      timestamp: "14:15",
      bookingId: "BK-7368",
      riderName: "Anas Darkhabani",
      intent: "Other → Booking question",
      riskTier: "LOW",
      outcome: "Auto-resolved",
      processingTime: "1.6s",
    },
    {
      id: "al-9",
      timestamp: "14:12",
      bookingId: "BK-7365",
      riderName: "Musa Al Ali",
      intent: "Vehicle breakdown",
      riskTier: "MEDIUM",
      outcome: "Human rejected",
      processingTime: "3m 05s",
    },
  ],
}

export const INTENT_OPTIONS = [
  "All intents",
  "Order not in restaurant",
  "Order not ready",
  "Customer unreachable",
  "Vehicle breakdown",
  "Can't do delivery",
  "Order damaged",
  "Customer refused",
  "Forgot to finish",
  "Other → Booking question",
]

export const OUTCOME_OPTIONS = [
  "All",
  "Auto-resolved",
  "Human approved",
  "Human edited",
  "Human rejected",
  "Escalated",
]

export const RISK_OPTIONS = ["All", "Low", "Medium", "High"]
