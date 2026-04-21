import io
from typing import Callable

import tiktoken
from docx import Document as DocxDocument
from openpyxl import load_workbook
from pptx import Presentation
from pypdf import PdfReader

from app.logging_config import get_logger

log = get_logger("app.services.document")

PDF_MIME = "application/pdf"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
TEXT_MIMES = {"text/plain", "text/csv", "text/markdown"}
IMAGE_MIMES = {"image/png", "image/jpeg", "image/jpg"}

_ENCODING = tiktoken.get_encoding("cl100k_base")


class UnsupportedFileType(Exception):
    pass


def load_text(content: bytes) -> str:
    return content.decode("utf-8", errors="replace").lstrip("\ufeff")


def load_pdf(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def load_docx(content: bytes) -> str:
    doc = DocxDocument(io.BytesIO(content))
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def load_pptx(content: bytes) -> str:
    prs = Presentation(io.BytesIO(content))
    parts = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    txt = "".join(run.text for run in para.runs) or para.text
                    if txt.strip():
                        parts.append(txt)
    return "\n".join(parts)


def load_xlsx(content: bytes) -> str:
    wb = load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    lines = []
    for sheet in wb.worksheets:
        for row in sheet.iter_rows(values_only=True):
            cells = [str(c) for c in row if c is not None]
            if cells:
                lines.append("\t".join(cells))
    return "\n".join(lines)


def chunk_text(
    text: str, chunk_tokens: int = 500, overlap_tokens: int = 50
) -> list[str]:
    text = text.strip()
    if not text:
        return []

    tokens = _ENCODING.encode(text)
    if len(tokens) <= chunk_tokens:
        return [text]

    step = chunk_tokens - overlap_tokens
    if step <= 0:
        raise ValueError("overlap_tokens must be smaller than chunk_tokens")

    chunks: list[str] = []
    start = 0
    while start < len(tokens):
        window = tokens[start : start + chunk_tokens]
        chunks.append(_ENCODING.decode(window))
        if start + chunk_tokens >= len(tokens):
            break
        start += step
    return chunks


def _import_ocr() -> Callable[[bytes], str]:
    from app.services.ocr import extract_text
    return extract_text


_LOADERS: dict[str, Callable[[bytes], str]] = {
    PDF_MIME: load_pdf,
    DOCX_MIME: load_docx,
    PPTX_MIME: load_pptx,
    XLSX_MIME: load_xlsx,
}


def load_bytes(content: bytes, mime_type: str, filename: str) -> str:
    loader = _LOADERS.get(mime_type)
    if loader:
        return loader(content)
    if mime_type in TEXT_MIMES:
        return load_text(content)
    if mime_type in IMAGE_MIMES:
        return _import_ocr()(content)
    log.warning(
        "unsupported_file_type",
        category="sync",
        action="parse_document",
        mime_type=mime_type,
        filename=filename,
    )
    raise UnsupportedFileType(f"{mime_type} ({filename})")
