'''Quick sanity check on the seeded database.

Run after scripts/seed.py to confirm counts, status distribution,
and sample records. Does NOT print PII beyond first-name-only.
'''
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.database import SessionLocal
from app.models.schemas import Driver, Restaurant, Booking, AuditLogEntry


def main():
    with SessionLocal() as s:
        n_drivers = s.query(Driver).count()
        n_restaurants = s.query(Restaurant).count()
        n_bookings = s.query(Booking).count()
        n_audit = s.query(AuditLogEntry).count()

        print(f'Drivers:     {n_drivers}')
        print(f'Restaurants: {n_restaurants}')
        print(f'Bookings:    {n_bookings}')
        print(f'Audit log:   {n_audit}')
        print()

        status_counts = Counter(b.status for b in s.query(Booking).all())
        print('Booking status distribution:')
        for status, count in status_counts.most_common():
            pct = 100 * count / n_bookings if n_bookings else 0
            print(f'  {status:20s} {count:5d}  ({pct:.1f}%)')
        print()

        vehicle_counts = Counter(d.vehicle_type for d in s.query(Driver).all())
        print('Driver vehicle mix:', dict(vehicle_counts))

        area_counts = Counter(d.service_area for d in s.query(Driver).all() if d.service_area)
        print(f'Distinct service areas: {len(area_counts)}')
        print(f'Top 5 areas: {area_counts.most_common(5)}')
        print()

        sample = s.query(Booking).filter(Booking.status == 'en_route').first()
        if sample:
            print('Sample en_route booking:')
            print(f'  external_id:    {sample.external_id}')
            print(f'  customer:       {sample.customer_first_name} (first name only)')
            print(f'  pickup:         {sample.pickup_address}')
            print(f'  dropoff:        {sample.dropoff_address}')
            print(f'  delivery_code:  {sample.delivery_code}')
            print(f'  driver_id:      {sample.driver_id}')


if __name__ == '__main__':
    main()
