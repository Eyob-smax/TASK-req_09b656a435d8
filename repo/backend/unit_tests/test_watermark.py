"""
PDF watermarking end-to-end (in-memory bytes only).
"""
import io
from datetime import datetime, timezone

from pypdf import PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from src.security.watermark import apply_pdf_watermark, has_watermark


def _sample_pdf(text: str = "Sample content") -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.drawString(72, 720, text)
    c.showPage()
    c.save()
    return buf.getvalue()


def test_watermark_applies_metadata():
    pdf = _sample_pdf()
    stamped_at = datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)
    stamped = apply_pdf_watermark(pdf, username="alice", timestamp=stamped_at)
    assert stamped != pdf
    assert has_watermark(stamped) is True
    meta = PdfReader(io.BytesIO(stamped)).metadata or {}
    assert meta.get("/MeritTrackWatermarkUser") == "alice"
    assert meta.get("/MeritTrackWatermarkStamp", "").startswith("2026-04-18T12:00:00")


def test_watermark_preserves_text():
    pdf = _sample_pdf("Important Document")
    stamped = apply_pdf_watermark(
        pdf, username="alice", timestamp=datetime.now(tz=timezone.utc)
    )
    reader = PdfReader(io.BytesIO(stamped))
    all_text = "".join(p.extract_text() or "" for p in reader.pages)
    assert "Important Document" in all_text


def test_watermark_is_idempotent():
    pdf = _sample_pdf()
    stamped_at = datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)
    first = apply_pdf_watermark(pdf, username="alice", timestamp=stamped_at)
    second = apply_pdf_watermark(first, username="alice", timestamp=stamped_at)
    assert has_watermark(second) is True
    reader = PdfReader(io.BytesIO(second))
    meta = reader.metadata or {}
    # Still exactly one MeritTrackWatermarkUser marker (not duplicated).
    assert sum(1 for k in meta.keys() if k.endswith("MeritTrackWatermarkUser")) == 1
