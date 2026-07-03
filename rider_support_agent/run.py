"""Entry point for the rider support agent HTTP service.

  python run.py

Starts the agent on the configured host/port (default 127.0.0.1:8002).
The mock MotionTools service must be running separately on port 8001.

reload_dirs restricts hot-reload watching to source code only, so
running checkpoint scripts or seeding data does NOT trigger a reload.
"""
import uvicorn
from src.config.settings import settings


if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_dirs=["src"],
    )
