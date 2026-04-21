import io

from PIL import Image, ImageDraw, ImageFont

from app.services.ocr import extract_text


def _image_with_text(text: str) -> bytes:
    img = Image.new("RGB", (400, 80), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.text((10, 20), text, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_extract_text_reads_simple_image():
    data = _image_with_text("HELLO WORLD")
    result = extract_text(data)
    assert "HELLO" in result.upper()


def test_extract_text_blank_image_returns_empty():
    img = Image.new("RGB", (200, 80), "white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = extract_text(buf.getvalue())
    assert result.strip() == ""
