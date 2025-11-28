from fastapi import FastAPI
from app.api.v1 import scan, jobs, auth
from app.db.base import Base
from app.db.session import engine
import asyncio

app = FastAPI(title="CNC Capture API")

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1", tags=["jobs"])
app.include_router(scan.router, prefix="/api/v1", tags=["scan"])

@app.on_event("startup")
async def startup():
    # create tables automatically (dev); in prod use alembic
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
