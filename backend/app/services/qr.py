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
