import time
import logging
import sys
from app import models 
from app.middleware import api_key_middleware
from fastapi import FastAPI, Request
from app.config import settings
from app.database import engine, Base
from app.routers import inventory

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)

app = FastAPI(title=settings.APP_NAME, version="1.0.0")
app.middleware("http")(api_key_middleware)


@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logging.info("Application started and database initialized.")


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time_ms = int((time.perf_counter() - start_time) * 1000)
    response.headers["X-Response-Time-Ms"] = str(process_time_ms)
    return response

app.include_router(inventory.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
