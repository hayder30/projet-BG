import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models  # noqa: F401  (register tables)
from .database import Base, SessionLocal, engine
from .routers import auth, categories, dashboard, products, stock, suppliers
from .seed import ensure_admin, seed_demo

log = logging.getLogger("uvicorn.error")


def init_db(retries: int = 15, delay: float = 2.0) -> None:
    """Create tables and seed data. Retries so the API can start before Postgres is ready."""
    for attempt in range(1, retries + 1):
        try:
            Base.metadata.create_all(engine)
            with SessionLocal() as db:
                ensure_admin(db)
                if os.getenv("SEED_DEMO_DATA", "true").lower() == "true":
                    seed_demo(db)
            return
        except Exception as exc:  # noqa: BLE001
            log.warning("Database not ready (%s/%s): %s", attempt, retries, exc)
            time.sleep(delay)
    raise RuntimeError("Could not connect to the database")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Brazilian Glow - Stock Management API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in (auth, categories, suppliers, products, stock, dashboard):
    app.include_router(r.router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
