from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.db.session import AsyncSessionLocal
from app.db.models import Job, Drawing, JobCard
from app.services.qr import build_qr_payload
from app.services.pdfgen import generate_job_card_pdf
from fastapi.responses import StreamingResponse
from io import BytesIO
from sqlalchemy import select

router = APIRouter()

class JobIn(BaseModel):
    name: str
    customer: str = None

class DrawingIn(BaseModel):
    job_id: int
    drawing_number: str
    planned_time_per_piece: int = 0
    planned_pieces: int = 1

class JobCardIn(BaseModel):
    drawing_id: int
    card_number: str

async def get_db():
    async with AsyncSessionLocal() as s:
        yield s

@router.post("/jobs")
async def create_job(j: JobIn, db=Depends(get_db)):
    job = Job(name=j.name, customer=j.customer)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return {"id": job.id}

@router.post("/drawings")
async def create_drawing(d: DrawingIn, db=Depends(get_db)):
    dr = Drawing(job_id=d.job_id, drawing_number=d.drawing_number, planned_time_per_piece=d.planned_time_per_piece, planned_pieces=d.planned_pieces)
    db.add(dr)
    await db.commit()
    await db.refresh(dr)
    return {"id": dr.id}

@router.post("/jobcards")
async def create_jobcard(jc: JobCardIn, db=Depends(get_db)):
    jc_obj = JobCard(drawing_id=jc.drawing_id, card_number=jc.card_number)
    db.add(jc_obj)
    await db.commit()
    await db.refresh(jc_obj)
    # build and save qr payload
    qr = build_qr_payload(jc_obj.id)
    jc_obj.qr_payload = qr
    db.add(jc_obj)
    await db.commit()
    await db.refresh(jc_obj)
    return {"id": jc_obj.id, "qr_payload": jc_obj.qr_payload}

@router.get("/jobcard/{id}/pdf")
async def jobcard_pdf(id: int, db=Depends(get_db)):
    q = await db.execute(select(JobCard).where(JobCard.id==id))
    jc = q.scalar_one_or_none()
    if not jc:
        raise HTTPException(404, "Not found")
    # get drawing
    q2 = await db.execute(select(Drawing).where(Drawing.id==jc.drawing_id))
    dr = q2.scalar_one()
    content = generate_job_card_pdf(jc, dr)
    return StreamingResponse(BytesIO(content), media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=jobcard_{id}.pdf"})
