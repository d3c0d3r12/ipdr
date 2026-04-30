import os
import sys
from pathlib import Path
import importlib

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def _configure_test_env(tmp_path_factory):
	backend_dir = Path(__file__).resolve().parents[1]
	if str(backend_dir) not in sys.path:
		sys.path.insert(0, str(backend_dir))

	db_path = tmp_path_factory.mktemp("db") / "ipdr_test.db"
	os.environ["JWT_SECRET"] = "test-secret-please-change"
	os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
	os.environ["ENVIRONMENT"] = "development"
	os.environ["IPDR_OFFLINE"] = "1"
	return str(db_path)


@pytest.fixture()
def client():
	import main
	importlib.reload(main)
	with TestClient(main.app) as c:
		yield c
