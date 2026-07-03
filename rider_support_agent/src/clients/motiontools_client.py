'''HTTP client for the mock MotionTools API.

The agent calls this to look up bookings, look up drivers, and perform
operational actions (redispatch, mark-complete).

When the real MotionTools API is granted access, replacing this file with
a client pointed at the real endpoint is the only code change required
in the agent codebase.
'''
from typing import Any, Optional
import httpx

from src.config.settings import settings


class MotionToolsHTTPError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f'MotionTools API error {status_code}: {detail}')


class MotionToolsClient:
    def __init__(self, base_url: Optional[str] = None, timeout: float = 10.0):
        self.base_url = (base_url or settings.motiontools_base_url).rstrip('/')
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout)

    # ---------- Bookings ----------

    def get_booking(self, booking_id: str) -> dict[str, Any]:
        r = self._client.get(f'/bookings/{booking_id}')
        self._raise_for_status(r)
        return r.json()

    def get_booking_by_external(self, external_id: str) -> dict[str, Any]:
        r = self._client.get(f'/bookings/by-external/{external_id}')
        self._raise_for_status(r)
        return r.json()

    def list_bookings(self, status: Optional[str] = None, limit: int = 50) -> list[dict[str, Any]]:
        params = {'limit': limit}
        if status:
            params['status'] = status
        r = self._client.get('/bookings', params=params)
        self._raise_for_status(r)
        return r.json()

    # ---------- Drivers ----------

    def get_driver(self, driver_id: str) -> dict[str, Any]:
        r = self._client.get(f'/drivers/{driver_id}')
        self._raise_for_status(r)
        return r.json()

    def get_driver_active_booking(self, driver_id: str) -> Optional[dict[str, Any]]:
        '''Convenience: returns the active booking dict for a driver, or None.'''
        d = self.get_driver(driver_id)
        return d.get('active_booking_summary')

    # ---------- Actions ----------

    def redispatch_booking(self, booking_id: str, reason: str) -> dict[str, Any]:
        r = self._client.post(
            '/actions/redispatch',
            json={'booking_id': booking_id, 'reason': reason},
        )
        self._raise_for_status(r)
        return r.json()

    def mark_complete(self, booking_id: str, delivery_code: str,
                      actor: str = 'AI_AGENT') -> dict[str, Any]:
        r = self._client.post(
            '/actions/mark-complete',
            json={
                'booking_id': booking_id,
                'delivery_code': delivery_code,
                'actor': actor,
            },
        )
        # mark-complete returns 400 for wrong code -- we want to surface that
        # as a structured result, not an exception
        if r.status_code == 400:
            return {'success': False, 'message': r.json().get('detail', 'Bad request')}
        self._raise_for_status(r)
        return r.json()

    # ---------- Health ----------

    def health(self) -> bool:
        try:
            r = self._client.get('/health')
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    # ---------- Internal ----------

    def _raise_for_status(self, r: httpx.Response) -> None:
        if r.status_code >= 400:
            try:
                detail = r.json().get('detail', r.text)
            except Exception:
                detail = r.text
            raise MotionToolsHTTPError(r.status_code, str(detail))

    def close(self):
        self._client.close()


    # ---------- Wait timers (added for agent retry state machine) ----------

    def start_wait(self, booking_id: str, reason_code: str, wait_seconds: int) -> dict:
        r = self._client.post(
            "/actions/start-wait",
            json={
                "booking_id": booking_id,
                "reason_code": reason_code,
                "wait_seconds": wait_seconds,
            },
        )
        self._raise_for_status(r)
        return r.json()

    def check_wait_expired(self, booking_id: str, wait_seconds: int) -> dict:
        r = self._client.post(
            "/actions/check-wait-expired",
            json={"booking_id": booking_id, "wait_seconds": wait_seconds},
        )
        self._raise_for_status(r)
        return r.json()
