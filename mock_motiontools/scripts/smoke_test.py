'''Smoke test: hits every endpoint of the mock MotionTools API.

Requires the server to be running (python run.py in another terminal).
Prints one line per endpoint with status code + brief result.
'''
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests
from app.config import settings
from app.db.database import SessionLocal
from app.models.schemas import Booking, Driver

BASE = f'http://{settings.host}:{settings.port}'


def report(label: str, resp: requests.Response, preview_key: str | None = None):
    ok = 200 <= resp.status_code < 300
    marker = 'OK ' if ok else 'FAIL'
    line = f'[{marker}] {resp.status_code}  {label}'
    if ok and preview_key is not None:
        try:
            body = resp.json()
            if isinstance(body, list):
                line += f'  ({len(body)} items)'
            elif isinstance(body, dict) and preview_key in body:
                line += f'  ({preview_key}={body[preview_key]!r})'
        except Exception:
            pass
    print(line)


def main():
    print(f'Smoke-testing {BASE}')
    print('-' * 60)

    # Pick a real booking + driver from the DB so we don't hardcode IDs
    with SessionLocal() as s:
        b = s.query(Booking).filter(Booking.status == 'en_route').first()
        d = s.query(Driver).filter(Driver.status == 'busy').first()
        if not b or not d:
            # fall back to any
            b = s.query(Booking).first()
            d = s.query(Driver).first()
        booking_id = b.id
        booking_external = b.external_id
        booking_code = b.delivery_code
        driver_id = d.id

    report('GET /health', requests.get(f'{BASE}/health'), preview_key='status')
    report('GET /', requests.get(f'{BASE}/'), preview_key='service')

    report('GET /drivers?limit=5', requests.get(f'{BASE}/drivers?limit=5'), preview_key=None)
    report(f'GET /drivers/{{id}}', requests.get(f'{BASE}/drivers/{driver_id}'), preview_key='id')

    report('GET /bookings?limit=5', requests.get(f'{BASE}/bookings?limit=5'), preview_key=None)
    report(f'GET /bookings/{{id}}', requests.get(f'{BASE}/bookings/{booking_id}'), preview_key='id')
    report(f'GET /bookings/by-external/{booking_external}',
           requests.get(f'{BASE}/bookings/by-external/{booking_external}'),
           preview_key='id')

    report('GET /audit?limit=5', requests.get(f'{BASE}/audit?limit=5'), preview_key=None)
    report('GET /audit/summary', requests.get(f'{BASE}/audit/summary'), preview_key='total')

    # Action: mark-complete with wrong code (should fail 400)
    r = requests.post(f'{BASE}/actions/mark-complete',
                      json={'booking_id': booking_id, 'delivery_code': '0000'})
    report('POST /actions/mark-complete (wrong code, expect 400)', r, preview_key=None)

    # Action: mark-complete with correct code
    r = requests.post(f'{BASE}/actions/mark-complete',
                      json={'booking_id': booking_id, 'delivery_code': booking_code})
    report('POST /actions/mark-complete (correct code)', r, preview_key='message')

    print()
    print('Smoke test complete. If everything is [OK], the API is ready.')


if __name__ == '__main__':
    main()
