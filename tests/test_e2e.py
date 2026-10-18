"""End-to-end: victim -> beacon (Flask) -> real HQ server (uvicorn) -> dispatcher -> back to victim."""
import os
import socket
import sys
import threading
import time

import pytest
import requests
import uvicorn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "beacon"))

# Never read the real .env (it holds the Retell key) and never call paid APIs from tests.
os.environ["RESCUENET_NO_DOTENV"] = "1"
for k in ("ANTHROPIC_API_KEY", "RETELL_API_KEY", "RETELL_FROM_NUMBER", "RETELL_TO_NUMBER", "RETELL_AGENT_ID",
          "BEACON_KEY", "DISPATCH_TOKEN"):
    os.environ.pop(k, None)
os.environ["HQ_DB"] = ":memory:"  # module-level app; tests use their own DBs below

import app as beacon_app  # noqa: E402
from hq import main as hq_main, retell, triage  # noqa: E402

assert not os.environ.get("RETELL_API_KEY"), "tests must not see a real Retell key"


@pytest.fixture(autouse=True)
def no_real_retell(monkeypatch):
    def blocked(*a, **kw):
        raise AssertionError("a test tried to make a real Retell HTTP request")
    monkeypatch.setattr(retell.httpx, "post", blocked)


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class HQServer:
    def __init__(self, db_path):
        self.port = free_port()
        self.url = "http://127.0.0.1:%d" % self.port
        self.app = hq_main.create_app(db_path)
        self.server = None

    def start(self):
        self.server = uvicorn.Server(uvicorn.Config(self.app, host="127.0.0.1", port=self.port, log_level="warning"))
        self.thread = threading.Thread(target=self.server.run, daemon=True)
        self.thread.start()
        for _ in range(100):
            try:
                if requests.get(self.url + "/api/v1/health", timeout=0.5).ok:
                    return
            except requests.RequestException:
                time.sleep(0.05)
        raise RuntimeError("HQ did not start")

    def stop(self):
        self.server.should_exit = True
        self.thread.join(5)


@pytest.fixture
def hq(tmp_path):
    srv = HQServer(str(tmp_path / "hq.db"))
    srv.start()
    yield srv
    srv.stop()


@pytest.fixture
def beacon(tmp_path, hq):
    b = beacon_app.Beacon("beacon-test-01", hq.url, str(tmp_path / "beacon.db"), lat=34.02, lon=-118.28)
    return b, beacon_app.create_app(b).test_client()


SOS = {"status": "trapped", "people": 2, "injured": 1, "landmark": "2nd floor, blue house, 123 Oak St",
       "needs": ["oxygen"], "note": "smoke in hallway", "callback": "(213) 555-0100"}


def status_of(client, code):
    return client.get("/api/status?codes=" + code).get_json()["statuses"][0]


def test_full_loop(hq, beacon):
    b, client = beacon
    r = client.post("/api/sos", json=SOS)
    assert r.status_code == 201
    code = r.get_json()["short_code"]
    st = status_of(client, code)
    assert st["state"] == "saved_on_beacon" and st["stage"] == 1
    assert "not yet delivered" in st["text"]

    res = b.sync_once()
    assert res["ok"] and res["uploaded"] == 1
    assert status_of(client, code)["state"] == "hq_confirmed"

    incs = requests.get(hq.url + "/api/v1/incidents").json()["incidents"]
    assert len(incs) == 1
    inc = incs[0]
    assert inc["severity"] == "critical"
    assert inc["lat"] == 34.02 and inc["hops"] == ["beacon-test-01", "hq"]
    assert inc["callback"] == "2135550100"

    areas = requests.get(hq.url + "/api/v1/areas").json()["areas"]
    assert areas[0]["summary"] == "beacon-test-01 area: 1 SOS, 2 people, 1 trapped, 1 injured, 1 on oxygen"

    r = requests.post(hq.url + "/api/v1/incidents/%s/assign" % inc["message_id"],
                      json={"team": "Engine 23", "eta_min": 15})
    assert r.ok
    b.sync_once()
    st = status_of(client, code)
    assert st["stage"] == 3
    assert st["text"] == "Help is on the way: Engine 23 · ETA 15 min"

    requests.post(hq.url + "/api/v1/incidents/%s/close" % inc["message_id"])
    b.sync_once()
    assert status_of(client, code)["stage"] == 4


def test_hq_offline_then_returns(tmp_path):
    srv = HQServer(str(tmp_path / "hq.db"))  # not started yet
    b = beacon_app.Beacon("beacon-test-02", srv.url, str(tmp_path / "b.db"))
    client = beacon_app.create_app(b).test_client()
    code = client.post("/api/sos", json=SOS).get_json()["short_code"]

    res = b.sync_once()
    assert not res["ok"] and res["uploaded"] == 0
    assert status_of(client, code)["state"] == "saved_on_beacon"

    srv.start()
    try:
        res = b.sync_once()
        assert res["uploaded"] == 1
        assert status_of(client, code)["state"] == "hq_confirmed"
    finally:
        srv.stop()


def test_duplicates_ignored(hq, beacon):
    b, client = beacon
    body = dict(SOS, message_id="11111111-2222-4333-8444-555555555555")
    first = client.post("/api/sos", json=body)
    again = client.post("/api/sos", json=body)  # double tap on the phone
    assert first.status_code == 201 and again.status_code == 200
    assert first.get_json()["short_code"] == again.get_json()["short_code"]
    b.sync_once()

    # Beacon re-uploads the same packet (e.g. lost ack): HQ keeps one incident.
    packet = requests.get(hq.url + "/api/v1/incidents").json()["incidents"][0]
    with b._conn() as c:
        c.execute("UPDATE outbox SET state='uploaded'")
    b.sync_once()
    r = requests.post(hq.url + "/api/v1/incidents", json={
        "message_id": packet["message_id"], "short_code": packet["short_code"], "beacon_id": packet["beacon_id"],
        "status": "trapped", "landmark": "x", "created_at": 1})
    assert r.json() == {"ack": True, "message_id": packet["message_id"], "duplicate": True, "severity": "critical"}
    assert len(requests.get(hq.url + "/api/v1/incidents").json()["incidents"]) == 1


def test_urgent_uploaded_first(hq, beacon):
    b, client = beacon
    client.post("/api/sos", json=dict(SOS, status="safe", needs=[], note="", landmark="park"))
    client.post("/api/sos", json=dict(SOS, status="trapped"))
    received = []
    real_post = beacon_app.requests.post

    def spy(url, json=None, **kw):
        received.append(json["status"])
        return real_post(url, json=json, **kw)

    beacon_app.requests.post = spy
    try:
        b.sync_once()
    finally:
        beacon_app.requests.post = real_post
    assert received == ["trapped", "safe"]


def test_validation_and_rate_limit(beacon):
    _, client = beacon
    assert client.post("/api/sos", json={"status": "trapped"}).status_code == 400  # landmark required
    assert client.post("/api/sos", json={"landmark": "x"}).status_code == 400  # status required
    codes = [client.post("/api/sos", json=SOS).status_code for _ in range(beacon_app.RATE_MAX + 1)]
    assert codes[-1] == 429


def test_page_is_offline_safe(beacon):
    _, client = beacon
    html = client.get("/").get_data(as_text=True)
    assert "beacon-test-01" in html
    assert "http://" not in html and "https://" not in html  # no CDN / external assets
    assert client.get("/generate_204").status_code == 302
    assert client.get("/hotspot-detect.html").status_code == 302


def test_ai_never_lowers(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setattr(triage, "ai_enrich", lambda sos, rule: {
        "severity": "low", "dispatch_summary": "s", "language": "Spanish", "translation_en": "t", "reason": "r"})
    client = TestClient(hq_main.create_app(str(tmp_path / "x.db")))
    client.post("/api/v1/incidents", json={"message_id": "aaaaaaaa-0000", "short_code": "AB12", "beacon_id": "b",
                                           "status": "trapped", "landmark": "x", "created_at": 1,
                                           "note": "fire"})
    inc = client.get("/api/v1/incidents").json()["incidents"][0]
    assert inc["severity"] == "critical" and inc["ai_severity"] == "low" and inc["ai_language"] == "Spanish"

    monkeypatch.setattr(triage, "ai_enrich", lambda sos, rule: {
        "severity": "critical", "dispatch_summary": "s", "language": "en", "translation_en": "t", "reason": "r"})
    client.post("/api/v1/incidents", json={"message_id": "bbbbbbbb-0000", "short_code": "CD34", "beacon_id": "b",
                                           "status": "safe", "landmark": "x", "created_at": 1})
    inc = [i for i in client.get("/api/v1/incidents").json()["incidents"] if i["short_code"] == "CD34"][0]
    assert inc["severity"] == "critical"  # AI raised it


def test_tokens_enforced(monkeypatch, tmp_path):
    from fastapi.testclient import TestClient

    monkeypatch.setenv("BEACON_KEY", "k1")
    monkeypatch.setenv("DISPATCH_TOKEN", "d1")
    client = TestClient(hq_main.create_app(str(tmp_path / "y.db")))
    body = {"message_id": "cccccccc-0000", "short_code": "EF56", "beacon_id": "b", "status": "injured",
            "landmark": "x", "created_at": 1}
    assert client.post("/api/v1/incidents", json=body).status_code == 401
    assert client.post("/api/v1/incidents", json=body, headers={"X-Beacon-Key": "k1"}).json()["ack"]
    assert client.post("/api/v1/incidents/cccccccc-0000/close").status_code == 401
    assert client.post("/api/v1/incidents/cccccccc-0000/close", headers={"X-Dispatch-Token": "d1"}).status_code == 200


def test_calls_off_by_default(monkeypatch, tmp_path):
    """Retell credit is scarce: no auto-call and no manual call until switched on."""
    from fastapi.testclient import TestClient
    from hq import retell

    placed = []
    monkeypatch.setattr(retell, "configured", lambda: True)
    monkeypatch.setattr(retell, "place_call", lambda inc, to=None: placed.append(inc["short_code"]) or {"ok": True, "call_id": "c1"})
    monkeypatch.setenv("AUTO_CALL", "critical")
    monkeypatch.setenv("AUTO_CALL_COOLDOWN_S", "0")
    client = TestClient(hq_main.create_app(str(tmp_path / "z.db")))
    sos = {"short_code": "GH78", "beacon_id": "b", "status": "trapped", "injured": 1, "landmark": "x", "created_at": 1}

    assert client.get("/api/v1/config").json()["calls_on"] is False
    client.post("/api/v1/incidents", json=dict(sos, message_id="dddddddd-0001"))
    assert placed == []
    assert client.get("/api/v1/incidents").json()["incidents"][0]["call_status"] == "not called (calls switched off)"
    assert client.post("/api/v1/incidents/dddddddd-0001/call", json={}).status_code == 409
    assert placed == []

    assert client.post("/api/v1/calls", json={"enabled": True, "minutes": 5}).json()["calls_on"] is True
    client.post("/api/v1/incidents", json=dict(sos, message_id="dddddddd-0002", short_code="JK90"))
    assert placed == ["JK90"]
    assert client.post("/api/v1/incidents/dddddddd-0001/call", json={}).status_code == 200
    assert placed == ["JK90", "GH78"]

    client.post("/api/v1/calls", json={"enabled": False})
    assert client.get("/api/v1/config").json()["calls_on"] is False
    assert client.post("/api/v1/incidents/dddddddd-0001/call", json={}).status_code == 409
