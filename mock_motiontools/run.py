'''Entry point: python run.py
Starts the mock MotionTools API on the configured host/port.
'''
import uvicorn
from app.config import settings


if __name__ == '__main__':
    uvicorn.run(
        'app.main:app',
        host=settings.host,
        port=settings.port,
        reload=True,
    )
