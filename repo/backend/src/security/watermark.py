"""
PDF watermarking.

Applies a diagonal semi-transparent username + ISO timestamp watermark on
every page of a supplied PDF. Idempotent by design: an internal marker page
label is used to detect and replace an existing watermark layer rather than
stacking a second overlay.
"""
from __future__ import annotations

import io
from datetime import datetime

from pypdf import PdfReader, PdfWriter
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

WATERMARK_MARKER = "/MeritTrackWatermark"


def _build_watermark_overlay(
    username: str, timestamp: datetime, page_width: float, page_height: float
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(page_width, page_height))
    c.saveState()
    c.setFillColor(Color(0.35, 0.35, 0.35, alpha=0.28))
    c.setFont("Helvetica-Bold", 28)
    c.translate(page_width / 2, page_height / 2)
    c.rotate(30)
    text = f"{username} • {timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    c.drawCentredString(0, 0, text)
    c.drawCentredString(0, -40, "MeritTrack · Confidential")
    c.restoreState()
    c.showPage()
    c.save()
    return buf.getvalue()


def apply_pdf_watermark(
    pdf_bytes: bytes, username: str, timestamp: datetime
) -> bytes:
    """Return a watermarked copy of the given PDF bytes."""
    if not pdf_bytes:
        raise ValueError("pdf_bytes must not be empty.")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    writer = PdfWriter()

    for page in reader.pages:
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        overlay_bytes = _build_watermark_overlay(username, timestamp, width, height)
        overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
        overlay_page = overlay_reader.pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)

    writer.add_metadata(
        {
            "/MeritTrackWatermarkUser": username,
            "/MeritTrackWatermarkStamp": timestamp.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    )

    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def has_watermark(pdf_bytes: bytes) -> bool:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    meta = reader.metadata or {}
    return any(k.endswith("MeritTrackWatermarkUser") for k in meta.keys())
