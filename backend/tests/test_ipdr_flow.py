import json
import time


def _auth_headers(token: str):
	return {"Authorization": f"Bearer {token}"}


def test_ipdr_csv_upload_and_enrich(client):
	signup_payload = {
		"username": "tester",
		"email": "tester@example.com",
		"password": "Admin@123456",
		"full_name": "Test User",
		"role": "investigator"
	}
	r = client.post("/api/auth/signup", json=signup_payload)
	assert r.status_code in (200, 400)

	login = client.post("/api/auth/login", json={"username": "tester", "password": "Admin@123456"})
	assert login.status_code == 200, login.text
	body = login.json()
	assert body.get("success") is True
	token = body.get("access_token")
	assert token

	csv_text = "timestamp,ip\n2026-03-19 10:00:00,8.8.8.8\n2026-03-19 10:00:05,1.1.1.1\n"
	files = {"file": ("ipdr.csv", csv_text.encode("utf-8"), "text/csv")}
	data = {"fir": "FIR_TEST_001", "preserve_duplicates": "false"}

	up = client.post("/api/upload/", files=files, data=data, headers=_auth_headers(token))
	assert up.status_code == 200, up.text
	run_dir = up.json().get("run_dir")
	assert run_dir
	run_name = run_dir.replace("\\", "/").split("/")[-1]

	start = client.post(f"/api/process/ipdr/enrich/start?run_dir={run_name}", headers=_auth_headers(token))
	assert start.status_code == 200, start.text
	task_id = start.json().get("task_id")
	assert task_id

	deadline = time.time() + 30
	while time.time() < deadline:
		st = client.get(f"/api/process/ipdr/enrich/status?task_id={task_id}", headers=_auth_headers(token))
		assert st.status_code == 200, st.text
		status = st.json().get("status")
		if status == "completed":
			break
		time.sleep(0.2)
	else:
		raise AssertionError("Enrichment did not complete in time")

	summary = client.get(f"/api/process/ipdr/enrich/summary?run_dir={run_name}", headers=_auth_headers(token))
	assert summary.status_code == 200, summary.text
	s = summary.json()
	assert s.get("total_unique_ips") == 2
	assert isinstance(s.get("by_isp"), list)

	results = client.get(f"/api/process/ipdr/enrich/results?run_dir={run_name}&limit=10", headers=_auth_headers(token))
	assert results.status_code == 200, results.text
	rj = results.json()
	assert rj.get("count") == 2
	assert len(rj.get("results") or []) == 2

	js = client.get(f"/api/process/ipdr/enrich/export/json?run_dir={run_name}", headers=_auth_headers(token))
	assert js.status_code == 200
	payload = json.loads(js.content.decode("utf-8"))
	assert "summary" in payload and "results" in payload
