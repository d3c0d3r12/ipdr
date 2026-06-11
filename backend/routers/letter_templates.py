# backend/routers/letter_templates.py
import base64

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, ValidationError

from core.db import get_db
from core.config import MAX_UPLOAD_SIZE
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


@router.post("/upload-docx")
async def upload_docx_template(
    file: UploadFile = File(...),
    name: str = Form(...),
    mode: str = Form("raw"),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    """Create a template from an uploaded .docx (mode 'raw' = use as-is, 'convert' = parse to blocks)."""
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large")

    if mode == "convert":
        from utils.docx_import import parse_docx_to_blocks
        try:
            blocks = parse_docx_to_blocks(content)
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid .docx file")
        if not blocks:
            raise HTTPException(status_code=422, detail="Document has no usable content")
        payload = {"name": name, "kind": "blocks", "blocks": blocks}
    else:
        # Validate it is a real docx before storing.
        try:
            import io
            from docx import Document
            Document(io.BytesIO(content))
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid .docx file")
        payload = {
            "name": name,
            "kind": "docx",
            "blocks": [],
            "docx_b64": base64.b64encode(content).decode("ascii"),
        }

    return {"success": True, "template": _handle(svc.create_template, db, user, payload)}
