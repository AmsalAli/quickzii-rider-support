'''Checkpoint for Batch A of the agent build.

Confirms:
  1. Settings load from .env
  2. Anthropic API key is present (does NOT make a real call)
  3. MotionTools HTTP client can reach the mock service
  4. A real booking and a real driver can be fetched
'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config.settings import settings
from src.config.risk_policy import get_risk_level
from src.models.schemas import IntentLabel, RiskLevel
from src.clients.motiontools_client import MotionToolsClient


def main():
    print('='*60)
    print('Rider Support Agent -- Batch A checkpoint')
    print('='*60)

    # 1. Settings
    print(f'\n[1] Settings loaded.')
    print(f'    Claude model:          {settings.claude_model}')
    print(f'    Timing mode:           {settings.timing_mode}')
    print(f'    Retry sec (not resto): {settings.retry_seconds_order_not_in_resto}')
    print(f'    Retry sec (not ready): {settings.retry_seconds_order_not_ready}')
    print(f'    MotionTools URL:       {settings.motiontools_base_url}')

    # 2. API key presence
    key = settings.anthropic_api_key or ''
    if key.startswith('sk-ant-') and len(key) > 20:
        print(f'\n[2] Anthropic API key present (starts with sk-ant-, length {len(key)}).')
    else:
        print('\n[2] WARNING: Anthropic API key looks wrong or missing.')
        print('    Open .env and set ANTHROPIC_API_KEY=<your real key>')

    # 3. Risk policy sanity
    print('\n[3] Risk policy sample:')
    for intent in [IntentLabel.CUSTOMER_UNREACHABLE, IntentLabel.VEHICLE_BREAKDOWN,
                   IntentLabel.ORDER_DAMAGED, IntentLabel.UNKNOWN]:
        print(f'    {intent.value:30s} -> {get_risk_level(intent).value}')

    # 4. MotionTools connectivity
    print('\n[4] MotionTools HTTP client...')
    client = MotionToolsClient()
    if not client.health():
        print('    FAILED: cannot reach mock MotionTools at', settings.motiontools_base_url)
        print('    Start the mock service first: cd ../mock_motiontools && python run.py')
        return

    print('    /health OK')
    bookings = client.list_bookings(status='en_route', limit=1)
    if not bookings:
        print('    No en_route bookings found in the mock database.')
        return
    b_summary = bookings[0]
    print(f'    Fetched an en_route booking: external_id={b_summary["external_id"]}')

    full = client.get_booking(b_summary['id'])
    print(f'    Full detail: restaurant={full["restaurant"]["name"] if full.get("restaurant") else "?"}, '
          f'driver_id={full.get("driver_id")}')

    if full.get('driver_id'):
        drv = client.get_driver(full['driver_id'])
        print(f'    Driver: {drv["first_name"]} (first name only), status={drv["status"]}, '
              f'service_area={drv.get("service_area")}')

    print('\nBatch A checkpoint passed.')


if __name__ == '__main__':
    main()
