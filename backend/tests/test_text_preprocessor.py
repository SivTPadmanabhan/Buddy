import pytest

from app.services.text_preprocessor import ContentBlock, preprocess_for_chunking


def test_pure_prose_returns_single_block():
    text = "This is a normal paragraph about recursion. It has multiple sentences."
    blocks = preprocess_for_chunking(text, "text/plain")
    assert len(blocks) == 1
    assert blocks[0].block_type == "prose"
    assert blocks[0].skip_semantic is False


def test_detects_pipe_table():
    text = "Introduction paragraph.\n\n| Name | Score |\n| --- | --- |\n| Alice | 10 |\n| Bob | 20 |\n\nConclusion paragraph."
    blocks = preprocess_for_chunking(text, "text/plain")
    types = [b.block_type for b in blocks]
    assert "table" in types
    assert "prose" in types


def test_detects_tab_separated_table():
    text = "Header text.\n\nname\tscore\tgrade\nalice\t10\tA\nbob\t20\tB\n\nFooter text."
    blocks = preprocess_for_chunking(text, "text/plain")
    types = [b.block_type for b in blocks]
    assert "table" in types


def test_detects_code_fence():
    text = "Some explanation.\n\n```python\ndef hello():\n    print('hi')\n```\n\nMore text."
    blocks = preprocess_for_chunking(text, "text/plain")
    types = [b.block_type for b in blocks]
    assert "code" in types
    assert "prose" in types


def test_detects_indented_code_block():
    text = "Explanation:\n\n    def foo():\n        return 42\n    \n    def bar():\n        return 7\n\nMore prose here."
    blocks = preprocess_for_chunking(text, "text/plain")
    types = [b.block_type for b in blocks]
    assert "code" in types


def test_ocr_content_marked_prose_not_skipped():
    text = "Some   noisy   OCR    text  with    gaps."
    blocks = preprocess_for_chunking(text, "image/png")
    assert len(blocks) == 1
    assert blocks[0].block_type == "prose"
    assert blocks[0].skip_semantic is False
    assert "   " not in blocks[0].text


def test_ocr_collapses_whitespace():
    text = "word1    word2\t\t\tword3"
    blocks = preprocess_for_chunking(text, "image/jpeg")
    assert "  " not in blocks[0].text


def test_mixed_content_returns_ordered_blocks():
    text = (
        "Introduction to data structures.\n\n"
        "| Type | Complexity |\n| --- | --- |\n| Array | O(1) |\n| List | O(n) |\n\n"
        "Here is an example:\n\n"
        "```python\narr = [1, 2, 3]\n```\n\n"
        "That concludes the overview."
    )
    blocks = preprocess_for_chunking(text, "text/plain")
    assert len(blocks) >= 3
    types = [b.block_type for b in blocks]
    assert types[0] == "prose"
    assert "table" in types
    assert "code" in types


def test_table_blocks_skip_semantic():
    text = "| A | B |\n| --- | --- |\n| 1 | 2 |"
    blocks = preprocess_for_chunking(text, "text/plain")
    table_blocks = [b for b in blocks if b.block_type == "table"]
    assert all(b.skip_semantic for b in table_blocks)


def test_code_blocks_skip_semantic():
    text = "```\nsome code\n```"
    blocks = preprocess_for_chunking(text, "text/plain")
    code_blocks = [b for b in blocks if b.block_type == "code"]
    assert all(b.skip_semantic for b in code_blocks)


def test_empty_text_returns_empty():
    blocks = preprocess_for_chunking("", "text/plain")
    assert blocks == []


def test_whitespace_only_returns_empty():
    blocks = preprocess_for_chunking("   \n\n  ", "text/plain")
    assert blocks == []
