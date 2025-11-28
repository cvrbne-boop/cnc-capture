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
