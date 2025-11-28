import dramatiq
from dramatiq.brokers.redis import RedisBroker
from app.services.notifier import send_telegram, send_email
from app.services.pdfgen import generate_job_card_pdf
from app.db.session import AsyncSessionLocal
from app.db.models import JobCard, Drawing
import asyncio

redis_broker = RedisBroker(url="redis://redis:6379")
dramatiq.set_broker(redis_broker)

@dramatiq.actor
def notify_telegram(text):
    import asyncio
    asyncio.run(send_telegram(text))

@dramatiq.actor
def notify_email(subject, body, to_email):
    import asyncio
    asyncio.run(send_email(subject, body, to_email))

@dramatiq.actor
def generate_and_store_pdf(jobcard_id):
    import asyncio
    from sqlalchemy.future import select
    async def _run():
        async with AsyncSessionLocal() as s:
            r = await s.execute(select(JobCard).where(JobCard.id==jobcard_id))
            jc = r.scalar_one_or_none()
            if not jc: return
            r2 = await s.execute(select(Drawing).where(Drawing.id==jc.drawing_id))
            dr = r2.scalar_one_or_none()
            pdf = generate_job_card_pdf(jc, dr)
            path = f"/tmp/jobcard_{jobcard_id}.pdf"
            with open(path, "wb") as f:
                f.write(pdf)
    asyncio.run(_run())
