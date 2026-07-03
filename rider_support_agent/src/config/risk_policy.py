'''Deterministic intent -> risk mapping.

Static lookup, not an LLM judgement. Rationale for Methodology chapter:
risk-tier assignment is a safety-critical decision that should be
auditable and reproducible, not subject to model variance between runs
on the same input.

Mapping rationale:
  LOW    -> agent can act autonomously; outcome is fully reversible or
            purely informational.
  MEDIUM -> agent can act but human should observe and approve/edit.
  HIGH   -> agent must not act; human takes over the conversation.
'''
from src.models.schemas import IntentLabel, RiskLevel


INTENT_RISK_MAP: dict[IntentLabel, RiskLevel] = {
    # LOW: autonomous
    IntentLabel.ORDER_NOT_IN_RESTAURANT: RiskLevel.LOW,   # wait or redispatch
    IntentLabel.ORDER_NOT_READY:         RiskLevel.LOW,   # wait or redispatch
    IntentLabel.CUSTOMER_UNREACHABLE:    RiskLevel.LOW,   # share contact
    IntentLabel.FORGOT_TO_FINISH:        RiskLevel.LOW,   # verify code, mark complete

    # MEDIUM: propose + human review
    IntentLabel.CANNOT_DELIVER:          RiskLevel.MEDIUM,
    IntentLabel.VEHICLE_BREAKDOWN:       RiskLevel.MEDIUM,

    # HIGH: escalate outright
    IntentLabel.ORDER_DAMAGED:           RiskLevel.HIGH,
    IntentLabel.CUSTOMER_REFUSED:        RiskLevel.HIGH,

    # OTHER: rider free-text; risk is decided after re-classification
    # If the agent cannot re-classify OTHER into a known intent, we fall
    # through to UNKNOWN which is HIGH by fail-safe policy.
    IntentLabel.OTHER:                   RiskLevel.MEDIUM,  # default to review

    # Fail-safe
    IntentLabel.UNKNOWN:                 RiskLevel.HIGH,
}


def get_risk_level(intent: IntentLabel) -> RiskLevel:
    return INTENT_RISK_MAP.get(intent, RiskLevel.HIGH)
