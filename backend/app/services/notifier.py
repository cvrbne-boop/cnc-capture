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
