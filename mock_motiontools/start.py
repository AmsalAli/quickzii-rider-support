"""Production entry point for Render.

Reads PORT from environment (assigned by Render); falls back to 8001 locally.
Uvicorn runs without reload in production.
"""
import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
