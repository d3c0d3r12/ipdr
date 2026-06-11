# Upload .docx as ISP Letter Template — Design

**Date:** 2026-06-11
**Status:** Approved (design)
**Extends:** `2026-06-09-isp-letter-template-builder-design.md`

## Problem

Officers often already have a Word letter they want to use. Today templates can only
be built block-by-block in the UI. They want to **upload a `.docx`** and have letters
generate from it — either used verbatim, or converted into the editable block template.

## Goals

- On the Template Builder page, an **Upload .docx** action with two modes:
  - **Use as-is** (`raw`): store the Word file; generate by token-substitution + IP-table injection, preserving the file's exact formatting.
  - **Convert to blocks** (`convert`): parse the docx into the existing block model so it can be previewed/edited.
- Uploaded templates appear in the template list/dropdown like any other and work in the existing generate flow (`template_id`).

## Non-Goals

- No live HTML preview for `raw` docx templates (Word formatting is preserved exactly; approximating it in HTML adds risk for no benefit).
- No editing of a `raw` docx's body in-app (edit happens in Word; re-upload to update). Convert-to-blocks is the editable path.
- No `.doc` (legacy binary) support — `.docx` only.

## Data Model

`LetterTemplate` (in `backend/utils/letter_template.py`) gains:
- `kind: Literal["blocks", "docx"] = "blocks"` — backward compatible; existing docs default to `blocks`.
- `docx_b64: Optional[str] = None` — base64 of the uploaded `.docx` (only for `kind == "docx"`).

Validation changes:
- The "at most one `ip_table`" rule applies only when `kind == "blocks"`.
- For `kind == "docx"`, `blocks` may be empty and `docx_b64` must be present.

The service layer (`letter_template_service.py`) stores/serves these fields unchanged
(it already persists the validated `model_dump()`).

## Backend Rendering

In `backend/utils/isp_letter_generator.py`:

- **`render_docx_template(docx_bytes, isp_name, ip_data, case_details) -> Document`:**
  1. `Document(io.BytesIO(docx_bytes))`.
  2. Build `values = {**case_details, "isp_name": isp_name}`.
  3. Substitute `{token}` in every paragraph (token may span runs → operate on each paragraph's full text; if a token is found, rewrite the paragraph's runs: set first run text to the substituted full text, clear the rest — preserves the first run's font). Apply to paragraphs in body AND inside table cells.
  4. Locate the IP-table marker: the first paragraph whose stripped text == `{ip_table}`. Insert the per-ISP table (via `_build_ip_table`) immediately before that paragraph, then remove the marker paragraph. If no marker exists, append the table at the end of the document.
  5. Return the `Document`.

- **`generate_letter(isp_name, ip_data, case_details, template=None)`** routes by kind:
  - `template` present and `template.get("kind") == "docx"` and has `docx_b64` → `render_docx_template(base64.b64decode(docx_b64), ...)`.
  - else → existing `render_template_to_docx(template or DEFAULT_TEMPLATE, ...)`.

## docx → blocks parser

In a new module `backend/utils/docx_import.py`:

- **`parse_docx_to_blocks(docx_bytes) -> list[dict]`:** iterate the document body in order:
  - Paragraph in a list style (style name contains "List Number"/"List Bullet" or has numbering) → append its text as an item to the current open `list` block (numbered vs bullet by style); a non-list paragraph closes any open list block.
  - Other non-empty paragraph → `text` block: `align` from `paragraph.alignment` (LEFT/CENTER/RIGHT→our enum, default left), `bold`/`italic`/`font`/`size` from the first run if present.
  - Empty paragraph → `spacer` (lines: 1).
  - First table encountered → one `ip_table` block; ignore subsequent tables (telco table is generated, not copied).
  - Each block gets a short unique `id`.
  - Result is a list of block dicts suitable for `LetterTemplate(blocks=...)`.

Best-effort: complex Word features (images, text boxes, nested tables) are dropped; the user can adjust in the builder.

## API

New endpoint in `backend/routers/letter_templates.py`:

- **`POST /api/letter-templates/upload-docx`** (multipart/form-data; `Depends(get_current_user)`, `Depends(get_db)`):
  - `file: UploadFile` — must end `.docx` and be a valid docx (else 400/422).
  - `name: str = Form(...)`.
  - `mode: str = Form("raw")` — `raw` or `convert`.
  - Reject if size > `MAX_UPLOAD_SIZE` (415/413) — reuse existing config.
  - `raw` → `svc.create_template(db, user, {"name": name, "kind": "docx", "docx_b64": b64, "blocks": []})`.
  - `convert` → `blocks = parse_docx_to_blocks(bytes)`; `svc.create_template(db, user, {"name": name, "kind": "blocks", "blocks": blocks})`.
  - Returns `{"success": True, "template": <created>}`.
  - python-docx raising on a bad file → caught → HTTP 422 "Invalid .docx file".

## Frontend (Template Builder page)

`frontend/src/lib/templates.ts`:
- Extend `LetterTemplate` type with `kind: 'blocks' | 'docx'` and `docx_b64?: string`.
- Add `uploadDocxTemplate(token, file, name, mode)` posting multipart to `/api/letter-templates/upload-docx`.

`frontend/src/pages/TemplateBuilderPage.tsx`:
- Add an **Upload .docx** button in the top bar → opens a small inline panel: file input (`accept=".docx"`), name input, mode radios (Use as-is / Convert to editable blocks), Upload button. On success, refresh list and select the new template.
- When the selected template has `kind === 'docx'`: hide the block list/editor and show a notice card — *"Uploaded Word file, rendered as-is. Tokens like `{fir_number}`, `{officer_name}` and `{ip_table}` are filled when letters are generated."* Plus a short list of supported tokens. (Delete/Save-As still available; block editing/preview disabled.)
- `convert` results are normal `blocks` templates → full editor/preview as today.

No change needed to `IspLettersCatalogPage`/`IspLettersPage` — they already send `template_id`, and the backend picks the renderer by kind.

## Error Handling

- Non-`.docx` upload → 400 "Only .docx files are supported".
- Corrupt/invalid docx (python-docx raises) → 422 "Invalid .docx file".
- `convert` producing zero blocks (empty doc) → 422 "Document has no usable content".
- `docx` template missing `docx_b64` at render time → fall back to system default template (defensive).

## Testing

- `render_docx_template`: programmatically build a docx containing `Subject {fir_number}` and a lone `{ip_table}` paragraph → render for Airtel and for Jio → assert `{fir_number}` substituted, marker paragraph gone, and a table with 4 cols (Airtel) / 6 cols (Jio) inserted; with no marker → table appended.
- `parse_docx_to_blocks`: build a docx with a centered bold heading, a numbered list (2 items), and a table → assert blocks `[text(align=center,bold), list(numbered, 2 items), ip_table]`.
- Endpoint (mongomock + generated sample docx): `mode=raw` creates `kind=docx` with `docx_b64`; `mode=convert` creates `kind=blocks` with parsed blocks; non-docx → 400; corrupt → 422.

## Rollout / Compatibility

- `kind` defaults to `blocks`; all existing templates and the seeded default keep working unchanged.
- Purely additive endpoint + optional fields.
