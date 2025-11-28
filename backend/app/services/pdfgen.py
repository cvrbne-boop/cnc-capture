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
