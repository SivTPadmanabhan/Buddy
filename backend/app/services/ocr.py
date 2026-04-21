import io

import pytesseract
from PIL import Image


def extract_text(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    return pytesseract.image_to_string(img).strip()
