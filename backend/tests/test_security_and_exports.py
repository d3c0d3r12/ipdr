import os
import time
import uuid


def _signup_and_login(client, username: str, password: str = "Admin@123456"):
	signup_payload = {
		"username": username,
		"email": f"{username}@example.com",
		"password": password,
		"full_name": "Test User",
		"role": "investigator"
	}
	client.post("/api/auth/signup", json=signup_payload)
	login = client.post("/api/auth/login", json={"username": username, "password": password})
	assert login.status_code == 200, login.text
	body = login.json()
	return body["access_token"]


def _auth_headers(token: str):
	return {"Authorization": f"Bearer {token}"}


def _wait_task(client, token: str, task_id: str, timeout_s: float = 30):
	deadline = time.time() + timeout_s
	while time.time() < deadline:
		st = client.get(f"/api/process/ipdr/enrich/status?task_id={task_id}", headers=_auth_headers(token))
		assert st.status_code == 200, st.text
		if st.json().get("status") == "completed":
			return
		time.sleep(0.2)
	raise AssertionError("task timeout")


def test_upload_requires_auth(client):
	csv_text = "timestamp,ip\n2026-03-19 10:00:00,8.8.8.8\n"
	files = {"file": ("ipdr.csv", csv_text.encode("utf-8"), "text/csv")}
	data = {"fir": "FIR_TEST_002", "preserve_duplicates": "false"}
	r = client.post("/api/upload/", files=files, data=data)
	assert r.status_code in (401, 403)


def test_upload_rejects_wrong_extension(client):
	token = _signup_and_login(client, f"u{uuid.uuid4().hex[:8]}")
	files = {"file": ("bad.txt", b"hello", "text/plain")}
	data = {"fir": "FIR_TEST_003", "preserve_duplicates": "false"}
	r = client.post("/api/upload/", files=files, data=data, headers=_auth_headers(token))
	assert r.status_code == 400


def test_upload_csv_filters_non_public_ips(client):
	token = _signup_and_login(client, f"u{uuid.uuid4().hex[:8]}")
	csv_text = "timestamp,ip\n2026-03-19 10:00:00,8.8.8.8\n2026-03-19 10:00:05,192.168.1.10\n"
	files = {"file": ("ipdr.csv", csv_text.encode("utf-8"), "text/csv")}
	data = {"fir": "FIR_TEST_004", "preserve_duplicates": "false"}
	r = client.post("/api/upload/", files=files, data=data, headers=_auth_headers(token))
	assert r.status_code == 200, r.text
	body = r.json()
	assert body["count_rows"] == 1
	assert body["problem_rows"] >= 1


def test_exports_work_after_enrichment(client):
	token = _signup_and_login(client, f"u{uuid.uuid4().hex[:8]}")
	csv_text = "timestamp,ip\n2026-03-19 10:00:00,8.8.8.8\n"
	files = {"file": ("ipdr.csv", csv_text.encode("utf-8"), "text/csv")}
	data = {"fir": "FIR_TEST_005", "preserve_duplicates": "false"}
	up = client.post("/api/upload/", files=files, data=data, headers=_auth_headers(token))
	assert up.status_code == 200, up.text
	run_name = up.json()["run_dir"].replace("\\", "/").split("/")[-1]

	start = client.post(f"/api/process/ipdr/enrich/start?run_dir={run_name}", headers=_auth_headers(token))
	assert start.status_code == 200, start.text
	task_id = start.json()["task_id"]
	_wait_task(client, token, task_id, timeout_s=30)

	j = client.get(f"/api/process/ipdr/enrich/export/json?run_dir={run_name}", headers=_auth_headers(token))
	assert j.status_code == 200
	assert j.headers.get("content-type", "").startswith("application/json")

	c = client.get(f"/api/process/ipdr/enrich/export/csv?run_dir={run_name}", headers=_auth_headers(token))
	assert c.status_code == 200
	assert c.headers.get("content-type", "").startswith("text/csv")

	p = client.get(f"/api/process/ipdr/enrich/export/pdf?run_dir={run_name}", headers=_auth_headers(token))
	assert p.status_code == 200
	assert p.headers.get("content-type", "").startswith("application/pdf")

	res = client.get(f"/api/process/ipdr/enrich/results?run_dir={run_name}&limit=1", headers=_auth_headers(token))
	assert res.status_code == 200, res.text
	isp_name = (res.json().get("results") or [{}])[0].get("isp") or "Unknown"

	letter = client.post(
		f"/api/process/ipdr/letter?run_dir={run_name}&isp={isp_name}",
		headers=_auth_headers(token),
		data={
			"fir_number": "FIR/TEST/007",
			"fir_date": "19.03.2026",
			"police_station": "Special Cell",
			"sections": "66 IT Act",
			"subject": "Reg provide information in case",
			"email_reference": "Email Ref",
			"body_description": "Test body",
			"complainant": "Test",
			"officer_name": "Inspector Test",
			"officer_designation": "IFSO, Special Cell",
			"officer_location": "Dwarka",
			"officer_contact": "9999999999",
			"letter_date": "19.03.2026"
		}
	)
	assert letter.status_code == 200
	assert "application/vnd.openxmlformats-officedocument.wordprocessingml.document" in (letter.headers.get("content-type") or "")

	letters_zip = client.post(
		f"/api/process/ipdr/letters?run_dir={run_name}",
		headers=_auth_headers(token),
		data={
			"fir_number": "FIR/TEST/007",
			"fir_date": "19.03.2026",
			"police_station": "Special Cell",
			"sections": "66 IT Act",
			"subject": "Reg provide information in case",
			"email_reference": "Email Ref",
			"body_description": "Test body",
			"complainant": "Test",
			"officer_name": "Inspector Test",
			"officer_designation": "IFSO, Special Cell",
			"officer_location": "Dwarka",
			"officer_contact": "9999999999",
			"letter_date": "19.03.2026"
		}
	)
	assert letters_zip.status_code == 200
	assert letters_zip.headers.get("content-type", "").startswith("application/zip")


def test_enrichment_uses_geolite_when_available(client, monkeypatch, tmp_path):
	token = _signup_and_login(client, f"u{uuid.uuid4().hex[:8]}")

	city_path = tmp_path / "GeoLite2-City.mmdb"
	asn_path = tmp_path / "GeoLite2-ASN.mmdb"
	city_path.write_bytes(b"x")
	asn_path.write_bytes(b"y")
	monkeypatch.setenv("GEOIP_CITY_DB", str(city_path))
	monkeypatch.setenv("GEOIP_ASN_DB", str(asn_path))
	monkeypatch.delenv("IPDR_OFFLINE", raising=False)

	import geoip2.database

	class _Postal:
		code = "110001"

	class _Location:
		latitude = 28.6139
		longitude = 77.2090
		time_zone = "Asia/Kolkata"

	class _Subdiv:
		name = "Delhi"

	class _Subdivs:
		most_specific = _Subdiv()

	class _Country:
		name = "India"

	class _City:
		name = "New Delhi"

	class _CityResp:
		country = _Country()
		subdivisions = _Subdivs()
		city = _City()
		location = _Location()
		postal = _Postal()

	class _AsnResp:
		autonomous_system_organization = "Test ISP"
		autonomous_system_number = 64500

	class _Reader:
		def __init__(self, path):
			self.path = path
		def city(self, ip):
			return _CityResp()
		def asn(self, ip):
			return _AsnResp()
		def close(self):
			return None

	monkeypatch.setattr(geoip2.database, "Reader", _Reader)

	csv_text = "timestamp,ip\n2026-03-19 10:00:00,8.8.8.8\n"
	files = {"file": ("ipdr.csv", csv_text.encode("utf-8"), "text/csv")}
	data = {"fir": "FIR_TEST_006", "preserve_duplicates": "false"}
	up = client.post("/api/upload/", files=files, data=data, headers=_auth_headers(token))
	assert up.status_code == 200, up.text
	run_name = up.json()["run_dir"].replace("\\", "/").split("/")[-1]

	start = client.post(f"/api/process/ipdr/enrich/start?run_dir={run_name}", headers=_auth_headers(token))
	assert start.status_code == 200, start.text
	task_id = start.json()["task_id"]
	_wait_task(client, token, task_id, timeout_s=30)

	results = client.get(f"/api/process/ipdr/enrich/results?run_dir={run_name}&limit=1", headers=_auth_headers(token))
	assert results.status_code == 200, results.text
	row = (results.json().get("results") or [])[0]
	assert row.get("source") == "geolite"
	assert row.get("isp") == "Test ISP"


def test_login_wrong_password_does_not_crash(client):
	username = f"u{uuid.uuid4().hex[:8]}"
	_signup_and_login(client, username, password="Admin@123456")
	r = client.post("/api/auth/login", json={"username": username, "password": "Wrong@123456"})
	assert r.status_code in (401, 403)
