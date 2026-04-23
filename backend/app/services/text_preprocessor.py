import re
from dataclasses import dataclass


@dataclass
class ContentBlock:
    text: str
    block_type: str  # "prose" | "table" | "code" | "ocr_raw"
    skip_semantic: bool


_CODE_FENCE_RE = re.compile(r"^```", re.MULTILINE)
_PIPE_TABLE_RE = re.compile(r"^\|.+\|$", re.MULTILINE)
_TAB_TABLE_RE = re.compile(r"^[^\t\n]+\t[^\t\n]+\t", re.MULTILINE)
_INDENTED_CODE_RE = re.compile(r"^(    .+\n){2,}", re.MULTILINE)


def _is_ocr_mime(mime_type: str) -> bool:
    return mime_type.startswith("image/")


def _clean_ocr_text(text: str) -> str:
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return text.strip()


def _split_into_sections(text: str) -> list[str]:
    return re.split(r"\n{2,}", text)


def _is_pipe_table(section: str) -> bool:
    lines = section.strip().splitlines()
    if len(lines) < 2:
        return False
    pipe_lines = sum(1 for l in lines if re.match(r"^\|.+\|$", l.strip()))
    return pipe_lines >= 2


def _is_tab_table(section: str) -> bool:
    lines = section.strip().splitlines()
    if len(lines) < 2:
        return False
    tab_lines = sum(1 for l in lines if l.count("\t") >= 2)
    return tab_lines >= 2


def _is_code_fence(section: str) -> bool:
    return section.strip().startswith("```") and section.strip().endswith("```")


def _is_indented_code(section: str) -> bool:
    lines = section.splitlines()
    if len(lines) < 2:
        return False
    indented = sum(1 for l in lines if l.startswith("    ") or l.strip() == "")
    return indented == len(lines) and any(l.startswith("    ") for l in lines)


def _classify_section(section: str) -> str:
    if _is_code_fence(section):
        return "code"
    if _is_indented_code(section):
        return "code"
    if _is_pipe_table(section):
        return "table"
    if _is_tab_table(section):
        return "table"
    return "prose"


def preprocess_for_chunking(text: str, mime_type: str) -> list[ContentBlock]:
    text = text.strip()
    if not text:
        return []

    if _is_ocr_mime(mime_type):
        cleaned = _clean_ocr_text(text)
        if not cleaned:
            return []
        return [ContentBlock(text=cleaned, block_type="prose", skip_semantic=False)]

    sections = _split_into_sections(text)
    blocks: list[ContentBlock] = []
    current_prose_parts: list[str] = []

    def flush_prose():
        if current_prose_parts:
            merged = "\n\n".join(current_prose_parts)
            if merged.strip():
                blocks.append(ContentBlock(
                    text=merged, block_type="prose", skip_semantic=False
                ))
            current_prose_parts.clear()

    for section in sections:
        if not section.strip():
            continue
        block_type = _classify_section(section)
        if block_type == "prose":
            current_prose_parts.append(section)
        else:
            flush_prose()
            blocks.append(ContentBlock(
                text=section.strip(),
                block_type=block_type,
                skip_semantic=True,
            ))

    flush_prose()
    return blocks
