# backend/services/letter_template_service.py
"""CRUD + seeding for ISP letter templates (collection: letter_templates)."""
import copy
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
    doc = copy.deepcopy(DEFAULT_TEMPLATE)
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
