from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.session import AsyncSessionLocal
from app.services.qr import verify_qr_payload
from app.db.models import Session as DBSession, SessionStatus, JobCard, Drawing
from sqlalchemy import select, func
import datetime
from app.services import notifier
import asyncio

router = APIRouter()

class ScanIn(BaseModel):
    operator_id: int
    machine_id: int
    qr_payload: str

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

@router.post("/scan")
async def scan(payload: ScanIn, db=Depends(get_db)):
    vf = verify_qr_payload(payload.qr_payload)
    if not vf:
        raise HTTPException(400, "Invalid QR payload")
    job_card_id = vf["job_card_id"]
    now = datetime.datetime.utcnow()

    q = select(DBSession).where(
        DBSession.job_card_id==job_card_id,
        DBSession.machine_id==payload.machine_id,
        DBSession.operator_id==payload.operator_id,
        DBSession.status==SessionStatus.started
    ).order_by(DBSession.start_ts.desc()).limit(1)
    res = await db.execute(q)
    existing = res.scalar_one_or_none()
    if existing is None:
        # START
        new = DBSession(job_card_id=job_card_id, operator_id=payload.operator_id,
                        machine_id=payload.machine_id, start_ts=now, status=SessionStatus.started)
        db.add(new)
        await db.commit()
        await db.refresh(new)
        return {"action": "started", "session_id": new.id, "start_ts": new.start_ts.isoformat()}
    else:
        # STOP
        existing.stop_ts = now
        existing.duration_seconds = int((existing.stop_ts - existing.start_ts).total_seconds())
        existing.status = SessionStatus.stopped
        db.add(existing)
        await db.commit()
        # check if jobcard done
        q2 = select(Drawing.planned_pieces).join(JobCard, JobCard.drawing_id==Drawing.id).where(JobCard.id==job_card_id)
        r2 = await db.execute(q2)
        planned = r2.scalar_one_or_none() or 1
        q3 = select(func.count(DBSession.id)).where(DBSession.job_card_id==job_card_id, DBSession.status==SessionStatus.stopped)
        r3 = await db.execute(q3)
        done = r3.scalar_one()
        if done >= planned:
            # fire off notification async
            asyncio.create_task(notifier.send_telegram(f"JobCard {job_card_id} completed: {done}/{planned}"))
        return {"action": "stopped", "session_id": existing.id, "duration_seconds": existing.duration_seconds, "done": done, "planned": planned}
