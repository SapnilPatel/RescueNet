"""RescueNet HQ: receives SOS uploads from beacons, triages them, shows them
on a live map, and sends dispatcher decisions back to the beacons.

Run:  uvicorn hq.main:app --host 0.0.0.0 --port 8000

Env (all optional): HQ_DB, BEACON_KEY, DISPATCH_TOKEN, ANTHROPIC_API_KEY,
CLAUDE_MODEL, RETELL_*, AUTO_CALL (critical|high|off), AUTO_CALL_COOLDOWN_S,
MAP_LAT, MAP_LON.
"""
import json
import logging
import os
import sqlite3
import threading
import time
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import retell, triage

HERE = os.path.dirname(os.path.abspath(__file__))
log = logging.getLogger("rescuenet.hq")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")


def _load_dotenv():
    path = os.path.join(HERE, "..", ".env")
    if os.environ.get("RESCUENET_NO_DOTENV") != "1" and os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

STATUSES = ("trapped", "injured", "evacuate", "safe")
NEEDS = ("child", "elderly", "oxygen", "wheelchair", "pet")


class IncidentIn(BaseModel):
    message_id: str = Field(min_length=8, max_length=64)
    short_code: str = Field(min_length=3, max_length=8)
    beacon_id: str = Field(min_length=1, max_length=64)
    status: str
    people: int = Field(default=1, ge=1, le=999)
    injured: int = Field(default=0, ge=0, le=999)
    needs: List[str] = []
    landmark: str = Field(min_length=1, max_length=200)
    note: str = Field(default="", max_length=100)
    name: str = Field(default="", max_length=60)
    callback: str = Field(default="", max_length=20)
    beacon_lat: Optional[float] = None
    beacon_lon: Optional[float] = None
    created_at: int
    hops: List[str] = []

    @field_validator("status")
    @classmethod
    def _status(cls, v):
        if v not in STATUSES:
            raise ValueError("status must be one of %s" % (STATUSES,))
        return v

    @field_validator("needs")
    @classmethod
    def _needs(cls, v):
        return sorted({n for n in v if n in NEEDS})


class AssignIn(BaseModel):
    team: str = Field(min_length=1, max_length=60)
    eta_min: Optional[int] = Field(default=None, ge=0, le=1440)


class CallIn(BaseModel):
    to: str = "dispatcher"  # "dispatcher" | "callback" | an E.164 number


class CallSwitchIn(BaseModel):
    enabled: bool
    minutes: int = Field(default=15, ge=1, le=120)


JSON_COLS = ("needs", "hops")


class Store:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        with self.conn() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute(
                """CREATE TABLE IF NOT EXISTS incidents (
                    message_id TEXT PRIMARY KEY,
                    short_code TEXT, beacon_id TEXT, status TEXT,
                    people INTEGER, injured INTEGER, needs TEXT,
                    landmark TEXT, note TEXT, name TEXT, callback TEXT,
                    lat REAL, lon REAL, created_at INTEGER, received_at INTEGER, hops TEXT,
                    score INTEGER, severity TEXT, summary TEXT,
                    ai_severity TEXT, ai_summary TEXT, ai_language TEXT, ai_translation TEXT, ai_reason TEXT,
                    dispatch_status TEXT DEFAULT 'new', team TEXT, eta_min INTEGER,
                    call_status TEXT, call_id TEXT,
                    updated_at INTEGER
                )"""
            )
            c.execute("CREATE INDEX IF NOT EXISTS ix_beacon ON incidents(beacon_id)")

    def conn(self):
        c = sqlite3.connect(self.path, timeout=10)
        c.row_factory = sqlite3.Row
        return c

    @staticmethod
    def to_dict(row):
        d = dict(row)
        for k in JSON_COLS:
            if k in d:
                d[k] = json.loads(d[k] or "[]")
        return d

    def get(self, message_id):
        with self.conn() as c:
            row = c.execute("SELECT * FROM incidents WHERE message_id=?", (message_id,)).fetchone()
        return self.to_dict(row) if row else None

    def insert(self, inc: IncidentIn, rule):
        """Returns (incident, created). Idempotent on message_id."""
        now = int(time.time())
        with self.lock, self.conn() as c:
            cur = c.execute(
                """INSERT OR IGNORE INTO incidents (message_id, short_code, beacon_id, status, people, injured,
                   needs, landmark, note, name, callback, lat, lon, created_at, received_at, hops,
                   score, severity, summary, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (inc.message_id, inc.short_code, inc.beacon_id, inc.status, inc.people, inc.injured,
                 json.dumps(inc.needs), inc.landmark, inc.note, inc.name, inc.callback,
                 inc.beacon_lat, inc.beacon_lon, inc.created_at, now, json.dumps(inc.hops + ["hq"]),
                 rule["score"], rule["severity"], rule["summary"], now),
            )
            created = cur.rowcount == 1
        return self.get(inc.message_id), created

    def update(self, message_id, **fields):
        fields["updated_at"] = int(time.time())
        cols = ", ".join("%s=?" % k for k in fields)
        with self.lock, self.conn() as c:
            cur = c.execute("UPDATE incidents SET %s WHERE message_id=?" % cols, (*fields.values(), message_id))
        if not cur.rowcount:
            raise HTTPException(404, "incident not found")
        return self.get(message_id)

    def query(self, sql, args=()):
        with self.conn() as c:
            return [self.to_dict(r) for r in c.execute(sql, args).fetchall()]


SEV_ORDER = "CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END"


def create_app(db_path=None):
    store = Store(db_path or os.environ.get("HQ_DB", os.path.join(HERE, "hq.db")))
    app = FastAPI(title="RescueNet HQ")
    app.state.store = store
    last_auto_call = {"at": 0.0}
    # Retell credit is scarce: calls are OFF until a dispatcher switches them on,
    # switch themselves off again after a few minutes, and reset to OFF on restart.
    call_switch = {"until": 0.0}

    def calls_on():
        return time.time() < call_switch["until"]

    def check_beacon(key):
        expected = os.environ.get("BEACON_KEY")
        if expected and key != expected:
            raise HTTPException(401, "bad beacon key")

    def check_dispatch(token):
        expected = os.environ.get("DISPATCH_TOKEN")
        if expected and token != expected:
            raise HTTPException(401, "dispatcher token required")

    def do_call(inc, to_number=None):
        store.update(inc["message_id"], call_status="calling")
        res = retell.place_call(inc, to_number)
        status = "placed" if res["ok"] else "failed: " + res["error"][:120]
        store.update(inc["message_id"], call_status=status, call_id=res.get("call_id"))
        log.info("call %s -> %s", inc["short_code"], status)
        return res

    def enrich_and_alert(message_id):
        inc = store.get(message_id)
        ai = triage.ai_enrich(inc, {"severity": inc["severity"]})
        if ai:
            inc = store.update(
                message_id,
                severity=triage.merge_severity(inc["severity"], ai.get("severity")),
                ai_severity=ai.get("severity"),
                ai_summary=ai.get("dispatch_summary", "")[:300],
                ai_language=ai.get("language", "")[:40],
                ai_translation=ai.get("translation_en", "")[:400],
                ai_reason=ai.get("reason", "")[:300],
            )
        auto = os.environ.get("AUTO_CALL", "critical").lower()
        threshold = {"critical": ["critical"], "high": ["critical", "high"]}.get(auto, [])
        cooldown = float(os.environ.get("AUTO_CALL_COOLDOWN_S", "60"))
        if inc["severity"] in threshold and retell.configured() and not inc.get("call_status"):
            if not calls_on():
                store.update(message_id, call_status="not called (calls switched off)")
                return
            if time.time() - last_auto_call["at"] >= cooldown:
                last_auto_call["at"] = time.time()
                do_call(inc)
            else:
                store.update(message_id, call_status="skipped (cooldown)")

    # ---------- beacon API ----------
    @app.post("/api/v1/incidents")
    def upload(inc: IncidentIn, background: BackgroundTasks, x_beacon_key: Optional[str] = Header(None)):
        check_beacon(x_beacon_key)
        rule = triage.rule_triage(inc.model_dump())
        incident, created = store.insert(inc, rule)
        if created:
            log.info("SOS %s from %s: %s", inc.short_code, inc.beacon_id, rule["summary"])
            background.add_task(enrich_and_alert, inc.message_id)
        return {"ack": True, "message_id": inc.message_id, "duplicate": not created,
                "severity": incident["severity"]}

    @app.get("/api/v1/updates")
    def updates(beacon_id: str = Query(..., max_length=64), x_beacon_key: Optional[str] = Header(None)):
        check_beacon(x_beacon_key)
        rows = store.query(
            "SELECT message_id, short_code, dispatch_status, team, eta_min, updated_at FROM incidents "
            "WHERE beacon_id=?", (beacon_id,))
        return {"beacon_id": beacon_id, "updates": [
            {k: r[k] for k in ("message_id", "short_code", "dispatch_status", "team", "eta_min", "updated_at")}
            for r in rows]}

    # ---------- dashboard API ----------
    @app.get("/api/v1/incidents")
    def incidents(include_closed: bool = True):
        where = "" if include_closed else "WHERE dispatch_status != 'closed'"
        return {"incidents": store.query(
            "SELECT * FROM incidents %s ORDER BY (dispatch_status='closed'), %s, received_at DESC" % (where, SEV_ORDER))}

    @app.get("/api/v1/areas")
    def areas():
        rows = store.query("SELECT * FROM incidents WHERE dispatch_status != 'closed'")
        out = {}
        for r in rows:
            a = out.setdefault(r["beacon_id"], {"beacon_id": r["beacon_id"], "lat": None, "lon": None, "sos": 0,
                                                "people": 0, "injured": 0, "trapped": 0, "needs": {},
                                                "worst": "low"})
            if r["lat"] is not None:
                a["lat"], a["lon"] = r["lat"], r["lon"]
            a["sos"] += 1
            a["people"] += r["people"] if r["status"] != "safe" else 0
            a["injured"] += r["injured"]
            a["trapped"] += r["status"] == "trapped"
            for n in r["needs"]:
                a["needs"][n] = a["needs"].get(n, 0) + 1
            if triage.RANK[r["severity"]] > triage.RANK[a["worst"]]:
                a["worst"] = r["severity"]
        for a in out.values():
            bits = ["%d SOS" % a["sos"], "%d people" % a["people"]]
            if a["trapped"]:
                bits.append("%d trapped" % a["trapped"])
            if a["injured"]:
                bits.append("%d injured" % a["injured"])
            bits += ["%d %s" % (v, "on oxygen" if k == "oxygen" else k) for k, v in sorted(a["needs"].items())]
            a["summary"] = "%s area: %s" % (a["beacon_id"], ", ".join(bits))
        return {"areas": sorted(out.values(), key=lambda a: -triage.RANK[a["worst"]])}

    @app.post("/api/v1/incidents/{message_id}/ack")
    def ack(message_id: str, x_dispatch_token: Optional[str] = Header(None)):
        check_dispatch(x_dispatch_token)
        inc = store.get(message_id) or {}
        if inc.get("dispatch_status") in ("assigned", "closed"):
            return inc
        return store.update(message_id, dispatch_status="acknowledged")

    @app.post("/api/v1/incidents/{message_id}/assign")
    def assign(message_id: str, body: AssignIn, x_dispatch_token: Optional[str] = Header(None)):
        check_dispatch(x_dispatch_token)
        return store.update(message_id, dispatch_status="assigned", team=body.team.strip(), eta_min=body.eta_min)

    @app.post("/api/v1/incidents/{message_id}/close")
    def close(message_id: str, x_dispatch_token: Optional[str] = Header(None)):
        check_dispatch(x_dispatch_token)
        return store.update(message_id, dispatch_status="closed")

    @app.post("/api/v1/incidents/{message_id}/call")
    def call(message_id: str, body: CallIn = CallIn(), x_dispatch_token: Optional[str] = Header(None)):
        check_dispatch(x_dispatch_token)
        inc = store.get(message_id)
        if not inc:
            raise HTTPException(404, "incident not found")
        if not calls_on():
            raise HTTPException(409, "Retell calls are switched off. Turn them on in the dashboard header first.")
        to = None
        if body.to == "callback":
            if not inc.get("callback"):
                raise HTTPException(400, "victim left no callback number")
            to = inc["callback"] if inc["callback"].startswith("+") else "+1" + inc["callback"]
        elif body.to.startswith("+"):
            to = body.to
        res = do_call(inc, to)
        if not res["ok"]:
            raise HTTPException(502, res["error"])
        return res

    @app.post("/api/v1/calls")
    def switch_calls(body: CallSwitchIn, x_dispatch_token: Optional[str] = Header(None)):
        check_dispatch(x_dispatch_token)
        call_switch["until"] = time.time() + body.minutes * 60 if body.enabled else 0.0
        log.info("Retell calls switched %s", "ON for %d min" % body.minutes if body.enabled else "OFF")
        return {"calls_on": calls_on(), "calls_until": int(call_switch["until"])}

    @app.get("/api/v1/config")
    def config():
        return {
            "calls_on": calls_on(),
            "calls_seconds_left": max(0, int(call_switch["until"] - time.time())),
            "claude_enabled": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "retell_enabled": retell.configured() and bool(os.environ.get("RETELL_TO_NUMBER")),
            "auto_call": os.environ.get("AUTO_CALL", "critical"),
            "dispatch_token_required": bool(os.environ.get("DISPATCH_TOKEN")),
            "map_center": [float(os.environ.get("MAP_LAT", "34.0205")), float(os.environ.get("MAP_LON", "-118.2856"))],
        }

    @app.get("/api/v1/health")
    def health():
        return {"ok": True, "time": int(time.time())}

    @app.get("/")
    def dashboard():
        return FileResponse(os.path.join(HERE, "static", "index.html"))

    app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
    return app


app = create_app()
