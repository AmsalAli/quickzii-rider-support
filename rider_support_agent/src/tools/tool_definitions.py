'''Tool definitions the agent exposes to Claude.

Each tool is a structured contract: Claude may only pass parameters
matching the JSON schema. This prevents hallucinated arguments and makes
every tool call auditable.

Design principle: tool names describe INTENT-LEVEL actions, not raw API
endpoints. e.g. 'share_customer_contact' not 'get_booking_customer_phone'.
This lets us change the underlying MotionTools calls without retraining
the agent's prompt.
'''

TOOLS = [
    {
        'name': 'lookup_booking',
        'description': (
            'Look up the current active booking for the rider in this '
            'conversation. Use this first, before any other tool, if you '
            'need booking details (restaurant, customer, addresses, status, '
            'delivery code). Returns the full booking record.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {},
            'required': [],
        },
    },
    {
        'name': 'share_customer_contact',
        'description': (
            'Share the customer name and phone number with the rider. Use '
            'ONLY when the rider explicitly asks how to reach the customer '
            'and you have confirmed that is their real intent (not a '
            'mis-tapped button). This is a LOW-risk autonomous action.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': 'One short sentence explaining why the rider needs the contact right now. Recorded for audit.',
                },
            },
            'required': ['reason'],
        },
    },
    {
        'name': 'start_wait_timer',
        'description': (
            'Start a wait-and-retry timer on the current booking. Use for '
            'ORDER_NOT_IN_RESTAURANT (5 minutes) or ORDER_NOT_READY '
            '(10 minutes) after the rider agrees to wait. If the rider '
            'later re-approaches about the same booking, check the timer '
            'state via lookup_booking; if the wait has expired, call '
            'redispatch_booking instead of starting another timer.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'reason_code': {
                    'type': 'string',
                    'enum': ['order_not_in_restaurant', 'order_not_ready'],
                    'description': 'Which flow triggered this wait.',
                },
            },
            'required': ['reason_code'],
        },
    },
    {
        'name': 'redispatch_booking',
        'description': (
            'Return the booking to the dispatch queue so a different rider '
            'can be assigned. Use when a wait timer has expired and the '
            'rider is still blocked, or when the rider explicitly declines '
            'to wait after being offered the option. This is a LOW-risk '
            'autonomous action for order_not_in_restaurant and '
            'order_not_ready intents.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'reason': {
                    'type': 'string',
                    'description': 'One short human-readable sentence explaining the redispatch. Recorded in audit log.',
                },
            },
            'required': ['reason'],
        },
    },
    {
        'name': 'mark_delivery_complete',
        'description': (
            'Mark the booking as delivered using a 4-digit confirmation '
            'code the rider provides. Use ONLY for the FORGOT_TO_FINISH '
            'flow, after the rider has typed the code. The mock service '
            'will verify the code against the booking record; if the code '
            'is wrong, the tool returns success=false and you must ask the '
            'rider to check the code and retry.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'delivery_code': {
                    'type': 'string',
                    'description': 'The 4-digit code the rider provided.',
                },
            },
            'required': ['delivery_code'],
        },
    },
    {
        'name': 'propose_human_action',
        'description': (
            'Queue a MEDIUM-risk case for human review. Use for '
            'CANNOT_DELIVER and VEHICLE_BREAKDOWN once you have gathered '
            'enough information to draft a proposed reply. The human '
            'reviewer will approve, edit, or reject your suggested reply. '
            'Do NOT act on the situation yourself; your reply is a proposal.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'proposed_reply': {
                    'type': 'string',
                    'description': 'The message you would send to the rider if approved.',
                },
                'reasoning': {
                    'type': 'string',
                    'description': 'One-sentence explanation for the human reviewer: what happened and why you propose this reply.',
                },
            },
            'required': ['proposed_reply', 'reasoning'],
        },
    },
    {
        'name': 'escalate_to_human',
        'description': (
            'Escalate a HIGH-risk case for full human handling. Use for '
            'ORDER_DAMAGED and CUSTOMER_REFUSED once you have gathered the '
            'rider\u0027s account of what happened. Do NOT propose a reply -- '
            'this is a full handoff. Send a brief holding message to the '
            'rider explaining a human agent will follow up.'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'summary': {
                    'type': 'string',
                    'description': 'One-paragraph summary of the situation for the human agent taking over.',
                },
                'rider_holding_message': {
                    'type': 'string',
                    'description': 'The short message shown to the rider while they wait for a human.',
                },
            },
            'required': ['summary', 'rider_holding_message'],
        },
    },
    {
        'name': 'send_reply_and_close',
        'description': (
            'Send a final reply to the rider and close the conversation. '
            'Use when the interaction is complete: after sharing contact, '
            'after the rider agrees to wait, after successful delivery '
            'completion, or when the rider indicates they no longer need '
            'help (e.g. \"never mind\", \"sorted\", \"thanks anyway\").'
        ),
        'input_schema': {
            'type': 'object',
            'properties': {
                'reply_text': {
                    'type': 'string',
                    'description': 'The final message sent to the rider.',
                },
                'outcome': {
                    'type': 'string',
                    'enum': ['resolved', 'rider_declined_help', 'no_action_needed'],
                    'description': 'Why the conversation is closing.',
                },
            },
            'required': ['reply_text', 'outcome'],
        },
    },
]
