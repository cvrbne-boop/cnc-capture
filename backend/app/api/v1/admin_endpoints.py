from fastapi import APIRouter, Depends
from app.db.session import AsyncSessionLocal
from app.db.models import Job, Machine, User
from sqlalchemy import select

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

@router.get('/jobs/list')
async def list_jobs(db=Depends(get_db)):
    r = await db.execute(select(Job))
    rows = r.scalars().all()
    return [{"id":row.id,"name":row.name} for row in rows]

@router.get('/machines/list')
async def list_machines(db=Depends(get_db)):
    r = await db.execute(select(Machine))
    rows = r.scalars().all()
    return [{"id":row.id,"name":row.name} for row in rows]
