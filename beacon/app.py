"""RescueNet beacon: offline SOS page + store-and-forward outbox.

Runs on an Android phone in Termux (or any laptop). Victims join the
SOS-HELP hotspot and submit an SOS from any browser. Every SOS is saved to
SQLite first; an uploader thread pushes the outbox to HQ (most urgent first)
whenever internet appears, and pulls dispatcher updates back so the victim's
page can show "Help is on the way".

Delivery states: saved_on_beacon -> uploaded -> hq_confirmed.
We never tell the victim "delivered" before HQ has acked.

Config (env vars):
  BEACON_ID        beacon-android-01
  HQ_URL           https://rescuenet-r90o.onrender.com   (no trailing slash)
  BEACON_KEY       optional shared secret sent as X-Beacon-Key
  PORT             8080
  BEACON_DB        beacon/beacon.db
  SYNC_INTERVAL    10 (seconds)
  BEACON_LAT/LON   fallback position if termux-location is unavailable
"""
import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import threading
import time
import uuid

import requests
from flask import Flask, Response, jsonify, redirect, request

HERE = os.path.dirname(os.path.abspath(__file__))

STATUSES = ("trapped", "injured", "evacuate", "safe")
NEEDS = ("child", "elderly", "oxygen", "wheelchair", "pet")
STATUS_PRIORITY = {"trapped": 0, "injured": 1, "evacuate": 2, "safe": 3}
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # no 0/O/1/I/L

# Per-client rate limit: at most RATE_MAX new SOS per RATE_WINDOW seconds.
RATE_MAX = 5
RATE_WINDOW = 600


def load_dotenv(path):
    """Tiny .env loader so Termux needs no extra package."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


class Beacon:
    def __init__(self, beacon_id, hq_url, db_path, beacon_key="", lat=None, lon=None):
        self.beacon_id = beacon_id
        self.hq_url = (hq_url or "").rstrip("/")
        self.beacon_key = beacon_key
        self.db_path = db_path
        self.lat = lat
        self.lon = lon
        self.gps_source = "config" if lat is not None else "none"
        self.last_sync = None  # {"at", "ok", "uploaded", "error"}
        self._lock = threading.Lock()
        self._rate = {}
        self._init_db()

    # ---------- storage ----------
    def _conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute(
                """CREATE TABLE IF NOT EXISTS outbox (
                    message_id TEXT PRIMARY KEY,
                    short_code TEXT UNIQUE NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    state TEXT NOT NULL DEFAULT 'saved_on_beacon',
                    created_at INTEGER NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    confirmed_at INTEGER,
                    dispatch_status TEXT,
                    team TEXT,
                    eta_min INTEGER,
                    hq_updated_at INTEGER
                )"""
            )

    def _new_code(self, c):
        while True:
            code = "".join(random.choice(CODE_ALPHABET) for _ in range(4))
            if not c.execute("SELECT 1 FROM outbox WHERE short_code=?", (code,)).fetchone():
                return code

    def rate_limited(self, client):
        now = time.time()
        hits = [t for t in self._rate.get(client, []) if now - t < RATE_WINDOW]
        self._rate[client] = hits
        return len(hits) >= RATE_MAX

    def rate_hit(self, client):
        """Only saved SOS count, so a rejected form (e.g. missing location) costs nothing."""
        self._rate.setdefault(client, []).append(time.time())

    def save_sos(self, data):
        """Validate + store an SOS. Returns (row_dict, created). Raises ValueError."""
        status = str(data.get("status", "")).lower()
        if status not in STATUSES:
            raise ValueError("Choose a status: trapped, injured, evacuate or safe.")
        landmark = str(data.get("landmark", "")).strip()[:200]
        if not landmark:
            raise ValueError("Tell responders where you are (address, landmark, floor).")
        people = _clamp_int(data.get("people", 1), 1, 99, 1)
        injured = _clamp_int(data.get("injured", 0), 0, people, 0)
        needs = data.get("needs") or []
        if isinstance(needs, str):
            needs = [n for n in needs.split(",") if n]
        needs = sorted({str(n).lower() for n in needs if str(n).lower() in NEEDS})

        message_id = str(data.get("message_id") or "").strip()
        if not re.fullmatch(r"[0-9a-fA-F-]{8,64}", message_id):
            message_id = str(uuid.uuid4())

        priority = STATUS_PRIORITY[status] * 10 - (5 if "oxygen" in needs else 0) - min(injured, 4)

        with self._lock, self._conn() as c:
            existing = c.execute("SELECT * FROM outbox WHERE message_id=?", (message_id,)).fetchone()
            if existing:  # double tap / resubmit: same SOS, not a new one
                return dict(existing), False
            code = self._new_code(c)
            packet = {
                "message_id": message_id,
                "short_code": code,
                "beacon_id": self.beacon_id,
                "status": status,
                "people": people,
                "injured": injured,
                "needs": needs,
                "landmark": landmark,
                "note": str(data.get("note", "")).strip()[:100],
                "name": str(data.get("name", "")).strip()[:60],
                "callback": re.sub(r"[^0-9+]", "", str(data.get("callback", "")))[:20],
                "beacon_lat": self.lat,
                "beacon_lon": self.lon,
                "created_at": int(time.time()),
                "hops": [self.beacon_id],
            }
            c.execute(
                "INSERT INTO outbox (message_id, short_code, payload, priority, created_at) VALUES (?,?,?,?,?)",
                (message_id, code, json.dumps(packet, separators=(",", ":")), priority, packet["created_at"]),
            )
            row = c.execute("SELECT * FROM outbox WHERE message_id=?", (message_id,)).fetchone()
            return dict(row), True

    def status_for(self, codes):
        codes = [c.strip().upper() for c in codes if c.strip()][:20]
        if not codes:
            return []
        with self._conn() as c:
            q = "SELECT * FROM outbox WHERE short_code IN (%s)" % ",".join("?" * len(codes))
            return [public_status(dict(r)) for r in c.execute(q, codes).fetchall()]

    def counts(self):
        with self._conn() as c:
            rows = c.execute("SELECT state, COUNT(*) n FROM outbox GROUP BY state").fetchall()
        return {r["state"]: r["n"] for r in rows}

    # ---------- uplink ----------
    def _headers(self):
        return {"X-Beacon-Key": self.beacon_key} if self.beacon_key else {}

    def hq_reachable(self, timeout=4):
        if not self.hq_url:
            return False
        try:
            r = requests.get(self.hq_url + "/api/v1/health", timeout=timeout)
            return r.ok
        except requests.RequestException:
            return False

    def sync_once(self, timeout=8):
        """Upload pending SOS (most urgent first), then pull dispatcher updates."""
        result = {"at": int(time.time()), "ok": False, "uploaded": 0, "updates": 0, "error": None}
        if not self.hq_reachable():
            result["error"] = "HQ unreachable (no internet yet?)"
            self.last_sync = result
            return result

        with self._conn() as c:
            pending = c.execute(
                "SELECT message_id, payload FROM outbox WHERE state != 'hq_confirmed' "
                "ORDER BY priority ASC, created_at ASC"
            ).fetchall()

        for row in pending:
            packet = json.loads(row["payload"])
            with self._conn() as c:
                c.execute(
                    "UPDATE outbox SET state='uploaded', attempts=attempts+1 WHERE message_id=? AND state != 'hq_confirmed'",
                    (row["message_id"],),
                )
            try:
                r = requests.post(self.hq_url + "/api/v1/incidents", json=packet,
                                  headers=self._headers(), timeout=timeout)
                body = r.json() if r.ok else {}
            except (requests.RequestException, ValueError) as e:
                # Sent but no ack: stays 'uploaded' and is retried (HQ is idempotent).
                result["error"] = "upload failed: %s" % e.__class__.__name__
                break
            if body.get("ack") and body.get("message_id") == row["message_id"]:
                with self._conn() as c:
                    c.execute(
                        "UPDATE outbox SET state='hq_confirmed', confirmed_at=? WHERE message_id=?",
                        (int(time.time()), row["message_id"]),
                    )
                result["uploaded"] += 1
            else:
                result["error"] = "HQ rejected upload (HTTP %s)" % r.status_code
                if r.status_code in (401, 403):
                    break

        try:
            r = requests.get(self.hq_url + "/api/v1/updates", params={"beacon_id": self.beacon_id},
                             headers=self._headers(), timeout=timeout)
            if r.ok:
                result["updates"] = self.apply_updates(r.json().get("updates", []))
        except (requests.RequestException, ValueError) as e:
            result["error"] = result["error"] or "update pull failed: %s" % e.__class__.__name__

        result["ok"] = result["error"] is None
        self.last_sync = result
        return result

    def apply_updates(self, updates):
        n = 0
        with self._conn() as c:
            for u in updates:
                cur = c.execute(
                    "UPDATE outbox SET dispatch_status=?, team=?, eta_min=?, hq_updated_at=?, "
                    "state='hq_confirmed', confirmed_at=COALESCE(confirmed_at, ?) "
                    "WHERE message_id=? AND (hq_updated_at IS NULL OR hq_updated_at <= ?)",
                    (u.get("dispatch_status"), u.get("team"), u.get("eta_min"), u.get("updated_at"),
                     int(time.time()), u.get("message_id"), u.get("updated_at") or 0),
                )
                n += cur.rowcount
        return n

    # ---------- GPS ----------
    def refresh_gps(self):
        """Beacon GPS via Termux:API. iOS Safari blocks GPS on http, so the
        beacon's own fix (victim is within Wi-Fi range) is our location."""
        if not shutil.which("termux-location"):
            if self.lat is None:
                print("[gps] termux-location not found: install the Termux:API app + `pkg install termux-api`", flush=True)
            return
        # Last-known first (instant, so early SOS get a location), then a fresh fix.
        for provider, request in (("network", "last"), ("gps", "once"), ("network", "once")):
            try:
                out = subprocess.run(["termux-location", "-p", provider, "-r", request],
                                     capture_output=True, text=True, timeout=45).stdout
                fix = json.loads(out)
                self.lat, self.lon = round(fix["latitude"], 6), round(fix["longitude"], 6)
                self.gps_source = "termux-%s-%s" % (provider, request)
                print("[gps] %s,%s via %s (±%sm)" % (self.lat, self.lon, self.gps_source,
                                                     round(fix.get("accuracy") or 0)), flush=True)
                if request == "once":
                    return
            except (subprocess.SubprocessError, ValueError, KeyError, TypeError):
                continue
        if self.lat is None:
            print("[gps] no location yet: give Termux:API location permission and turn on Location", flush=True)


def _clamp_int(value, lo, hi, default):
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def public_status(row):
    """What the victim's page may show. Only claims delivery after HQ ack."""
    ds = row.get("dispatch_status")
    if ds == "closed":
        stage, text = 4, "Marked rescued / closed by responders."
    elif ds == "assigned":
        eta = " · ETA %s min" % row["eta_min"] if row.get("eta_min") is not None else ""
        stage, text = 3, "Help is on the way: %s%s" % (row.get("team") or "rescue team", eta)
    elif row["state"] == "hq_confirmed":
        stage = 2
        text = ("A dispatcher has seen your SOS." if ds == "acknowledged"
                else "Delivered to HQ. Waiting for a team to be assigned.")
    else:
        stage, text = 1, "Saved on beacon — not yet delivered. It will upload as soon as this beacon reaches signal."
    return {
        "short_code": row["short_code"],
        "stage": stage,
        "state": row["state"],
        "dispatch_status": ds,
        "team": row.get("team"),
        "eta_min": row.get("eta_min"),
        "text": text,
        "updated_at": row.get("hq_updated_at") or row.get("confirmed_at") or row["created_at"],
    }


def create_app(beacon):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 8 * 1024
    page = open(os.path.join(HERE, "sos_page.html"), encoding="utf-8").read()

    @app.get("/")
    def index():
        html = page.replace("{{BEACON_ID}}", beacon.beacon_id)
        return Response(html, mimetype="text/html", headers={"Cache-Control": "no-store"})

    @app.post("/api/sos")
    def submit():
        data = request.get_json(silent=True) or request.form.to_dict(flat=True)
        if "needs" in request.form:
            data["needs"] = request.form.getlist("needs")
        client = request.headers.get("X-Forwarded-For", request.remote_addr or "?")
        msg_id = str(data.get("message_id") or "")
        # Re-sends of the same message_id are always allowed (idempotent).
        is_resend = False
        if msg_id:
            with beacon._conn() as c:
                is_resend = c.execute("SELECT 1 FROM outbox WHERE message_id=?", (msg_id,)).fetchone() is not None
        if not is_resend and beacon.rate_limited(client):
            return jsonify(error="Too many SOS from this device. Your earlier SOS is saved."), 429
        try:
            row, created = beacon.save_sos(data)
        except ValueError as e:
            return jsonify(error=str(e)), 400
        if created:
            beacon.rate_hit(client)
        out = public_status(row)
        out["message_id"] = row["message_id"]
        out["created"] = created
        return jsonify(out), 201 if created else 200

    @app.get("/api/status")
    def status():
        return jsonify(statuses=beacon.status_for(request.args.get("codes", "").split(",")))

    @app.get("/api/beacon")
    def info():
        return jsonify(
            beacon_id=beacon.beacon_id,
            hq_url=beacon.hq_url,
            lat=beacon.lat, lon=beacon.lon, gps_source=beacon.gps_source,
            counts=beacon.counts(),
            last_sync=beacon.last_sync,
        )

    @app.post("/api/sync")
    def sync_now():
        return jsonify(beacon.sync_once())

    # Captive-portal probes: answer "not the internet" so phones show the
    # sign-in sheet pointing at the SOS page when DNS reaches us.
    @app.route("/generate_204")
    @app.route("/gen_204")
    @app.route("/hotspot-detect.html")
    @app.route("/library/test/success.html")
    @app.route("/ncsi.txt")
    @app.route("/connecttest.txt")
    @app.route("/success.txt")
    @app.route("/canonical.html")
    @app.route("/redirect")
    def captive_probe():
        return redirect("/", code=302)

    @app.errorhandler(404)
    def to_sos_page(_e):
        if request.path.startswith("/api/"):
            return jsonify(error="not found"), 404
        return redirect("/", code=302)

    return app


def uploader_loop(beacon, interval):
    while True:
        try:
            r = beacon.sync_once()
            if r["uploaded"] or r["updates"]:
                print("[sync] uploaded=%d updates=%d" % (r["uploaded"], r["updates"]), flush=True)
        except Exception as e:  # never let the uploader die
            print("[sync] error:", e, flush=True)
        time.sleep(interval)


def gps_loop(beacon):
    while True:
        beacon.refresh_gps()
        time.sleep(300)


def main():
    load_dotenv(os.path.join(HERE, ".env"))
    load_dotenv(os.path.join(HERE, "..", ".env"))
    lat, lon = os.environ.get("BEACON_LAT"), os.environ.get("BEACON_LON")
    beacon = Beacon(
        beacon_id=os.environ.get("BEACON_ID", "beacon-android-01"),
        hq_url=os.environ.get("HQ_URL", "http://127.0.0.1:8000"),
        db_path=os.environ.get("BEACON_DB", os.path.join(HERE, "beacon.db")),
        beacon_key=os.environ.get("BEACON_KEY", ""),
        lat=float(lat) if lat else None,
        lon=float(lon) if lon else None,
    )
    interval = float(os.environ.get("SYNC_INTERVAL", "10"))
    threading.Thread(target=gps_loop, args=(beacon,), daemon=True).start()
    threading.Thread(target=uploader_loop, args=(beacon, interval), daemon=True).start()
    port = int(os.environ.get("PORT", "8080"))
    print("RescueNet beacon %s on http://0.0.0.0:%d -> HQ %s" % (beacon.beacon_id, port, beacon.hq_url), flush=True)
    create_app(beacon).run(host="0.0.0.0", port=port, threaded=True)


if __name__ == "__main__":
    main()
