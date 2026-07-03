'''Central configuration for the mock MotionTools service.

Loaded from .env at startup. Missing/malformed values fail loud rather than
silently, which is what you want for a service that seeds a database.
'''
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Seeding
    anonymize_drivers: bool = True
    num_bookings: int = 350

    # Server
    host: str = '127.0.0.1'
    port: int = 8001

    # Paths
    database_url: str = 'sqlite:///./data/motiontools.db'
    drivers_csv_path: str = 'data/all_riders_data.csv'
    tours_csv_path: str = 'data/all_tours.csv'


settings = Settings()
