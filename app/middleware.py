
import secrets

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import settings


PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
}


async def api_key_middleware(request: Request, call_next):
    """Validate the API key before accessing private endpoints."""

    if request.url.path not in PUBLIC_PATHS:
        expected_key = settings.API_KEY_SECRET
        provided_key = request.headers.get("X-Api-Key", "")

        if not expected_key or not secrets.compare_digest(
            provided_key, expected_key
        ):
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"},
            )

    return await call_next(request)
