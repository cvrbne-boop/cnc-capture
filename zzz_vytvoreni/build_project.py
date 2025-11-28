#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_project.py
Generuje kompletní projekt 'cnc-capture' (backend, worker, frontend, docker-compose, tests, CI)
a vytvoří archiv cnc-capture.zip
"""

import os
import shutil
import zipfile
from pathlib import Path
from textwrap import dedent

ROOT = Path.cwd() / "cnc-capture"

FILES = {
    # top-level
    "docker-compose.yml": dedent("""\
        version: "3.8"
        services:
          db:
            image: postgres:15
            environment:
              POSTGRES_USER: cnc
              POSTGRES_PASSWORD: cncpass
              POSTGRES_DB: cnc
            volumes:
              - db_data:/var/lib/postgresql/data
            ports:
              - "5432:5432"

          redis:
            image: redis:7
            ports:
              - "6379:6379"

          backend:
            build: ./backend
            env_file: .env
            depends_on:
              - db
              - redis
            ports:
              - "8000:8000"
            volumes:
              - ./backend/app:/app/app
            command: ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--reload"]

          worker:
            build:
              context: ./worker
            env_file: .env
            depends_on:
              - redis
              - db
            volumes:
              - ./backend/app:/app/app

          frontend:
            build: ./frontend
            ports:
              - "5173:5173"
            volumes:
              - ./frontend:/app
              - /app/node_modules

        volumes:
          db_data:
        """),

    ".env.example": dedent("""\
        # Backend DB
        DATABASE_URL=postgresql+asyncpg://cnc:cncpass@db:5432/cnc

        # Secrets
        SECRET_KEY=change-me
        QR_SECRET=change-qr-secret

        # Telegram (volitelné)
        TELEGRAM_BOT_TOKEN=
        TELEGRAM_CHAT_ID=

        # SMTP (volitelné)
        SMTP_HOST=
        SMTP_PORT=587
        SMTP_USER=
        SMTP_PASS=

        # Other
        FRONTEND_URL=http://localhost:5173
        """),

    "README.md": dedent("""\
        # CNC Capture — Generated Project
        Tento repozitář byl vygenerován automaticky skriptem `build_project.py`.

        ## Struktura
        - backend/ — FastAPI backend
        - worker/ — Dramatiq worker
        - frontend/ — React (Vite) scanner PWA
        - docker-compose.yml — lokální orchestrace: db, redis, backend, worker, frontend
        - .env.example — proměnné prostředí

        ## Rychlý start (lokálně)
        1. zkopíruj `.env.example` do `.env` a uprav hodnoty (alespoň DB pokud chceš jinak)
        2. `docker compose up --build`
        3. Backend: http://localhost:8000 (OpenAPI: /docs)
        4. Frontend: http://localhost:5173

        ## Poznámky
        - Měj na paměti, že tento projekt je skeleton pro rychlé testování a další rozvoj.
        - Pro produkci se doporučuje přidat Alembic migrace, SSL, JWT secrets, RBAC, atd.
        """),

    # backend files (some folders)
    "backend/Dockerfile": dedent("""\
        FROM python:3.11-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . /app
        CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        """),

    "backend/requirements.txt": dedent("""\
        fastapi==0.100.0
        uvicorn[standard]==0.22.0
        SQLAlchemy==2.0.21
        asyncpg==0.27.0
        alembic==1.12.0
        pydantic==2.6.0
        python-jose==3.3.0
        passlib[bcrypt]==1.7.5
        aiosmtplib==1.1.6
        httpx==0.24.1
        cryptography==41.0.3
        reportlab==4.1.0
        qrcode==7.4.2
        pillow==10.0.0
        psycopg2-binary==2.9.7
        """),

    "backend/app/main.py": dedent("""\
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
        """),

    "backend/app/core/config.py": dedent("""\
        from pydantic import BaseSettings

        class Settings(BaseSettings):
            DATABASE_URL: str = "postgresql+asyncpg://cnc:cncpass@db:5432/cnc"
            SECRET_KEY: str = "replace-me-with-secure-secret"
            ACCESS_TOKEN_EXPIRE_MINUTES: int = 60*24
            QR_SECRET: str = "qr-secret-change"
            TELEGRAM_BOT_TOKEN: str = ""
            TELEGRAM_CHAT_ID: str = ""
            SMTP_HOST: str = ""
            SMTP_PORT: int = 587
            SMTP_USER: str = ""
            SMTP_PASS: str = ""
            FRONTEND_URL: str = "http://localhost:5173"

            class Config:
                env_file = "/app/.env"

        settings = Settings()
        """),

    "backend/app/db/session.py": dedent("""\
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker
        from app.core.config import settings

        engine = create_async_engine(settings.DATABASE_URL, future=True, echo=False)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        """),

    "backend/app/db/base.py": dedent("""\
        from sqlalchemy.orm import declarative_base
        Base = declarative_base()
        """),

    "backend/app/db/models.py": dedent("""\
        from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, JSON, UniqueConstraint
        from sqlalchemy.sql import func
        import enum
        from app.db.base import Base
        from sqlalchemy.orm import relationship

        class SessionStatus(str, enum.Enum):
            started = "started"
            stopped = "stopped"
            cancelled = "cancelled"

        class User(Base):
            __tablename__ = "users"
            id = Column(Integer, primary_key=True)
            username = Column(String, unique=True, nullable=False)
            full_name = Column(String)
            email = Column(String)

        class Machine(Base):
            __tablename__ = "machines"
            id = Column(Integer, primary_key=True)
            name = Column(String, nullable=False)

        class Job(Base):
            __tablename__ = "jobs"
            id = Column(Integer, primary_key=True)
            name = Column(String)
            customer = Column(String)

        class Drawing(Base):
            __tablename__ = "drawings"
            id = Column(Integer, primary_key=True)
            job_id = Column(Integer, ForeignKey("jobs.id"))
            drawing_number = Column(String)
            planned_time_per_piece = Column(Integer, default=0)
            planned_pieces = Column(Integer, default=1)

            job = relationship("Job")

        class JobCard(Base):
            __tablename__ = "job_cards"
            id = Column(Integer, primary_key=True)
            drawing_id = Column(Integer, ForeignKey("drawings.id"))
            card_number = Column(String)
            qr_payload = Column(String)

            drawing = relationship("Drawing")

        class Session(Base):
            __tablename__ = "sessions"
            id = Column(Integer, primary_key=True)
            job_card_id = Column(Integer, ForeignKey("job_cards.id"))
            operator_id = Column(Integer, ForeignKey("users.id"))
            machine_id = Column(Integer, ForeignKey("machines.id"))
            piece_index = Column(Integer, default=1)
            start_ts = Column(DateTime(timezone=True), server_default=func.now())
            stop_ts = Column(DateTime(timezone=True), nullable=True)
            duration_seconds = Column(Integer, nullable=True)
            status = Column(Enum(SessionStatus), default=SessionStatus.started)
            meta = Column(JSON, nullable=True)

            job_card = relationship("JobCard")
            operator = relationship("User")
            machine = relationship("Machine")

            __table_args__ = (
                UniqueConstraint('job_card_id', 'piece_index', 'machine_id', 'operator_id', name='uniq_piece_owner'),
            )
        """),

    "backend/app/services/qr.py": dedent("""\
        import hmac, hashlib, base64, datetime
        from app.core.config import settings

        def build_qr_payload(job_card_id: int, issued_at: datetime.datetime = None) -> str:
            if issued_at is None:
                issued_at = datetime.datetime.utcnow()
            payload = f"{job_card_id}|{issued_at.isoformat()}"
            sig = hmac.new(settings.QR_SECRET.encode(), payload.encode(), hashlib.sha256).digest()
            token = base64.urlsafe_b64encode(payload.encode() + b"." + sig).decode()
            return token

        def verify_qr_payload(token: str):
            try:
                raw = base64.urlsafe_b64decode(token.encode())
                payload_part, sig = raw.rsplit(b".", 1)
                expected = hmac.new(settings.QR_SECRET.encode(), payload_part, hashlib.sha256).digest()
                if not hmac.compare_digest(expected, sig):
                    return None
                payload = payload_part.decode()
                job_card_id_str, issued_at = payload.split("|", 1)
                return {"job_card_id": int(job_card_id_str), "issued_at": issued_at}
            except Exception:
                return None
        """),

    "backend/app/services/pdfgen.py": dedent("""\
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        from io import BytesIO
        from app.db.models import JobCard, Drawing
        import qrcode
        from PIL import Image

        def generate_job_card_pdf(job_card: JobCard, drawing: Drawing):
            buf = BytesIO()
            c = canvas.Canvas(buf, pagesize=A4)
            width, height = A4
            c.setFont("Helvetica", 14)
            c.drawString(40, height-40, f"Průvodka: {job_card.card_number}")
            c.setFont("Helvetica", 12)
            c.drawString(40, height-80, f"Výkres: {drawing.drawing_number}  (Job {drawing.job_id})")
            c.drawString(40, height-110, f"Plánovaný kusů: {drawing.planned_pieces}")
            c.drawString(40, height-140, f"Plánovaný čas / kus (s): {drawing.planned_time_per_piece}")
            # generate qr image
            qr_img = qrcode.make(job_card.qr_payload)
            qr_buf = BytesIO()
            qr_img.save(qr_buf, format="PNG")
            qr_buf.seek(0)
            # draw QR onto PDF
            c.drawInlineImage(Image.open(qr_buf), 40, height-380, width=160, height=160)
            c.showPage()
            c.save()
            buf.seek(0)
            return buf.read()
        """),

    "backend/app/services/notifier.py": dedent("""\
        import aiohttp, aiosmtplib
        from app.core.config import settings
        from email.message import EmailMessage

        async def send_telegram(text: str):
            if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
                return
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            async with aiohttp.ClientSession() as s:
                await s.post(url, json={"chat_id": settings.TELEGRAM_CHAT_ID, "text": text})

        async def send_email(subject: str, body: str, to_email: str):
            if not settings.SMTP_HOST:
                return
            msg = EmailMessage()
            msg["From"] = settings.SMTP_USER
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.set_content(body)
            await aiosmtplib.send(msg, hostname=settings.SMTP_HOST, port=settings.SMTP_PORT,
                                  username=settings.SMTP_USER, password=settings.SMTP_PASS, start_tls=True)
        """),

    "backend/app/api/v1/scan.py": dedent("""\
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
        """),

    "backend/app/api/v1/jobs.py": dedent("""\
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
        """),

    "backend/app/api/v1/auth.py": dedent("""\
        from fastapi import APIRouter, HTTPException
        from pydantic import BaseModel
        from datetime import datetime, timedelta
        from jose import jwt
        from app.core.config import settings

        router = APIRouter()

        class Token(BaseModel):
            access_token: str
            token_type: str = "bearer"

        class LoginIn(BaseModel):
            username: str

        @router.post("/login", response_model=Token)
        async def login(payload: LoginIn):
            # demo: accept any username, issue token (for real app implement password check)
            to_encode = {"sub": payload.username}
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            to_encode.update({"exp": expire.isoformat()})
            token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
            return {"access_token": token, "token_type": "bearer"}
        """),

    # worker
    "worker/Dockerfile": dedent("""\
        FROM python:3.11-slim
        WORKDIR /app
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . /app
        CMD ["dramatiq", "worker.py", "--processes", "1", "--threads", "4"]
        """),

    "worker/requirements.txt": dedent("""\
        dramatiq==1.13.0
        redis==4.5.5
        aiohttp==3.9.4
        aiosmtplib==1.1.6
        reportlab==4.1.0
        qrcode==7.4.2
        pillow==10.0.0
        SQLAlchemy==2.0.21
        asyncpg==0.27.0
        """),

    "worker/worker.py": dedent("""\
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
        """),

    # frontend minimal
    "frontend/package.json": dedent("""\
        {
          "name": "cnc-frontend",
          "version": "0.1.0",
          "private": true,
          "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview"
          },
          "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "@zxing/browser": "^0.0.10"
          },
          "devDependencies": {
            "vite": "^5.0.0",
            "@vitejs/plugin-react": "^4.0.0"
          }
        }
        """),

    "frontend/src/Scanner.jsx": dedent("""\
        import React, { useEffect, useRef, useState } from "react";
        import { BrowserMultiFormatReader } from "@zxing/browser";

        export default function Scanner() {
          const videoRef = useRef();
          const [result, setResult] = useState(null);
          const [operatorId, setOperatorId] = useState(1);
          const [machineId, setMachineId] = useState(1);

          useEffect(() => {
            const codeReader = new BrowserMultiFormatReader();
            let selectedDeviceId;

            codeReader
              .listVideoInputDevices()
              .then(videoInputDevices => {
                if (videoInputDevices.length > 0) {
                  selectedDeviceId = videoInputDevices[0].deviceId;
                  codeReader.decodeFromVideoDevice(selectedDeviceId, videoRef.current, (result, err) => {
                    if (result) {
                      setResult(result.getText());
                      // send to backend
                      fetch("/api/v1/scan", {
                        method: "POST",
                        headers: {"Content-Type":"application/json"},
                        body: JSON.stringify({ operator_id: operatorId, machine_id: machineId, qr_payload: result.getText() })
                      }).then(r=>r.json()).then(console.log).catch(console.error);
                    }
                  });
                }
              })
              .catch(err => console.error(err));

            return () => {
              codeReader.reset();
            };
          }, [operatorId, machineId]);

          return (
            <div>
              <h3>Scanner</h3>
              <div>
                Operator id: <input type="number" value={operatorId} onChange={e=>setOperatorId(+e.target.value)} />
                Machine id: <input type="number" value={machineId} onChange={e=>setMachineId(+e.target.value)} />
              </div>
              <video ref={videoRef} style={{width: "100%", maxWidth: 640}} />
              <div>Last QR: {result}</div>
            </div>
          );
        }
        """),

    "frontend/src/App.jsx": dedent("""\
        import React from "react";
        import Scanner from "./Scanner";

        export default function App(){
          return (
            <div style={{padding:20}}>
              <h1>CNC Capture — Scanner</h1>
              <Scanner />
            </div>
          );
        }
        """),

    "frontend/vite.config.js": dedent("""\
        import { defineConfig } from 'vite'
        import react from '@vitejs/plugin-react'

        export default defineConfig({
          plugins: [react()],
          server: { port: 5173, proxy: { '/api': 'http://backend:8000' } }
        })
        """),

    # tests
    "tests/test_scan.py": dedent("""\
        import pytest
        from httpx import AsyncClient
        from app.main import app

        @pytest.mark.asyncio
        async def test_start_stop_cycle():
            async with AsyncClient(app=app, base_url="http://test") as ac:
                # create job
                r = await ac.post("/api/v1/jobs", json={"name":"Tst", "customer":"X"})
                assert r.status_code==200
                job_id = r.json()["id"]
                r2 = await ac.post("/api/v1/drawings", json={"job_id":job_id,"drawing_number":"D1","planned_time_per_piece":10,"planned_pieces":1})
                drawing_id = r2.json()["id"]
                r3 = await ac.post("/api/v1/jobcards", json={"drawing_id":drawing_id,"card_number":"C1"})
                qc = r3.json()
                token = qc["qr_payload"]
                # start
                r4 = await ac.post("/api/v1/scan", json={"operator_id":1,"machine_id":1,"qr_payload":token})
                assert r4.json()["action"]=="started"
                # stop
                r5 = await ac.post("/api/v1/scan", json={"operator_id":1,"machine_id":1,"qr_payload":token})
                assert r5.json()["action"]=="stopped"
        """),

    # simple CI pipeline
    ".github/workflows/ci.yml": dedent("""\
        name: CI

        on:
          push:
            branches: [ main ]
          pull_request:
            branches: [ main ]

        jobs:
          test:
            runs-on: ubuntu-latest
            services:
              postgres:
                image: postgres:15
                env:
                  POSTGRES_USER: cnc
                  POSTGRES_PASSWORD: cncpass
                  POSTGRES_DB: cnc
                ports:
                  - 5432:5432
              redis:
                image: redis:7
                ports:
                  - 6379:6379
            steps:
              - uses: actions/checkout@v4
              - name: Set up Python
                uses: actions/setup-python@v4
                with:
                  python-version: 3.11
              - name: Install backend deps
                run: |
                  pip install -r backend/requirements.txt
              - name: Run tests
                run: |
                  pytest -q
        """),
}

# helper to create nested path
def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path}")

def create_project():
    # remove existing
    if ROOT.exists():
        print(f"Removing existing {ROOT} ...")
        shutil.rmtree(ROOT)
    print("Creating project structure...")
    # write top-level files
    for rel, content in FILES.items():
        target = ROOT / rel
        write_file(target, content)

    # create minimal frontend src structure
    (ROOT / "frontend" / "src").mkdir(parents=True, exist_ok=True)
    # add index.html and main.jsx
    write_file(ROOT / "frontend" / "index.html", dedent("""\
        <!doctype html>
        <html>
          <head>
            <meta charset="utf-8" />
            <meta name="viewport" content="width=device-width, initial-scale=1.0" />
            <title>CNC Capture</title>
          </head>
          <body>
            <div id="root"></div>
            <script type="module" src="/src/main.jsx"></script>
          </body>
        </html>
        """))
    write_file(ROOT / "frontend" / "src" / "main.jsx", dedent("""\
        import React from 'react'
        import { createRoot } from 'react-dom/client'
        import App from './App'
        import './style.css'

        createRoot(document.getElementById('root')).render(<App />)
        """))
    write_file(ROOT / "frontend" / "src" / "style.css", "body{font-family:Arial,Helvetica,sans-serif}\n")
    # already included App.jsx and Scanner.jsx in FILES; move them into src
    # (they are at frontend/src path but dictionary keys were with that path)
    # ensure package.json exists (it does)

    # create backend app package __init__ files
    write_file(ROOT / "backend" / "app" / "__init__.py", "")
    write_file(ROOT / "backend" / "app" / "api" / "__init__.py", "")
    write_file(ROOT / "backend" / "app" / "api" / "v1" / "__init__.py", "")
    write_file(ROOT / "backend" / "app" / "services" / "__init__.py", "")
    write_file(ROOT / "backend" / "app" / "db" / "__init__.py", "")

    # Alembic skeleton
    alembic_env = dedent("""\
        from logging.config import fileConfig
        from sqlalchemy import engine_from_config
        from sqlalchemy import pool
        from alembic import context
        import os, sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        from app.db.base import Base
        from app.core.config import settings
        target_metadata = Base.metadata

        config = context.config
        fileConfig(config.config_file_name)

        def run_migrations_offline():
            url = settings.DATABASE_URL
            context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
            with context.begin_transaction():
                context.run_migrations()

        def run_migrations_online():
            connectable = engine_from_config(
                config.get_section(config.config_ini_section),
                prefix='sqlalchemy.',
                poolclass=pool.NullPool,
                url=settings.DATABASE_URL,
            )
            with connectable.connect() as connection:
                context.configure(connection=connection, target_metadata=target_metadata)
                with context.begin_transaction():
                    context.run_migrations()

        if context.is_offline_mode():
            run_migrations_offline()
        else:
            run_migrations_online()
        """)
    write_file(ROOT / "backend" / "app" / "alembic" / "env.py", alembic_env)
    write_file(ROOT / "backend" / "app" / "alembic" / "script.py.mako", "")  # placeholder

    # create gitignore
    write_file(ROOT / ".gitignore", dedent("""\
        __pycache__/
        *.pyc
        .env
        .venv
        node_modules/
        /cnc-capture.zip
        """))

    # create package.json for frontend already added

    # Write a small entrypoint script to generate .env from example
    write_file(ROOT / "setup_env.sh", dedent("""\
        #!/usr/bin/env bash
        if [ -f .env ]; then
          echo ".env exists"
        else
          cp .env.example .env
          echo "Copied .env.example -> .env. Edit it as needed."
        fi
        """))
    os.chmod(ROOT / "setup_env.sh", 0o755)

    # create zip
    zip_path = Path.cwd() / "cnc-capture.zip"
    if zip_path.exists():
        zip_path.unlink()
    print("Creating zip archive...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for folder, subs, files in os.walk(ROOT):
            for file in files:
                full_path = os.path.join(folder, file)
                arcname = os.path.relpath(full_path, ROOT.parent)
                z.write(full_path, arcname)
    print(f"Created {zip_path}")

if __name__ == "__main__":
    create_project()
    print("Done. Projekt je vytvořen ve složce 'cnc-capture' a archiv 'cnc-capture.zip' byl vytvořen.")
    print("Přečti README.md pro další kroky.")
