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
