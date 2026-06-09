# ISP Letter Template Builder — Design

**Date:** 2026-06-09
**Status:** Approved (design)
**Author:** brainstormed with user

## Problem

ISP letters (`.docx`) are the only "report" in the app with a real layout, but most
of that layout is **hardcoded** and cannot be changed by users:

- Legal notice line, office header (Dwarka address, phone, email), the
  "Notice u/s 94 BNSS, 2023" heading, the 4 numbered request points, and the
  signature block are hardcoded in `backend/utils/isp_letter_generator.py`
  (in three near-duplicate methods: `create_letter_airtel/vi/jio`).
- The subject and body paragraph are hardcoded in the frontend
  (`frontend/src/pages/IspLettersPage.tsx`, `FIXED_FIELDS`).
- Users can only edit FIR/officer fields.

Officers want to customize the **format and wording** of their letters from the UI,
in a user-friendly way, without touching code.

## Goals

- A **full in-app template builder** for ISP letters: add / remove / reorder blocks,
  edit text and per-block formatting (alignment, bold/italic, font, size).
- A **live preview** that updates as the template is edited.
- The **IP table stays telco-correct**: it auto-formats per ISP and is not freely
  editable (changing columns risks telco rejection). It can be repositioned.
- **Saved templates**: per-user, plus a shared built-in default; admins can share a
  template to the whole department.
- Output stays **`.docx` only** (ZIP, one letter per ISP). Existing behavior preserved.

## Non-Goals

- No freely-editable IP-table columns (telco formats are fixed by Airtel/Jio/Vi).
- No PDF output (may be added later).
- No changes to the CSV "Master File" / "Fully Fixed File" reports.
- No WYSIWYG-to-docx (HTML→docx) conversion — rejected as unreliable for legal docs.

## Chosen Approach

**Structured "blocks" template + smart docx renderer.**

A template is an ordered list of typed blocks stored as JSON. The backend walks the
blocks to build the `.docx`; the frontend renders the same blocks as HTML for the
live preview. Rejected alternatives: (B) upload a Word file with `{{placeholders}}`
via docxtpl — no live preview, hard to inject per-ISP table; (C) WYSIWYG HTML→docx —
lossy/fragile for legal documents.

## Data Model

New MongoDB collection `letter_templates`:

```jsonc
{
  "_id": ObjectId,
  "name": "IFSO Dwarka Default",
  "owner_id": "<user id>" | null,   // null = system/built-in
  "scope": "system" | "user" | "shared",
  "page": {
    "margins_inches": { "top": 0.5, "bottom": 0.5, "left": 0.75, "right": 0.75 },
    "default_font": "Calibri",
    "default_size": 10
  },
  "blocks": [ /* ordered Block[] */ ],
  "created_at": ISODate,
  "updated_at": ISODate
}
```

### Block types

Every block has `{ "id": "<uuid>", "type": "..." }` plus type-specific fields.

1. **`text`** — one paragraph (may contain `\n`).
   - `content` (string, may contain placeholders)
   - `align`: `"left" | "center" | "right"`
   - `bold`, `italic`: bool
   - `font`: string (optional, falls back to `page.default_font`)
   - `size`: number pt (optional, falls back to `page.default_size`)
   - Covers: legal notice, office header, notice heading, recipient, subject,
     salutation, body, signature.

2. **`list`** — an ordered/unordered list.
   - `style`: `"numbered" | "bullet"`
   - `items`: string[] (each may contain placeholders)
   - `font`, `size` (optional)
   - Covers: the request points.

3. **`ip_table`** — the smart per-ISP IP table. **Singleton** (only the first one
   renders; UI prevents adding a second).
   - No editable columns. Position in the block list is its only setting.
   - At render time delegates to `_build_ip_table(doc, isp_name, ip_df)`.

4. **`spacer`** — blank vertical space.
   - `lines`: number (default 1)

### Placeholders

A fixed token set, substituted at generation time from the case form:

```
{fir_number} {fir_date} {letter_date} {police_station} {sections}
{complainant} {isp_name} {officer_name} {officer_designation}
{officer_location} {officer_contact} {subject} {email_reference}
```

Substitution: simple `str.replace` of each `{token}` with its value (empty string if
missing). `{isp_name}` is supplied per-ISP during the generation loop.

## Backend Changes

### `backend/utils/isp_letter_generator.py` (refactor)

- Add `render_template_to_docx(template: dict, isp_name: str, ip_df: pd.DataFrame, case_details: dict) -> Document`:
  - Create `Document`, apply `template.page` margins.
  - Iterate `template.blocks`:
    - `text` → one paragraph; substitute placeholders; apply align/bold/italic/font/size.
    - `list` → numbered or bulleted paragraphs; substitute placeholders per item.
    - `ip_table` → call `_build_ip_table(doc, isp_name, ip_df)`.
    - `spacer` → N empty paragraphs.
- Extract `_build_ip_table(doc, isp_name, ip_df)` from the three existing methods,
  preserving **exactly**:
  - Airtel → 4-column (Type, Search Value, From Date+Time, To Date+Time), `convert_date_to_airtel_format`.
  - Jio → 6-column with `pad_time_to_6_digits`.
  - Vi/others → 6-column, no padding.
- Keep the per-ISP Jio `.txt` generation in `generate_all_letters` (unchanged).
- `generate_letter(...)` / `generate_all_letters(...)` accept an optional `template`
  (dict); when present, route through `render_template_to_docx`. When absent, use the
  seeded system default. The old `create_letter_*` methods are removed once the default
  template reproduces their output (verified by test).

### Seed: "IFSO Dwarka Default" system template

A `scope: "system"`, `owner_id: null` template whose blocks reproduce **today's letter
content**: legal-notice text block (italic, centered, 10pt), office-header text block
(bold name 11pt + address 10pt + contact 9pt, centered), notice-heading block (bold
11pt centered), recipient block, subject block (bold), salutation, body block, request
`list` (the 4 points + closing line), `ip_table`, signature block. Seeded idempotently
on startup (insert if not present).

### New router `backend/routers/letter_templates.py` (prefix `/api/letter-templates`)

| Method | Path | Who | Purpose |
|---|---|---|---|
| GET | `/` | any auth user | list visible: system + own + shared |
| GET | `/{id}` | owner / shared / system | fetch one |
| POST | `/` | any auth user | create (owner = caller, scope `user`) |
| PUT | `/{id}` | owner (or admin for shared/system) | update |
| DELETE | `/{id}` | owner | delete (cannot delete system) |
| POST | `/{id}/share` | admin only | set scope `shared` |

Validation: block list must contain at most one `ip_table`; block types and fields are
validated against a Pydantic schema; placeholder tokens outside the known set are
allowed as literal text (not an error).

### `backend/routers/auto_steps_6_7.py` / generate endpoint

`POST /api/generate-isp-letters` gains optional `template_id` form field. If provided,
load that template (enforcing visibility); else use the system default. Pass the
template dict into `generate_all_letters`.

## Frontend Changes

### New page: Template Builder (`/isp-letters/templates`)

- Left column: **block list** — drag to reorder (HTML5 DnD or a tiny helper), add block
  (`+ Add block ▼`: Text / List / IP Table / Spacer), delete, select.
  - Below it: **selected-block editor** — align toggle, B/I, font dropdown, size,
    content textarea / list-item editor, **Insert placeholder ▼**.
- Right column: **live A4 preview** — renders blocks to HTML approximating the docx
  (white page, margins, fonts, alignment). `ip_table` renders sample rows in the correct
  per-ISP layout (ISP selector to preview Airtel vs Jio vs Vi). Note: "preview is an
  approximation; the .docx is final."
- Top bar: template selector dropdown, **Save / Save As… / Duplicate / Delete**, and
  **Share** (admins only).
- All preview logic is client-side from template JSON (instant, no server round-trip).

### `IspLettersPage.tsx`

- Add a **Template** dropdown at the top (lists visible templates, default = "IFSO
  Dwarka Default"). The chosen `template_id` is sent to `/api/generate-isp-letters`.
- Remove the hardcoded `FIXED_FIELDS`; that content now lives in the default template.
- Add a link/button to the Template Builder page.

### Routing / nav

- Register `/isp-letters/templates` route and a nav entry (near ISP Letters).

## Error Handling

- Generate with a deleted/invisible `template_id` → 404, frontend falls back to default
  with a notice.
- Template with no `ip_table` block → allowed (some letters may omit the table); warn in
  the builder.
- Malformed block JSON on save → 422 with the offending block id.
- Placeholder with no value → renders as empty string (never crashes generation).

## Testing

- **Renderer parity test:** rendering the seeded default template for each ISP produces a
  `.docx` whose paragraphs/headings/request list and table columns match the pre-refactor
  output (assert on extracted text + table shape per ISP: Airtel 4 cols, Jio 6 cols + a
  `.txt`, Vi 6 cols).
- **Block renderer unit tests:** each block type → expected docx paragraph/table;
  placeholder substitution; alignment/bold/italic/font/size applied.
- **CRUD + permissions:** user creates/edits/deletes own; cannot edit another user's;
  only admin can `share`; system template cannot be deleted.
- **Endpoint test:** `generate-isp-letters` with a custom `template_id` uses that
  template; with none uses default.

## Rollout / Compatibility

- Existing users see no change until they pick a different template — the default
  reproduces current output.
- Seeding is idempotent; safe across restarts.
