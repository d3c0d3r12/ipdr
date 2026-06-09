# ISP Letter Template Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users design their own ISP-letter `.docx` format from an in-app block builder with live preview, save templates per-user (plus a shared department default), while the IP table stays telco-correct.

**Architecture:** A letter template is an ordered list of typed JSON blocks (`text`, `list`, `ip_table`, `spacer`). A backend renderer walks blocks to build the `.docx`, delegating the IP table to existing per-ISP logic. Templates live in a new MongoDB `letter_templates` collection with CRUD endpoints. The frontend renders the same blocks as HTML for live preview.

**Tech Stack:** FastAPI + PyMongo (sync `get_db`), python-docx, Pydantic v2; React 18 + Vite + TypeScript; pytest (+ mongomock for DB tests).

**Spec:** `docs/superpowers/specs/2026-06-09-isp-letter-template-builder-design.md`

**Branch:** `feature/isp-letter-template-builder` (already created).

---

## File Structure

**Backend (create):**
- `backend/utils/letter_template.py` — Pydantic block/template models, `PLACEHOLDERS`, `substitute()`, `DEFAULT_TEMPLATE` dict.
- `backend/services/letter_template_service.py` — CRUD + seeding over `letter_templates` collection.
- `backend/routers/letter_templates.py` — `/api/letter-templates` endpoints.
- `backend/tests/test_letter_renderer.py` — renderer + default-parity tests (pure, no DB).
- `backend/tests/test_letter_template_service.py` — CRUD/permission tests (mongomock).

**Backend (modify):**
- `backend/utils/isp_letter_generator.py` — extract `_build_ip_table`, add `render_template_to_docx`, route `generate_letter`/`generate_all_letters` through templates.
- `backend/routers/ip_lookup.py:1045` — `generate-isp-letters` accepts optional `template_id`.
- `backend/routers/ipdr_processing.py:731` — run-based generate accepts optional `template_id`.
- `backend/main.py` — include router; seed default template on startup.
- `backend/requirements.txt` — add `mongomock` (test dep).

**Frontend (create):**
- `frontend/src/lib/templates.ts` — types + API client for templates.
- `frontend/src/pages/TemplateBuilderPage.tsx` — the builder UI + live preview.

**Frontend (modify):**
- `frontend/src/App.tsx` — add `/isp-letters/templates` route.
- `frontend/src/components/Layout.tsx` — nav entry for the builder.
- `frontend/src/pages/IspLettersCatalogPage.tsx` + `frontend/src/pages/IspLettersPage.tsx` — template selector; send `template_id`.

---

## Phase 1 — Backend renderer (pure, TDD)

### Task 1: Template schema, placeholders, substitution, default template

**Files:**
- Create: `backend/utils/letter_template.py`
- Test: `backend/tests/test_letter_renderer.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_letter_renderer.py
from utils.letter_template import (
    LetterTemplate, PLACEHOLDERS, substitute, DEFAULT_TEMPLATE,
)


def test_substitute_replaces_known_tokens():
    out = substitute("FIR {fir_number} for {isp_name}",
                     {"fir_number": "201/25", "isp_name": "Airtel"})
    assert out == "FIR 201/25 for Airtel"


def test_substitute_missing_value_becomes_empty():
    assert substitute("Hello {officer_name}!", {}) == "Hello !"


def test_placeholders_list_has_expected_tokens():
    assert "fir_number" in PLACEHOLDERS
    assert "isp_name" in PLACEHOLDERS
    assert len(PLACEHOLDERS) == 13


def test_default_template_validates_and_has_single_ip_table():
    tpl = LetterTemplate.model_validate(DEFAULT_TEMPLATE)
    ip_tables = [b for b in tpl.blocks if b.type == "ip_table"]
    assert len(ip_tables) == 1
    assert tpl.name == "IFSO Dwarka Default"


def test_template_rejects_two_ip_tables():
    import pytest
    from pydantic import ValidationError
    bad = {
        "name": "x", "scope": "user",
        "page": DEFAULT_TEMPLATE["page"],
        "blocks": [
            {"id": "a", "type": "ip_table"},
            {"id": "b", "type": "ip_table"},
        ],
    }
    with pytest.raises(ValidationError):
        LetterTemplate.model_validate(bad)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -v -p no:cacheprovider --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'utils.letter_template'`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/utils/letter_template.py
"""Schema + default for ISP letter templates (block-based)."""
from __future__ import annotations
from typing import Annotated, List, Literal, Optional, Union
from pydantic import BaseModel, Field, model_validator

PLACEHOLDERS: List[str] = [
    "fir_number", "fir_date", "letter_date", "police_station", "sections",
    "complainant", "isp_name", "officer_name", "officer_designation",
    "officer_location", "officer_contact", "subject", "email_reference",
]


def substitute(text: str, values: dict) -> str:
    """Replace every {token} with its value (empty string if missing)."""
    out = text
    for token in PLACEHOLDERS:
        out = out.replace("{" + token + "}", str(values.get(token, "") or ""))
    return out


class PageSettings(BaseModel):
    margins_inches: dict = Field(
        default_factory=lambda: {"top": 0.5, "bottom": 0.5, "left": 0.75, "right": 0.75}
    )
    default_font: str = "Calibri"
    default_size: int = 10


class TextBlock(BaseModel):
    id: str
    type: Literal["text"] = "text"
    content: str = ""
    align: Literal["left", "center", "right"] = "left"
    bold: bool = False
    italic: bool = False
    font: Optional[str] = None
    size: Optional[int] = None


class ListBlock(BaseModel):
    id: str
    type: Literal["list"] = "list"
    style: Literal["numbered", "bullet"] = "numbered"
    items: List[str] = Field(default_factory=list)
    font: Optional[str] = None
    size: Optional[int] = None


class IpTableBlock(BaseModel):
    id: str
    type: Literal["ip_table"] = "ip_table"


class SpacerBlock(BaseModel):
    id: str
    type: Literal["spacer"] = "spacer"
    lines: int = 1


Block = Annotated[
    Union[TextBlock, ListBlock, IpTableBlock, SpacerBlock],
    Field(discriminator="type"),
]


class LetterTemplate(BaseModel):
    name: str
    owner_id: Optional[str] = None
    scope: Literal["system", "user", "shared"] = "user"
    page: PageSettings = Field(default_factory=PageSettings)
    blocks: List[Block]

    @model_validator(mode="after")
    def _at_most_one_ip_table(self):
        n = sum(1 for b in self.blocks if b.type == "ip_table")
        if n > 1:
            raise ValueError("A template may contain at most one ip_table block")
        return self


def _t(id, content, **kw):
    return {"id": id, "type": "text", "content": content, **kw}


DEFAULT_TEMPLATE = {
    "name": "IFSO Dwarka Default",
    "owner_id": None,
    "scope": "system",
    "page": {
        "margins_inches": {"top": 0.5, "bottom": 0.5, "left": 0.75, "right": 0.75},
        "default_font": "Calibri",
        "default_size": 10,
    },
    "blocks": [
        _t("legal", "Seeking data under the statutory provisions contained in Section 94 of the "
                    "Bharatiya Nagarik Suraksha Sanhita, 2023 or Section 5(2) of the Indian Telegraph "
                    "Act, 1885 read with Rule 419A of the Indian Telegraph (Amendment) Rules, 2007.",
           align="center", italic=True, size=10),
        _t("office_name", "OFFICE OF THE CYBER CRIME UNIT, IFSO, SPECIAL CELL, DELHI POLICE,",
           align="center", bold=True, size=11),
        _t("office_addr", "SEC - 16C, DWARKA, NEW DELHI - 110078", align="center", size=10),
        _t("office_contact", "Contact No. 011-20892632, E-Mail ID : acp-cybercell1@delhipolice.gov.in",
           align="center", size=9),
        _t("notice", "Notice u/s 94 BNSS, 2023", align="center", bold=True, size=11),
        {"id": "sp1", "type": "spacer", "lines": 1},
        _t("to", "To,\n     The Nodal Officer\n     {isp_name}"),
        _t("subject", "Subject:- {subject} FIR No. {fir_number}, PS {police_station} ({email_reference})",
           bold=True),
        _t("salutation", "Sir,"),
        _t("body", "                It is submitted that case FIR No.{fir_number}, U/s {sections}, "
                   "Dated {fir_date}, PS {police_station}, Delhi has been registered on the complaint "
                   "of {complainant} at IFSO/CCU/Spl. Cell, New Delhi. During investigation the "
                   "following IP details/numbers have emerged as suspect."),
        _t("req_intro", "You are hereby requested to provide the following information/documents:-"),
        {"id": "reqs", "type": "list", "style": "numbered", "items": [
            "Details of the user (Name, Address, Contact No. etc.) to whom below IP's were allotted "
            "at the mentioned Date & time against each.",
            "Kindly provide the ownership of the users, to whom IP was allotted.",
            "Kindly preserve the record till further directions.",
            "Kindly provide any other useful details.",
        ]},
        _t("urgent", "The above-mentioned information is urgent and a prompt reply is anticipated."),
        {"id": "sp2", "type": "spacer", "lines": 1},
        {"id": "table", "type": "ip_table"},
        {"id": "sp3", "type": "spacer", "lines": 1},
        _t("sig", "{officer_name}\n{officer_designation}\n{officer_location}\n"
                  "Contact No.: {officer_contact}\nDated : {letter_date}"),
    ],
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -v -p no:cacheprovider --no-cov`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/utils/letter_template.py backend/tests/test_letter_renderer.py
git commit -m "feat: add ISP letter template schema, placeholders, and default template

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 2: Extract the per-ISP IP table into one `_build_ip_table` method

**Files:**
- Modify: `backend/utils/isp_letter_generator.py` (add method; refactor `create_letter_airtel/vi/jio` table loops to call it)
- Test: `backend/tests/test_letter_renderer.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_letter_renderer.py`:

```python
import pandas as pd
from docx import Document
from utils.isp_letter_generator import ISPLetterGenerator


def _sample_df():
    return pd.DataFrame([
        {"Type": "IPV4", "Search Value": "1.2.3.4",
         "From Date": "2025-01-28", "From Time": "14:30:25",
         "To Date": "2025-01-28", "To Time": "15:30:25"},
    ])


def test_build_ip_table_airtel_has_4_columns():
    doc = Document()
    ISPLetterGenerator()._build_ip_table(doc, "Airtel", _sample_df())
    table = doc.tables[0]
    assert len(table.columns) == 4
    headers = [table.rows[0].cells[i].text for i in range(4)]
    assert headers[0] == "Type" and headers[1] == "Search Value"


def test_build_ip_table_jio_has_6_columns_and_padded_time():
    doc = Document()
    ISPLetterGenerator()._build_ip_table(doc, "Jio", _sample_df())
    table = doc.tables[0]
    assert len(table.columns) == 6
    # From Time cell padded to 6 digits
    assert table.rows[1].cells[3].text == "143025"


def test_build_ip_table_vi_has_6_columns():
    doc = Document()
    ISPLetterGenerator()._build_ip_table(doc, "Vodafone Idea", _sample_df())
    assert len(doc.tables[0].columns) == 6
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -k build_ip_table -v -p no:cacheprovider --no-cov`
Expected: FAIL with `AttributeError: 'ISPLetterGenerator' object has no attribute '_build_ip_table'`

- [ ] **Step 3: Write minimal implementation**

Add this method to the `ISPLetterGenerator` class in `backend/utils/isp_letter_generator.py` (place it just above `generate_letter`). It moves the table-building logic out of the three `create_letter_*` methods:

```python
    def _build_ip_table(self, doc: Document, isp_name: str, ip_data: pd.DataFrame) -> None:
        """Append the telco-correct IP table for the ISP to the document."""
        template_type = self.get_template_type(isp_name)

        if template_type == 'airtel':
            table = doc.add_table(rows=1, cols=4)
            table.style = 'Table Grid'
            hdr = table.rows[0].cells
            hdr[0].text, hdr[1].text = 'Type', 'Search Value'
            hdr[2].text = 'From Date\n(DD-MMM-YYYY)\n(HH24:MI:SS)'
            hdr[3].text = 'To Date\n(DD-MMM-YYYY)\n(HH24:MI:SS)'
            self._bold_header(hdr, 9)
            for _, row in ip_data.iterrows():
                cells = table.add_row().cells
                ip = str(row.get('Search Value', row.get('ip', '')))
                ip_type = str(row.get('Type', '')) or ''
                if not ip_type or ip_type == 'nan':
                    ip_type = 'IPV6' if ':' in ip else 'IPV4'
                from_date = str(row.get('From Date', ''))
                from_time = str(row.get('From Time', ''))
                if from_date and from_date != 'nan':
                    fda = self.convert_date_to_airtel_format(from_date)
                    tda = self.convert_date_to_airtel_format(str(row.get('To Date', '')))
                    cells[0].text, cells[1].text = ip_type, ip
                    cells[2].text = fda + ' ' + from_time if from_time and from_time != 'nan' else fda
                    to_time = str(row.get('To Time', ''))
                    cells[3].text = tda + ' ' + to_time if to_time and to_time != 'nan' else tda
                else:
                    f = self.format_timestamp_for_airtel(row.get('timestamp', ''))
                    cells[0].text, cells[1].text = ip_type, ip
                    cells[2].text, cells[3].text = f['from_datetime'], f['to_datetime']
                self._set_cell_font(cells, 9)
            return

        # Jio and all others use 6 columns; Jio pads time to 6 digits.
        is_jio = template_type == 'jio'
        table = doc.add_table(rows=1, cols=6)
        table.style = 'Table Grid'
        hdr = table.rows[0].cells
        hdr[0].text, hdr[1].text = 'Type', 'Search Value'
        if is_jio:
            hdr[2].text, hdr[3].text = 'From Date\nYYYYMMDD', 'From Time\nHHMMSS\n(IST)'
            hdr[4].text, hdr[5].text = 'To Date\nYYYYMMDD', 'To Time\nHHMMSS\n(IST)'
        else:
            hdr[2].text, hdr[3].text = 'From Date\nDD:MM:YYYY', 'From Time\nHH:MM:SS\n(IST)'
            hdr[4].text, hdr[5].text = 'To Date\nDD:MM:YYYY', 'To Time\nHH:MM:SS\n(IST)'
        self._bold_header(hdr, 8)
        for _, row in ip_data.iterrows():
            cells = table.add_row().cells
            ip = str(row.get('Search Value', row.get('ip', '')))
            ip_type = str(row.get('Type', '')) or ''
            if not ip_type or ip_type == 'nan':
                ip_type = 'IPV6' if ':' in ip else 'IPV4'
            from_date = str(row.get('From Date', ''))
            from_time = str(row.get('From Time', ''))
            to_date = str(row.get('To Date', ''))
            to_time = str(row.get('To Time', ''))
            if from_date and from_date != 'nan':
                if is_jio:
                    from_time = self.pad_time_to_6_digits(from_time) if from_time and from_time != 'nan' else '000000'
                    to_time = self.pad_time_to_6_digits(to_time) if to_time and to_time != 'nan' else '000000'
                cells[0].text, cells[1].text = ip_type, ip
                cells[2].text = from_date
                cells[3].text = from_time if from_time and from_time != 'nan' else ''
                cells[4].text = to_date if to_date and to_date != 'nan' else ''
                cells[5].text = to_time if to_time and to_time != 'nan' else ''
            else:
                f = (self.format_timestamp_for_jio if is_jio else self.format_timestamp_for_vi)(row.get('timestamp', ''))
                cells[0].text, cells[1].text = ip_type, ip
                cells[2].text, cells[3].text = f['from_date'], f['from_time']
                cells[4].text, cells[5].text = f['to_date'], f['to_time']
            self._set_cell_font(cells, 8)

    @staticmethod
    def _bold_header(hdr_cells, size_pt: int) -> None:
        for cell in hdr_cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.bold = True
                    run.font.size = Pt(size_pt)

    @staticmethod
    def _set_cell_font(cells, size_pt: int) -> None:
        for cell in cells:
            for paragraph in cell.paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(size_pt)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -k build_ip_table -v -p no:cacheprovider --no-cov`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/utils/isp_letter_generator.py backend/tests/test_letter_renderer.py
git commit -m "refactor: extract per-ISP IP table into _build_ip_table

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 3: `render_template_to_docx` — walk blocks to build the letter

**Files:**
- Modify: `backend/utils/isp_letter_generator.py` (add method)
- Test: `backend/tests/test_letter_renderer.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_letter_renderer.py`:

```python
from utils.letter_template import DEFAULT_TEMPLATE


def _doc_text(doc):
    return "\n".join(p.text for p in doc.paragraphs)


def test_render_substitutes_placeholders_in_text_and_list():
    case = {
        "fir_number": "201/25", "sections": "420 IPC", "fir_date": "01/02/2025",
        "police_station": "Special Cell", "complainant": "John Doe",
        "subject": "Reg info", "email_reference": "ref-1",
        "officer_name": "Insp X", "officer_designation": "IO",
        "officer_location": "Dwarka", "officer_contact": "999",
        "letter_date": "09/06/2026",
    }
    doc = ISPLetterGenerator().render_template_to_docx(
        DEFAULT_TEMPLATE, "Airtel", _sample_df(), case)
    text = _doc_text(doc)
    assert "FIR No.201/25" in text
    assert "Insp X" in text
    assert "{isp_name}" not in text          # all tokens replaced
    assert "Airtel" in text                  # isp_name injected
    # numbered list rendered
    assert "1. Details of the user" in text
    # the smart table is present with 4 cols (Airtel)
    assert len(doc.tables) == 1
    assert len(doc.tables[0].columns) == 4
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -k render_substitutes -v -p no:cacheprovider --no-cov`
Expected: FAIL with `AttributeError: ... has no attribute 'render_template_to_docx'`

- [ ] **Step 3: Write minimal implementation**

Add to `ISPLetterGenerator` in `backend/utils/isp_letter_generator.py` (the import for `substitute` goes at top of file):

```python
# add near the top imports of isp_letter_generator.py:
from utils.letter_template import substitute
```

```python
    def render_template_to_docx(self, template: dict, isp_name: str,
                                ip_data: pd.DataFrame, case_details: dict) -> Document:
        """Build a letter .docx by walking a template's blocks."""
        values = dict(case_details)
        values["isp_name"] = isp_name

        doc = Document()
        page = template.get("page", {})
        margins = page.get("margins_inches", {})
        default_font = page.get("default_font", "Calibri")
        default_size = page.get("default_size", 10)
        for section in doc.sections:
            section.top_margin = Inches(margins.get("top", 0.5))
            section.bottom_margin = Inches(margins.get("bottom", 0.5))
            section.left_margin = Inches(margins.get("left", 0.75))
            section.right_margin = Inches(margins.get("right", 0.75))

        align_map = {
            "left": WD_ALIGN_PARAGRAPH.LEFT,
            "center": WD_ALIGN_PARAGRAPH.CENTER,
            "right": WD_ALIGN_PARAGRAPH.RIGHT,
        }

        for block in template.get("blocks", []):
            btype = block.get("type")
            if btype == "text":
                p = doc.add_paragraph()
                p.alignment = align_map.get(block.get("align", "left"), WD_ALIGN_PARAGRAPH.LEFT)
                run = p.add_run(substitute(block.get("content", ""), values))
                run.bold = bool(block.get("bold"))
                run.italic = bool(block.get("italic"))
                run.font.name = block.get("font") or default_font
                run.font.size = Pt(block.get("size") or default_size)
            elif btype == "list":
                style = block.get("style", "numbered")
                for i, item in enumerate(block.get("items", []), start=1):
                    text = substitute(item, values)
                    prefix = f"{i}. " if style == "numbered" else "• "
                    p = doc.add_paragraph()
                    run = p.add_run(prefix + text)
                    run.font.name = block.get("font") or default_font
                    run.font.size = Pt(block.get("size") or default_size)
            elif btype == "ip_table":
                self._build_ip_table(doc, isp_name, ip_data)
            elif btype == "spacer":
                for _ in range(int(block.get("lines", 1))):
                    doc.add_paragraph()

        return doc
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -k render_substitutes -v -p no:cacheprovider --no-cov`
Expected: PASS (1 passed)

- [ ] **Step 5: Commit**

```bash
git add backend/utils/isp_letter_generator.py backend/tests/test_letter_renderer.py
git commit -m "feat: render ISP letter .docx from template blocks

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 4: Route `generate_letter`/`generate_all_letters` through templates

**Files:**
- Modify: `backend/utils/isp_letter_generator.py`
- Test: `backend/tests/test_letter_renderer.py`

- [ ] **Step 1: Write the failing test**

Append to `backend/tests/test_letter_renderer.py`:

```python
def test_generate_letter_defaults_to_system_template_when_none_given():
    case = {"fir_number": "5/25", "subject": "Reg info", "email_reference": "",
            "police_station": "PS", "sections": "420", "fir_date": "1/1/25",
            "complainant": "X", "officer_name": "Y", "officer_designation": "IO",
            "officer_location": "L", "officer_contact": "9", "letter_date": "1/1/26"}
    doc = ISPLetterGenerator().generate_letter("Airtel", _sample_df(), case)
    text = _doc_text(doc)
    assert "Notice u/s 94 BNSS, 2023" in text     # default content present
    assert "FIR No.5/25" in text
    assert len(doc.tables[0].columns) == 4         # Airtel table preserved
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -k defaults_to_system -v -p no:cacheprovider --no-cov`
Expected: FAIL — current `generate_letter` produces output via the old `create_letter_*` path and the signature/behavior differs (it builds from hardcoded methods, not the default template). The assertion `"FIR No.5/25"` may pass but the test pins behavior to the template path; if it passes coincidentally, proceed to Step 3 to make the implementation explicit.

- [ ] **Step 3: Write minimal implementation**

Replace the body of `generate_letter` and `generate_all_letters` in `backend/utils/isp_letter_generator.py`. Delete `create_letter_airtel`, `create_letter_vi`, `create_letter_jio` (their content now lives in the default template + `_build_ip_table`). Keep `create_jio_txt_file`, `detect_isps_from_zip`, `get_template_type`, the date/time formatters, `convert_date_to_airtel_format`, `pad_time_to_6_digits`.

```python
    def generate_letter(self, isp_name: str, ip_data: pd.DataFrame,
                        case_details: dict, template: dict = None) -> Document:
        """Generate a letter for one ISP using the given template (or the default)."""
        from utils.letter_template import DEFAULT_TEMPLATE
        return self.render_template_to_docx(template or DEFAULT_TEMPLATE,
                                            isp_name, ip_data, case_details)

    def generate_all_letters(self, zip_file_path: str, case_details: dict,
                            template: dict = None) -> bytes:
        """Generate all ISP letters from a Step-6 ZIP. Returns ZIP bytes."""
        isp_data = self.detect_isps_from_zip(zip_file_path)
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for isp_name, ip_df in isp_data.items():
                doc = self.generate_letter(isp_name, ip_df, case_details, template)
                doc_buffer = io.BytesIO()
                doc.save(doc_buffer)
                doc_buffer.seek(0)
                fir = str(case_details.get('fir_number', 'N-A')).replace('/', '-')
                zip_file.writestr(f"{isp_name}_Letter_{fir}.docx", doc_buffer.getvalue())
                if self.get_template_type(isp_name) == 'jio':
                    txt = self.create_jio_txt_file(isp_name, ip_df, case_details)
                    zip_file.writestr(f"{isp_name}_Data_{fir}.txt", txt)
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
```

- [ ] **Step 4: Run the full renderer suite**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py -v -p no:cacheprovider --no-cov`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add backend/utils/isp_letter_generator.py backend/tests/test_letter_renderer.py
git commit -m "refactor: drive letter generation from templates, drop hardcoded per-ISP methods

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase 2 — Template storage + API

### Task 5: Template service (CRUD + seed) with mongomock tests

**Files:**
- Create: `backend/services/letter_template_service.py`
- Modify: `backend/requirements.txt` (add `mongomock`)
- Test: `backend/tests/test_letter_template_service.py`

- [ ] **Step 1: Install mongomock and record it**

Run: `cd backend && .venv/bin/pip install mongomock && echo "mongomock" >> requirements.txt`
Expected: `Successfully installed mongomock-...`

- [ ] **Step 2: Write the failing test**

```python
# backend/tests/test_letter_template_service.py
import mongomock
import pytest
from services import letter_template_service as svc


@pytest.fixture()
def db():
    return mongomock.MongoClient().testdb


def test_seed_is_idempotent_and_creates_system_default(db):
    svc.seed_default_template(db)
    svc.seed_default_template(db)
    systems = list(db[svc.COLLECTION].find({"scope": "system"}))
    assert len(systems) == 1
    assert systems[0]["name"] == "IFSO Dwarka Default"


def test_user_sees_system_own_and_shared_only(db):
    svc.seed_default_template(db)
    svc.create_template(db, {"_id": "u1", "role": "investigator"},
                        {"name": "Mine", "blocks": [{"id": "t", "type": "text", "content": "hi"}]})
    svc.create_template(db, {"_id": "u2", "role": "investigator"},
                        {"name": "Theirs", "blocks": [{"id": "t", "type": "text", "content": "x"}]})
    names = {t["name"] for t in svc.list_templates(db, {"_id": "u1", "role": "investigator"})}
    assert "IFSO Dwarka Default" in names
    assert "Mine" in names
    assert "Theirs" not in names


def test_user_cannot_update_others_template(db):
    created = svc.create_template(db, {"_id": "u1", "role": "investigator"},
                                  {"name": "Mine", "blocks": [{"id": "t", "type": "text", "content": "hi"}]})
    with pytest.raises(svc.PermissionError):
        svc.update_template(db, created["id"], {"_id": "u2", "role": "investigator"},
                            {"name": "Hacked", "blocks": [{"id": "t", "type": "text", "content": "no"}]})


def test_only_admin_can_share(db):
    created = svc.create_template(db, {"_id": "u1", "role": "investigator"},
                                  {"name": "Mine", "blocks": [{"id": "t", "type": "text", "content": "hi"}]})
    with pytest.raises(svc.PermissionError):
        svc.share_template(db, created["id"], {"_id": "u1", "role": "investigator"})
    shared = svc.share_template(db, created["id"], {"_id": "admin", "role": "admin"})
    assert shared["scope"] == "shared"


def test_cannot_delete_system_template(db):
    svc.seed_default_template(db)
    sys_id = svc.list_templates(db, {"_id": "u1", "role": "investigator"})[0]["id"]
    with pytest.raises(svc.PermissionError):
        svc.delete_template(db, sys_id, {"_id": "u1", "role": "investigator"})
```

- [ ] **Step 3: Run test to verify it fails**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_template_service.py -v -p no:cacheprovider --no-cov`
Expected: FAIL with `ModuleNotFoundError: No module named 'services.letter_template_service'`

- [ ] **Step 4: Write minimal implementation**

```python
# backend/services/letter_template_service.py
"""CRUD + seeding for ISP letter templates (collection: letter_templates)."""
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from utils.letter_template import LetterTemplate, DEFAULT_TEMPLATE

COLLECTION = "letter_templates"


class PermissionError(Exception):
    """Raised when a user is not allowed to perform the action."""


class NotFoundError(Exception):
    """Raised when a template does not exist or is not visible."""


def _to_oid(tid: str):
    try:
        return ObjectId(tid)
    except (InvalidId, TypeError):
        raise NotFoundError("Template not found")


def _serialize(doc: dict) -> dict:
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def seed_default_template(db) -> None:
    """Insert the system default template once (idempotent)."""
    if db[COLLECTION].find_one({"scope": "system"}):
        return
    doc = dict(DEFAULT_TEMPLATE)
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    db[COLLECTION].insert_one(doc)


def list_templates(db, user: dict) -> list:
    uid = str(user["_id"])
    cursor = db[COLLECTION].find({"$or": [
        {"scope": "system"}, {"scope": "shared"}, {"owner_id": uid},
    ]})
    return [_serialize(d) for d in cursor]


def get_template(db, tid: str, user: dict) -> dict:
    doc = db[COLLECTION].find_one({"_id": _to_oid(tid)})
    if not doc:
        raise NotFoundError("Template not found")
    uid = str(user["_id"])
    if doc.get("scope") in ("system", "shared") or doc.get("owner_id") == uid:
        return _serialize(doc)
    raise NotFoundError("Template not found")


def _validate(payload: dict, owner_id, scope: str) -> dict:
    tpl = LetterTemplate.model_validate({**payload, "owner_id": owner_id, "scope": scope})
    return tpl.model_dump()


def create_template(db, user: dict, payload: dict) -> dict:
    uid = str(user["_id"])
    doc = _validate(payload, uid, "user")
    doc["created_at"] = doc["updated_at"] = datetime.now(timezone.utc)
    res = db[COLLECTION].insert_one(doc)
    return _serialize(db[COLLECTION].find_one({"_id": res.inserted_id}))


def update_template(db, tid: str, user: dict, payload: dict) -> dict:
    doc = db[COLLECTION].find_one({"_id": _to_oid(tid)})
    if not doc:
        raise NotFoundError("Template not found")
    uid = str(user["_id"])
    is_admin = user.get("role") == "admin"
    if doc.get("scope") == "system" and not is_admin:
        raise PermissionError("Cannot edit the system template")
    if doc.get("scope") == "user" and doc.get("owner_id") != uid:
        raise PermissionError("Cannot edit another user's template")
    if doc.get("scope") == "shared" and not is_admin:
        raise PermissionError("Only an admin can edit a shared template")
    updated = _validate(payload, doc.get("owner_id"), doc.get("scope"))
    updated["created_at"] = doc.get("created_at")
    updated["updated_at"] = datetime.now(timezone.utc)
    db[COLLECTION].replace_one({"_id": doc["_id"]}, updated)
    return _serialize(db[COLLECTION].find_one({"_id": doc["_id"]}))


def delete_template(db, tid: str, user: dict) -> None:
    doc = db[COLLECTION].find_one({"_id": _to_oid(tid)})
    if not doc:
        raise NotFoundError("Template not found")
    uid = str(user["_id"])
    if doc.get("scope") == "system":
        raise PermissionError("Cannot delete the system template")
    if doc.get("scope") == "shared" and user.get("role") != "admin":
        raise PermissionError("Only an admin can delete a shared template")
    if doc.get("scope") == "user" and doc.get("owner_id") != uid:
        raise PermissionError("Cannot delete another user's template")
    db[COLLECTION].delete_one({"_id": doc["_id"]})


def share_template(db, tid: str, user: dict) -> dict:
    if user.get("role") != "admin":
        raise PermissionError("Admin privileges required")
    doc = db[COLLECTION].find_one({"_id": _to_oid(tid)})
    if not doc:
        raise NotFoundError("Template not found")
    db[COLLECTION].update_one({"_id": doc["_id"]},
                              {"$set": {"scope": "shared", "updated_at": datetime.now(timezone.utc)}})
    return _serialize(db[COLLECTION].find_one({"_id": doc["_id"]}))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd backend && .venv/bin/python -m pytest tests/test_letter_template_service.py -v -p no:cacheprovider --no-cov`
Expected: PASS (5 passed)

- [ ] **Step 6: Commit**

```bash
git add backend/services/letter_template_service.py backend/tests/test_letter_template_service.py backend/requirements.txt
git commit -m "feat: add letter template service with CRUD, seeding, and permissions

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 6: Template CRUD router

**Files:**
- Create: `backend/routers/letter_templates.py`
- Modify: `backend/main.py` (include router)

- [ ] **Step 1: Write the router**

```python
# backend/routers/letter_templates.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ValidationError

from core.db import get_db
from routers.auth_secure import get_current_user
from services import letter_template_service as svc

router = APIRouter()


class TemplatePayload(BaseModel):
    name: str
    page: dict | None = None
    blocks: list


def _handle(fn, *args):
    try:
        return fn(*args)
    except svc.NotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    except svc.PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/")
async def list_templates(user=Depends(get_current_user), db=Depends(get_db)):
    return {"success": True, "templates": svc.list_templates(db, user)}


@router.get("/{tid}")
async def get_template(tid: str, user=Depends(get_current_user), db=Depends(get_db)):
    return {"success": True, "template": _handle(svc.get_template, db, tid, user)}


@router.post("/")
async def create_template(payload: TemplatePayload, user=Depends(get_current_user), db=Depends(get_db)):
    return {"success": True, "template": _handle(svc.create_template, db, user, payload.model_dump(exclude_none=True))}


@router.put("/{tid}")
async def update_template(tid: str, payload: TemplatePayload, user=Depends(get_current_user), db=Depends(get_db)):
    return {"success": True, "template": _handle(svc.update_template, db, tid, user, payload.model_dump(exclude_none=True))}


@router.delete("/{tid}")
async def delete_template(tid: str, user=Depends(get_current_user), db=Depends(get_db)):
    _handle(svc.delete_template, db, tid, user)
    return {"success": True}


@router.post("/{tid}/share")
async def share_template(tid: str, user=Depends(get_current_user), db=Depends(get_db)):
    return {"success": True, "template": _handle(svc.share_template, db, tid, user)}
```

- [ ] **Step 2: Register the router in `backend/main.py`**

Add to the imports line (the `from routers import ...`) the name `letter_templates`, and add this include near the other `app.include_router(...)` calls (after the `fir_management` include):

```python
app.include_router(letter_templates.router, prefix="/api/letter-templates", tags=["📝 Letter Templates"])
```

- [ ] **Step 3: Verify the app imports and routes are registered**

Run: `cd backend && .venv/bin/python -c "import main; paths=[r.path for r in main.app.routes]; print([p for p in paths if 'letter-templates' in p])"`
Expected: a list containing `/api/letter-templates/`, `/api/letter-templates/{tid}`, `/api/letter-templates/{tid}/share`

- [ ] **Step 4: Commit**

```bash
git add backend/routers/letter_templates.py backend/main.py
git commit -m "feat: add /api/letter-templates CRUD router

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 7: Seed on startup + thread `template_id` into generate endpoints

**Files:**
- Modify: `backend/main.py` (seed in `startup_event`)
- Modify: `backend/routers/ip_lookup.py:1045`
- Modify: `backend/routers/ipdr_processing.py:731`

- [ ] **Step 1: Seed default template on startup**

In `backend/main.py`, inside `startup_event()` after the index-creation block, add:

```python
    # Seed the default ISP letter template (idempotent)
    try:
        from core.db import get_db as _get_sync_db
        from services.letter_template_service import seed_default_template
        seed_default_template(_get_sync_db())
        logger.info("✅ Default letter template ready")
    except Exception as e:
        logger.warning(f"⚠️ Letter template seeding skipped: {e}")
```

- [ ] **Step 2: Add `template_id` to `/api/generate-isp-letters`**

In `backend/routers/ip_lookup.py`, modify `generate_isp_letters` (starts at line 1045):
- Add params to the signature: `template_id: Optional[str] = Form(None)`, `current_user=Depends(get_current_user)`, `db=Depends(get_db)`. (Confirm `from typing import Optional`, `get_current_user`, and `get_db` are imported at the top of the file — `get_current_user` already is; add the others if missing.)
- After building `case_details` and before `generator.generate_all_letters(...)`, resolve the template:

```python
        template = None
        if template_id:
            from services.letter_template_service import get_template, NotFoundError
            try:
                template = get_template(db, template_id, current_user)
            except NotFoundError:
                template = None  # fall back to system default
        letters_zip = generator.generate_all_letters(str(temp_zip_path), case_details, template)
```

- [ ] **Step 3: Add `template_id` to the run-based generate in `ipdr_processing.py`**

In `backend/routers/ipdr_processing.py`, locate `generate_isp_letters_from_run` (around line 731). Add `template_id: Optional[str] = Form(None)` to its signature (ensure it also depends on `get_current_user` and `get_db`; follow the pattern used by neighbouring endpoints in that file). Where it calls the generator (`generate_all_letters` or `generate_letter`), resolve and pass `template` exactly as in Step 2.

- [ ] **Step 4: Verify the app still imports**

Run: `cd backend && .venv/bin/python -c "import main; print('ok')"`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/routers/ip_lookup.py backend/routers/ipdr_processing.py
git commit -m "feat: seed default template on startup and accept template_id when generating letters

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Phase 3 — Frontend builder + wiring

> Frontend has no JS test runner configured (no `test` script in `frontend/package.json`).
> Verify these tasks by running the app and exercising the UI in a browser (commands in
> each task), not via unit tests.

### Task 8: Template API client + types

**Files:**
- Create: `frontend/src/lib/templates.ts`

- [ ] **Step 1: Write the client**

```ts
// frontend/src/lib/templates.ts
import { apiRequest } from './api'

export type Align = 'left' | 'center' | 'right'
export type Block =
  | { id: string; type: 'text'; content: string; align: Align; bold: boolean; italic: boolean; font?: string; size?: number }
  | { id: string; type: 'list'; style: 'numbered' | 'bullet'; items: string[]; font?: string; size?: number }
  | { id: string; type: 'ip_table' }
  | { id: string; type: 'spacer'; lines: number }

export type LetterTemplate = {
  id: string
  name: string
  owner_id: string | null
  scope: 'system' | 'user' | 'shared'
  page: { margins_inches: Record<string, number>; default_font: string; default_size: number }
  blocks: Block[]
}

export const PLACEHOLDERS = [
  'fir_number', 'fir_date', 'letter_date', 'police_station', 'sections',
  'complainant', 'isp_name', 'officer_name', 'officer_designation',
  'officer_location', 'officer_contact', 'subject', 'email_reference',
] as const

export async function listTemplates(token: string) {
  return apiRequest<{ templates: LetterTemplate[] }>('/api/letter-templates/', { method: 'GET' }, token)
}
export async function getTemplate(token: string, id: string) {
  return apiRequest<{ template: LetterTemplate }>(`/api/letter-templates/${id}`, { method: 'GET' }, token)
}
export async function createTemplate(token: string, body: Pick<LetterTemplate, 'name' | 'page' | 'blocks'>) {
  return apiRequest<{ template: LetterTemplate }>('/api/letter-templates/', { method: 'POST', body: JSON.stringify(body) }, token)
}
export async function updateTemplate(token: string, id: string, body: Pick<LetterTemplate, 'name' | 'page' | 'blocks'>) {
  return apiRequest<{ template: LetterTemplate }>(`/api/letter-templates/${id}`, { method: 'PUT', body: JSON.stringify(body) }, token)
}
export async function deleteTemplate(token: string, id: string) {
  return apiRequest(`/api/letter-templates/${id}`, { method: 'DELETE' }, token)
}
export async function shareTemplate(token: string, id: string) {
  return apiRequest<{ template: LetterTemplate }>(`/api/letter-templates/${id}/share`, { method: 'POST' }, token)
}

export function newBlock(type: Block['type']): Block {
  const id = Math.random().toString(36).slice(2, 10)
  if (type === 'text') return { id, type, content: '', align: 'left', bold: false, italic: false }
  if (type === 'list') return { id, type, style: 'numbered', items: [''] }
  if (type === 'spacer') return { id, type, lines: 1 }
  return { id, type: 'ip_table' }
}
```

- [ ] **Step 2: Verify it type-checks (build)**

Run: `cd frontend && npx tsc --noEmit`
Expected: no errors referencing `templates.ts`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/templates.ts
git commit -m "feat: add letter-template API client and types

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 9: Template Builder page (block list + editor + live preview)

**Files:**
- Create: `frontend/src/pages/TemplateBuilderPage.tsx`
- Modify: `frontend/src/App.tsx` (route)
- Modify: `frontend/src/components/Layout.tsx` (nav link)

- [ ] **Step 1: Create the page**

Create `frontend/src/pages/TemplateBuilderPage.tsx`. It must:
- Load templates on mount via `listTemplates`; default-select "IFSO Dwarka Default".
- Show a **block list** (left) with reorder up/down buttons (▲/▼), delete (✕), and `+ Add block` menu (Text / List / IP Table / Spacer). Disable adding a 2nd `ip_table`.
- Show a **selected-block editor** below the list: for `text` — a textarea bound to `content`, align radios, Bold/Italic toggles, font input, size number, and an **Insert placeholder** `<select>` that appends `{token}` to the content at the end; for `list` — style radio + one input per item with add/remove item; for `spacer` — a `lines` number; for `ip_table` — read-only note "Columns auto-format per ISP".
- Show a **live preview** (right): an A4-ish white panel that maps blocks to HTML — `text` → `<p>` with `textAlign`, `fontWeight`, `fontStyle`, `fontFamily`, `fontSize` from the block; `list` → `<ol>`/`<ul>`; `ip_table` → a sample `<table>` whose columns depend on a small ISP `<select>` (Airtel = 4 cols, Jio/Vi = 6 cols) using the same headers as the backend; `spacer` → empty vertical space. Placeholders render literally (e.g. `{fir_number}`) in the preview.
- Top bar: template `<select>`, **Save** (PUT if `scope==='user'` & owned else disabled), **Save As…** (prompt name → `createTemplate`), **Duplicate**, **Delete** (only own), **Share** (only when `user.role==='admin'`).

```tsx
// frontend/src/pages/TemplateBuilderPage.tsx
import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../lib/auth'
import {
  Block, LetterTemplate, PLACEHOLDERS, newBlock,
  listTemplates, createTemplate, updateTemplate, deleteTemplate, shareTemplate,
} from '../lib/templates'

const SAMPLE_ROW = { type: 'IPV4', ip: '1.2.3.4', fromDate: '28-Jan-2025', fromTime: '14:30:25', toDate: '28-Jan-2025', toTime: '15:30:25' }

function PreviewTable({ isp }: { isp: string }) {
  const airtel = isp.toLowerCase().includes('airtel')
  if (airtel) {
    return (
      <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 11 }}>
        <thead><tr>{['Type', 'Search Value', 'From Date (DD-MMM-YYYY HH24:MI:SS)', 'To Date (DD-MMM-YYYY HH24:MI:SS)'].map(h =>
          <th key={h} style={{ border: '1px solid #888', padding: 4 }}>{h}</th>)}</tr></thead>
        <tbody><tr>{[SAMPLE_ROW.type, SAMPLE_ROW.ip, `${SAMPLE_ROW.fromDate} ${SAMPLE_ROW.fromTime}`, `${SAMPLE_ROW.toDate} ${SAMPLE_ROW.toTime}`].map((c, i) =>
          <td key={i} style={{ border: '1px solid #888', padding: 4 }}>{c}</td>)}</tr></tbody>
      </table>
    )
  }
  const jio = isp.toLowerCase().includes('jio') || isp.toLowerCase().includes('reliance')
  const dateHdr = jio ? 'YYYYMMDD' : 'DD:MM:YYYY'
  const timeHdr = jio ? 'HHMMSS (IST)' : 'HH:MM:SS (IST)'
  return (
    <table style={{ borderCollapse: 'collapse', width: '100%', fontSize: 11 }}>
      <thead><tr>{['Type', 'Search Value', `From Date ${dateHdr}`, `From Time ${timeHdr}`, `To Date ${dateHdr}`, `To Time ${timeHdr}`].map(h =>
        <th key={h} style={{ border: '1px solid #888', padding: 4 }}>{h}</th>)}</tr></thead>
      <tbody><tr>{[SAMPLE_ROW.type, SAMPLE_ROW.ip, jio ? '20250128' : '28:01:2025', jio ? '143025' : '14:30:25', jio ? '20250128' : '28:01:2025', jio ? '153025' : '15:30:25'].map((c, i) =>
        <td key={i} style={{ border: '1px solid #888', padding: 4 }}>{c}</td>)}</tr></tbody>
    </table>
  )
}

function BlockPreview({ block, isp }: { block: Block; isp: string }) {
  if (block.type === 'text') {
    return <p style={{ textAlign: block.align, fontWeight: block.bold ? 700 : 400, fontStyle: block.italic ? 'italic' : 'normal', fontFamily: block.font || 'Calibri', fontSize: (block.size || 10) + 1, whiteSpace: 'pre-wrap', margin: '2px 0' }}>{block.content || ' '}</p>
  }
  if (block.type === 'list') {
    const Tag = block.style === 'numbered' ? 'ol' : 'ul'
    return <Tag style={{ fontSize: (block.size || 10) + 1, margin: '4px 0 4px 20px' }}>{block.items.map((it, i) => <li key={i}>{it}</li>)}</Tag>
  }
  if (block.type === 'ip_table') return <div style={{ margin: '6px 0' }}><PreviewTable isp={isp} /></div>
  return <div style={{ height: (block.lines || 1) * 14 }} />
}

export default function TemplateBuilderPage() {
  const { token, user } = useAuth()
  const [templates, setTemplates] = useState<LetterTemplate[]>([])
  const [selId, setSelId] = useState<string>('')
  const [draft, setDraft] = useState<LetterTemplate | null>(null)
  const [selBlock, setSelBlock] = useState<string>('')
  const [previewIsp, setPreviewIsp] = useState('Airtel')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    listTemplates(token).then(r => {
      const list = r.data?.templates ?? []
      setTemplates(list)
      const def = list.find(t => t.name === 'IFSO Dwarka Default') || list[0]
      if (def) { setSelId(def.id); setDraft(structuredClone(def)) }
    })
  }, [token])

  const onSelect = (id: string) => {
    const t = templates.find(x => x.id === id)
    if (t) { setSelId(id); setDraft(structuredClone(t)); setSelBlock('') }
  }

  const isOwn = draft?.scope === 'user' && draft?.owner_id === String(user?.id)
  const block = useMemo(() => draft?.blocks.find(b => b.id === selBlock), [draft, selBlock])

  const mutate = (fn: (d: LetterTemplate) => void) => setDraft(d => { if (!d) return d; const c = structuredClone(d); fn(c); return c })
  const updateBlock = (patch: Partial<Block>) => mutate(d => {
    const b = d.blocks.find(x => x.id === selBlock); if (b) Object.assign(b, patch)
  })
  const move = (i: number, dir: -1 | 1) => mutate(d => {
    const j = i + dir; if (j < 0 || j >= d.blocks.length) return
    ;[d.blocks[i], d.blocks[j]] = [d.blocks[j], d.blocks[i]]
  })
  const addBlock = (type: Block['type']) => {
    if (type === 'ip_table' && draft?.blocks.some(b => b.type === 'ip_table')) { setMsg('Only one IP table allowed'); return }
    mutate(d => { d.blocks.push(newBlock(type)) })
  }
  const removeBlock = (id: string) => mutate(d => { d.blocks = d.blocks.filter(b => b.id !== id) })

  const body = (d: LetterTemplate) => ({ name: d.name, page: d.page, blocks: d.blocks })
  const save = async () => {
    if (!draft || !isOwn) return
    const r = await updateTemplate(token, draft.id, body(draft))
    setMsg(r.success ? 'Saved' : (r.error || 'Save failed'))
    if (r.success) (await listTemplates(token)).data && setTemplates((await listTemplates(token)).data!.templates)
  }
  const saveAs = async () => {
    if (!draft) return
    const name = window.prompt('New template name', draft.name + ' (copy)')
    if (!name) return
    const r = await createTemplate(token, { ...body(draft), name })
    if (r.success && r.data) { const list = (await listTemplates(token)).data!.templates; setTemplates(list); setSelId(r.data.template.id); setDraft(structuredClone(r.data.template)) }
    setMsg(r.success ? 'Created' : (r.error || 'Failed'))
  }
  const del = async () => {
    if (!draft || !isOwn || !window.confirm('Delete this template?')) return
    await deleteTemplate(token, draft.id)
    const list = (await listTemplates(token)).data!.templates; setTemplates(list)
    const def = list.find(t => t.name === 'IFSO Dwarka Default') || list[0]
    if (def) { setSelId(def.id); setDraft(structuredClone(def)) }
  }
  const share = async () => { if (draft) { await shareTemplate(token, draft.id); setMsg('Shared with department') } }

  if (!draft) return <section><p className="muted">Loading templates…</p></section>

  return (
    <section>
      <div style={{ marginBottom: 16 }}>
        <h1>ISP Letter Template Builder</h1>
        <p className="muted" style={{ fontSize: 13, margin: 0 }}>Design your own letter layout. The IP table always auto-formats per ISP.</p>
      </div>

      <div style={{ display: 'flex', gap: 10, alignItems: 'center', marginBottom: 14, flexWrap: 'wrap' }}>
        <select value={selId} onChange={e => onSelect(e.target.value)} style={{ minWidth: 220 }}>
          {templates.map(t => <option key={t.id} value={t.id}>{t.name}{t.scope === 'system' ? ' (default)' : t.scope === 'shared' ? ' (shared)' : ''}</option>)}
        </select>
        <button className="btn btn-primary" disabled={!isOwn} onClick={save}>Save</button>
        <button className="btn" onClick={saveAs}>Save As…</button>
        <button className="btn" onClick={saveAs}>Duplicate</button>
        <button className="btn btn-ghost" disabled={!isOwn} onClick={del}>Delete</button>
        {user?.role === 'admin' && <button className="btn btn-ghost" onClick={share}>Share</button>}
        {msg && <span className="muted" style={{ fontSize: 12 }}>{msg}</span>}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: 16, alignItems: 'start' }}>
        <div className="card" style={{ marginBottom: 0 }}>
          <input value={draft.name} onChange={e => mutate(d => { d.name = e.target.value })} disabled={!isOwn && draft.scope !== 'user'} style={{ marginBottom: 10, width: '100%' }} />
          <div style={{ display: 'grid', gap: 4, marginBottom: 10 }}>
            {draft.blocks.map((b, i) => (
              <div key={b.id} onClick={() => setSelBlock(b.id)} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '6px 8px', borderRadius: 6, cursor: 'pointer', border: '1px solid var(--border)', background: selBlock === b.id ? 'rgba(0,229,255,0.08)' : 'transparent' }}>
                <span style={{ flex: 1, fontSize: 12 }}>{b.type === 'text' ? `Text · ${(b as any).content.slice(0, 20) || 'empty'}` : b.type === 'list' ? `List (${(b as any).items.length})` : b.type === 'ip_table' ? 'IP Table (auto)' : `Spacer (${(b as any).lines})`}</span>
                <button className="btn btn-ghost" style={{ padding: '0 6px' }} onClick={e => { e.stopPropagation(); move(i, -1) }}>▲</button>
                <button className="btn btn-ghost" style={{ padding: '0 6px' }} onClick={e => { e.stopPropagation(); move(i, 1) }}>▼</button>
                <button className="btn btn-ghost" style={{ padding: '0 6px' }} onClick={e => { e.stopPropagation(); removeBlock(b.id) }}>✕</button>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
            {(['text', 'list', 'ip_table', 'spacer'] as const).map(t => (
              <button key={t} className="btn" style={{ fontSize: 11 }} onClick={() => addBlock(t)}>+ {t}</button>
            ))}
          </div>

          {block && (
            <div style={{ marginTop: 14, borderTop: '1px solid var(--border)', paddingTop: 12 }}>
              {block.type === 'text' && (
                <>
                  <textarea value={block.content} onChange={e => updateBlock({ content: e.target.value } as any)} rows={4} style={{ width: '100%' }} />
                  <div style={{ display: 'flex', gap: 8, marginTop: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    {(['left', 'center', 'right'] as const).map(a => (
                      <label key={a} style={{ fontSize: 12 }}><input type="radio" checked={block.align === a} onChange={() => updateBlock({ align: a } as any)} /> {a}</label>
                    ))}
                    <label style={{ fontSize: 12 }}><input type="checkbox" checked={block.bold} onChange={e => updateBlock({ bold: e.target.checked } as any)} /> Bold</label>
                    <label style={{ fontSize: 12 }}><input type="checkbox" checked={block.italic} onChange={e => updateBlock({ italic: e.target.checked } as any)} /> Italic</label>
                    <input placeholder="font" value={block.font || ''} onChange={e => updateBlock({ font: e.target.value } as any)} style={{ width: 90 }} />
                    <input type="number" placeholder="size" value={block.size || ''} onChange={e => updateBlock({ size: Number(e.target.value) || undefined } as any)} style={{ width: 64 }} />
                    <select onChange={e => { if (e.target.value) { updateBlock({ content: block.content + `{${e.target.value}}` } as any); e.target.value = '' } }}>
                      <option value="">Insert placeholder…</option>
                      {PLACEHOLDERS.map(p => <option key={p} value={p}>{p}</option>)}
                    </select>
                  </div>
                </>
              )}
              {block.type === 'list' && (
                <>
                  <div style={{ marginBottom: 6 }}>
                    {(['numbered', 'bullet'] as const).map(s => <label key={s} style={{ fontSize: 12, marginRight: 10 }}><input type="radio" checked={block.style === s} onChange={() => updateBlock({ style: s } as any)} /> {s}</label>)}
                  </div>
                  {block.items.map((it, idx) => (
                    <div key={idx} style={{ display: 'flex', gap: 6, marginBottom: 4 }}>
                      <input value={it} onChange={e => updateBlock({ items: block.items.map((x, k) => k === idx ? e.target.value : x) } as any)} style={{ flex: 1 }} />
                      <button className="btn btn-ghost" onClick={() => updateBlock({ items: block.items.filter((_, k) => k !== idx) } as any)}>✕</button>
                    </div>
                  ))}
                  <button className="btn" style={{ fontSize: 11 }} onClick={() => updateBlock({ items: [...block.items, ''] } as any)}>+ item</button>
                </>
              )}
              {block.type === 'spacer' && (
                <label style={{ fontSize: 12 }}>Lines <input type="number" value={block.lines} onChange={e => updateBlock({ lines: Number(e.target.value) || 1 } as any)} style={{ width: 64 }} /></label>
              )}
              {block.type === 'ip_table' && <p className="muted" style={{ fontSize: 12 }}>Columns auto-format per ISP (Airtel 4-col, Jio/Vi 6-col). Not editable.</p>}
            </div>
          )}
        </div>

        <div className="card" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <strong style={{ fontSize: 13 }}>Live Preview</strong>
            <label style={{ fontSize: 12 }}>IP table as: <select value={previewIsp} onChange={e => setPreviewIsp(e.target.value)}><option>Airtel</option><option>Jio</option><option>Vodafone Idea</option></select></label>
          </div>
          <div style={{ background: '#fff', color: '#000', padding: '32px 40px', minHeight: 600, boxShadow: '0 0 0 1px var(--border)' }}>
            {draft.blocks.map(b => <BlockPreview key={b.id} block={b} isp={previewIsp} />)}
          </div>
          <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>Preview is an approximation. The generated .docx is the final document.</p>
        </div>
      </div>
    </section>
  )
}
```

- [ ] **Step 2: Add the route in `frontend/src/App.tsx`**

Import the page at the top with the other page imports:

```tsx
import TemplateBuilderPage from './pages/TemplateBuilderPage'
```

Add this route just after the `/isp-letters` route (line ~62):

```tsx
        <Route path="/isp-letters/templates" element={<ProtectedLayout><TemplateBuilderPage /></ProtectedLayout>} />
```

- [ ] **Step 3: Add a nav link in `frontend/src/components/Layout.tsx`**

Find the nav items list (the existing entries like ISP Letters). Add an entry pointing to `/isp-letters/templates` labelled "Letter Templates", following the exact shape of the surrounding nav-item objects/JSX in that file.

- [ ] **Step 4: Build + manual verify**

Run: `cd frontend && npx tsc --noEmit` → expect no errors.
Then with backend + frontend running (backend on :8000, `cd frontend && npm run dev`), open `http://localhost:3001/isp-letters/templates`, confirm: the default template loads, the preview shows the letter, adding/reordering/deleting blocks updates the preview, the IP-table ISP selector switches 4↔6 columns, and "Save As…" creates a new template that appears in the dropdown.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/TemplateBuilderPage.tsx frontend/src/App.tsx frontend/src/components/Layout.tsx
git commit -m "feat: ISP letter template builder page with live preview

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

### Task 10: Template selector on the letter-generation pages

**Files:**
- Modify: `frontend/src/pages/IspLettersCatalogPage.tsx`
- Modify: `frontend/src/pages/IspLettersPage.tsx`

- [ ] **Step 1: Add a template selector + send `template_id` (Catalog page)**

In `frontend/src/pages/IspLettersCatalogPage.tsx`:
- Import `listTemplates, LetterTemplate` from `../lib/templates`.
- Add state: `const [templates, setTemplates] = useState<LetterTemplate[]>([])` and `const [templateId, setTemplateId] = useState('')`.
- On mount (extend the existing data-loading `useEffect`, or add one): `listTemplates(token).then(r => { const list = r.data?.templates ?? []; setTemplates(list); setTemplateId((list.find(t => t.name === 'IFSO Dwarka Default') || list[0])?.id ?? '') })`.
- In the letter form, add a `<select>` bound to `templateId` listing `templates` (label each option `t.name`), with a label "Letter template".
- Wherever the page builds the `FormData`/body for the generate request, add `fd.append('template_id', templateId)` (or include `template_id` in the JSON body, matching how that request is currently sent).

- [ ] **Step 2: Same for the standalone `IspLettersPage.tsx`**

Apply the identical changes in `frontend/src/pages/IspLettersPage.tsx`: load templates, add the selector, and `fd.append('template_id', templateId)` inside the `generate` handler before the `fetch` to `/api/generate-isp-letters`. Leave `FIXED_FIELDS` being sent as-is (the backend default template ignores unused fields), so behavior is unchanged when the default template is selected.

- [ ] **Step 3: Build + manual verify end-to-end**

Run: `cd frontend && npx tsc --noEmit` → expect no errors.
With both servers running, log in, open ISP Letters, pick the default template, generate, and confirm the downloaded `.docx` matches today's letter. Then create a custom template in the builder (e.g. change the office header text), select it on the ISP Letters page, generate, and confirm the `.docx` reflects the change while the IP table columns remain correct per ISP.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/IspLettersCatalogPage.tsx frontend/src/pages/IspLettersPage.tsx
git commit -m "feat: choose a letter template when generating ISP letters

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
```

---

## Final verification

- [ ] **Backend suite green:** `cd backend && .venv/bin/python -m pytest tests/test_letter_renderer.py tests/test_letter_template_service.py -v -p no:cacheprovider --no-cov` → all pass.
- [ ] **App boots:** `cd backend && .venv/bin/python -c "import main; print('ok')"` → `ok`.
- [ ] **Frontend type-checks:** `cd frontend && npx tsc --noEmit` → no errors.
- [ ] **Manual smoke (from the `run` flow):** generate with the default template (output unchanged), then with a custom template (reflects edits, IP table still telco-correct per ISP), and confirm a non-admin cannot edit the system/shared template (Save disabled; API returns 403).

## Notes for the implementer

- Tests run with `--no-cov` to bypass the repo's default `--cov=routers.ipdr_processing` addopts, and `-p no:cacheprovider` to avoid cache writes; the renderer/service tests don't touch that coverage target.
- The service tests use `mongomock` so they never hit MongoDB Atlas.
- `generate_letter`'s signature is `(isp_name, ip_data, case_details, template=None)`. Note the pre-existing call in `routers/auto_steps_6_7.py:194` passes args in the order `(isp_df, isp_name, case_details)` — that call site is already inconsistent with the old signature and is out of scope; do not "fix" it unless a task fails because of it.
