# backend/utils/docx_import.py
"""Best-effort conversion of an uploaded .docx into letter-template blocks."""
import io
from docx import Document
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_ALIGN_PARAGRAPH

_ALIGN = {
    WD_ALIGN_PARAGRAPH.CENTER: "center",
    WD_ALIGN_PARAGRAPH.RIGHT: "right",
    WD_ALIGN_PARAGRAPH.LEFT: "left",
}


def _list_kind(paragraph) -> str | None:
    """Return 'numbered'/'bullet' if the paragraph is a list item, else None."""
    name = (paragraph.style.name or "").lower() if paragraph.style else ""
    if "list number" in name or "list paragraph" in name and _has_numbering(paragraph):
        return "numbered"
    if "list bullet" in name:
        return "bullet"
    if _has_numbering(paragraph):
        return "numbered"
    return None


def _has_numbering(paragraph) -> bool:
    pPr = paragraph._p.pPr
    return pPr is not None and pPr.numPr is not None


def _text_block(paragraph, idx: int) -> dict:
    align = _ALIGN.get(paragraph.alignment, "left")
    run = paragraph.runs[0] if paragraph.runs else None
    block = {
        "id": f"b{idx}",
        "type": "text",
        "content": paragraph.text,
        "align": align,
        "bold": bool(run.bold) if run is not None and run.bold is not None else False,
        "italic": bool(run.italic) if run is not None and run.italic is not None else False,
    }
    if run is not None and run.font is not None:
        if run.font.name:
            block["font"] = run.font.name
        if run.font.size is not None:
            block["size"] = int(run.font.size.pt)
    return block


def parse_docx_to_blocks(docx_bytes: bytes) -> list:
    """Parse a .docx into an ordered list of template block dicts.

    Paragraphs become text blocks (carrying alignment + first-run bold/italic/font/size),
    consecutive list items collapse into one list block, empty paragraphs become spacers,
    and the first table becomes the single ip_table block (further tables are ignored).
    """
    doc = Document(io.BytesIO(docx_bytes))
    blocks: list = []
    idx = 0
    cur_list: dict | None = None
    has_table = False

    def close_list():
        nonlocal cur_list
        if cur_list is not None:
            blocks.append(cur_list)
            cur_list = None

    for child in doc.element.body.iterchildren():
        tag = child.tag
        if tag.endswith("}p"):
            paragraph = Paragraph(child, doc)
            text = paragraph.text.strip()
            if text == "{ip_table}":
                close_list()
                if not has_table:
                    has_table = True
                    idx += 1
                    blocks.append({"id": f"b{idx}", "type": "ip_table"})
                continue
            lk = _list_kind(paragraph)
            if lk and text:
                if cur_list is None or cur_list["style"] != lk:
                    close_list()
                    idx += 1
                    cur_list = {"id": f"b{idx}", "type": "list", "style": lk, "items": []}
                cur_list["items"].append(paragraph.text.strip())
                continue
            close_list()
            if not text:
                idx += 1
                blocks.append({"id": f"b{idx}", "type": "spacer", "lines": 1})
            else:
                idx += 1
                blocks.append(_text_block(paragraph, idx))
        elif tag.endswith("}tbl"):
            close_list()
            if not has_table:
                has_table = True
                idx += 1
                blocks.append({"id": f"b{idx}", "type": "ip_table"})
            # additional tables ignored (telco table is generated, not copied)

    close_list()
    return blocks
