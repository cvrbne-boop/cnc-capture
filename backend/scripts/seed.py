#!/usr/bin/env python3
"""Seed script — vloží jednoduché demo uživatele, stroje a ukázkovou zakázku."""
import asyncio
from app.db.session import AsyncSessionLocal, engine
from app.db.base import Base
from app.db.models import User, Machine, Job, Drawing, JobCard
from app.services.qr import build_qr_payload

async def run():
    async with engine.begin() as conn:
        # create tables if not exist
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSessionLocal() as s:
        # create demo user
        u = User(username='operator1', full_name='Operátor 1', email='op1@example.com')
        s.add(u)
        m = Machine(name='MAZAK-1')
        s.add(m)
        job = Job(name='Demo zakázka', customer='Acme')
        s.add(job)
        await s.flush()
        drawing = Drawing(job_id=job.id, drawing_number='D-100', planned_time_per_piece=60, planned_pieces=3)
        s.add(drawing)
        await s.flush()
        jc = JobCard(drawing_id=drawing.id, card_number='JC-100')
        s.add(jc)
        await s.flush()
        # build QR payload
        jc.qr_payload = build_qr_payload(jc.id)
        await s.commit()
        print('Seed data created: user id', u.id, 'machine id', m.id, 'jobcard id', jc.id)

if __name__ == '__main__':
    asyncio.run(run())
