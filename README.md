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
