'''Seeds the mock MotionTools database from the real CSV exports.

By default, PII (names/emails/phones) is anonymized via Faker while
preserving structure (IDs, service areas, addresses, distributions).
Set ANONYMIZE_DRIVERS=false in .env only if you accept GDPR responsibility.

Usage:
    python scripts/seed.py
'''
import csv
import random
import string
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Ensure project root is on sys.path so we can import app.*
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from faker import Faker
from app.config import settings
from app.db.database import engine, SessionLocal, Base
from app.models.schemas import (
    Driver, Restaurant, Booking, AuditLogEntry,
    BOOKING_STATUSES, VEHICLE_TYPES, DRIVER_STATUSES,
)

fake = Faker('de_DE')  # German locale matches real operating area
random.seed(42)
Faker.seed(42)


# ---------- Status distribution (mirrors real export proportions) ----------
# From your real tours CSV: mostly to_be_dispatched + en_route, some pickable,
# few paid, very few cancelled. Adjust here if you want different mix.
STATUS_WEIGHTS = {
    'to_be_dispatched': 0.25,
    'pickable':         0.15,
    'en_route':         0.30,
    'paid':             0.25,
    'cancelled':        0.05,
}


def four_digit_code() -> str:
    return ''.join(random.choices(string.digits, k=4))


def short_external_id() -> str:
    '''Match MotionTools 'FFFXTC' style: 6 uppercase alphanumeric.'''
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def extract_city_from_address(address: str) -> str:
    '''Real addresses are like 'Stader Straße 256, 21075 Hamburg'.
    Last whitespace-separated token is the city name.'''
    if not address or ',' not in address:
        return 'Unknown'
    tail = address.rsplit(',', 1)[1].strip()
    parts = tail.split(' ', 1)
    if len(parts) == 2:
        return parts[1].strip()
    return tail


# ---------- Driver loading (with anonymization) ----------

def load_drivers(session, anonymize: bool) -> list[Driver]:
    csv_path = Path(settings.drivers_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f'Drivers CSV not found at {csv_path}. Copy your export into data/all_riders_data.csv'
        )

    drivers = []
    seen_emails = set()

    with open(csv_path, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            driver_id = row.get('id') or str(uuid.uuid4())

            if anonymize:
                first = fake.first_name()
                last = fake.last_name()
                email = f'{first.lower()}.{last.lower()}.{driver_id[:6]}@example.local'
                phone = fake.phone_number()
            else:
                first = row['first_name']
                last = row['last_name']
                email = row['email']
                phone = row['phone_number']

            if email in seen_emails:
                continue
            seen_emails.add(email)

            drivers.append(Driver(
                id=driver_id,
                email=email,
                first_name=first,
                last_name=last,
                phone_number=phone,
                status=random.choice(DRIVER_STATUSES),
                vehicle_type=random.choice(VEHICLE_TYPES),
                service_area=None,  # filled below when we know cities
                organization=random.choice(['FPUD001', 'FPAN001', 'FPBM001']),
                blocked=False,
            ))

    session.add_all(drivers)
    session.flush()
    return drivers


# ---------- Restaurant + address extraction from real tours CSV ----------

def load_restaurants_and_addresses(session) -> tuple[list[Restaurant], list[tuple[str, str, str]]]:
    '''Extract distinct pickup addresses from the tours CSV to build a
    plausible restaurant list, and return (pickup, dropoff, city) triples
    for booking generation.'''
    csv_path = Path(settings.tours_csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(
            f'Tours CSV not found at {csv_path}. Copy your export into data/all_tours.csv'
        )

    seen_pickups: dict[str, tuple[str, str]] = {}  # pickup_addr -> (city, name)
    address_triples: list[tuple[str, str, str]] = []

    restaurant_name_pool = [
        'Pizza Hut', 'Kebap Haus', 'Bistro Milano', 'Sushi Express',
        'Burger Palast', 'Doner Star', 'Napoli Pizzeria', 'Thai Garden',
        'Bella Italia', 'Curry King', 'Cafe Nord', 'Grill Master',
    ]

    with open(csv_path, encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            pickup = (row.get('stop_1_address') or '').strip()
            dropoff = (row.get('stop_2_address') or '').strip()
            if not pickup or not dropoff:
                continue
            city = extract_city_from_address(pickup)
            if pickup not in seen_pickups:
                name = f'{random.choice(restaurant_name_pool)} {city}'
                seen_pickups[pickup] = (city, name)
            address_triples.append((pickup, dropoff, city))

    restaurants = [
        Restaurant(
            id=str(uuid.uuid4()),
            name=name,
            address=addr,
            city=city,
        )
        for addr, (city, name) in seen_pickups.items()
    ]
    session.add_all(restaurants)
    session.flush()

    # Return a lookup so we can attach restaurant_id to each booking
    restaurant_by_address = {r.address: r for r in restaurants}
    triples_with_restaurant = [
        (restaurant_by_address[p].id, p, d, c) for (p, d, c) in address_triples
        if p in restaurant_by_address
    ]
    return restaurants, triples_with_restaurant


# ---------- Booking generation ----------

def weighted_status() -> str:
    r = random.random()
    cumulative = 0.0
    for status, weight in STATUS_WEIGHTS.items():
        cumulative += weight
        if r < cumulative:
            return status
    return 'to_be_dispatched'


def generate_bookings(session, drivers: list[Driver], address_data, num_bookings: int):
    if not address_data:
        raise RuntimeError('No usable pickup/dropoff addresses extracted from tours CSV.')

    # Also assign service_area to each driver based on cities present
    cities = list({c for (_, _, _, c) in address_data})
    for d in drivers:
        d.service_area = random.choice(cities) if cities else None

    now = datetime.now(timezone.utc)
    bookings_created = []

    for _ in range(num_bookings):
        restaurant_id, pickup, dropoff, city = random.choice(address_data)
        status = weighted_status()

        # Only en_route bookings have an assigned driver; pickable are visible-but-unassigned
        assigned_driver = None
        if status == 'en_route':
            eligible = [d for d in drivers if d.service_area == city] or drivers
            assigned_driver = random.choice(eligible)

        created_at = now - timedelta(minutes=random.randint(5, 60 * 24))
        scheduled_at = created_at + timedelta(minutes=random.randint(10, 60))
        completed_at = scheduled_at + timedelta(minutes=random.randint(20, 60)) if status == 'paid' else None

        b = Booking(
            id=str(uuid.uuid4()),
            external_id=short_external_id(),
            status=status,
            customer_id=str(uuid.uuid4()),
            customer_first_name=fake.first_name(),
            customer_last_name=fake.last_name(),
            customer_phone=fake.phone_number(),
            restaurant_id=restaurant_id,
            pickup_address=pickup,
            dropoff_address=dropoff,
            driver_id=assigned_driver.id if assigned_driver else None,
            created_at=created_at,
            scheduled_at=scheduled_at,
            completed_at=completed_at,
            delivery_code=four_digit_code(),
            retry_status='none',
            retry_count=0,
            vehicle_type=random.choice(VEHICLE_TYPES),
        )
        bookings_created.append(b)

    session.add_all(bookings_created)
    session.flush()

    # Bump assigned drivers to 'busy'
    for b in bookings_created:
        if b.driver_id and b.status == 'en_route':
            drv = session.get(Driver, b.driver_id)
            if drv:
                drv.status = 'busy'

    return bookings_created


# ---------- Main ----------

def main():
    print('='*60)
    print('Mock MotionTools database seeder')
    print('='*60)
    print(f'Anonymize drivers: {settings.anonymize_drivers}')
    print(f'Target bookings:   {settings.num_bookings}')
    print()

    if not settings.anonymize_drivers:
        print('WARNING: ANONYMIZE_DRIVERS is false. Real PII will be loaded.')
        print('         This is a GDPR-relevant operation. Continuing in 3 seconds...')
        import time; time.sleep(3)

    # Reset DB
    print('Dropping and recreating tables...')
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as session:
        print('Loading drivers...')
        drivers = load_drivers(session, anonymize=settings.anonymize_drivers)
        print(f'  loaded {len(drivers)} drivers')

        print('Extracting restaurants + addresses from tours CSV...')
        restaurants, address_data = load_restaurants_and_addresses(session)
        print(f'  extracted {len(restaurants)} restaurants and {len(address_data)} address pairs')

        print(f'Generating {settings.num_bookings} bookings...')
        bookings = generate_bookings(session, drivers, address_data, settings.num_bookings)
        print(f'  created {len(bookings)} bookings')

        # Seed one audit log entry per booking (creation event)
        print('Writing initial audit log entries...')
        for b in bookings:
            session.add(AuditLogEntry(
                id=str(uuid.uuid4()),
                timestamp=b.created_at,
                booking_id=b.id,
                actor='SYSTEM',
                event_type='booking_created',
                description=f'Booking {b.external_id} created with status {b.status}',
                payload_json={'external_id': b.external_id, 'initial_status': b.status},
            ))

        session.commit()

    print()
    print('Seed complete.')
    print(f'Database: {settings.database_url}')


if __name__ == '__main__':
    main()
