# Demo & Build Plan

## Devices (we have 2 iPhones + 1 Android + laptop)
| Device | Role | Runs |
|---|---|---|
| **Android** | Beacon + courier ("B") | Hotspot renamed **SOS-HELP** (mobile data OFF) + **Termux** running Python **Flask** SOS page + SQLite + uploader loop (reuse `node.py` logic) |
| **iPhone 1** (+ judges' phones) | Victim / sender ("A") — no app | Safari → join SOS-HELP → scan QR → submit SOS |
| **iPhone 2** | Family / dispatcher | Receives **Retell** call, shows HQ map |
| **Laptop** | HQ ("C" side) | FastAPI + SQLite, Leaflet map, LLM triage, Retell API, adoption simulation chart |

## Tech stack
### Beacon (Android, offline)
- **Termux** (F-Droid/GitHub build) + **Termux:API** (`termux-location` for beacon GPS)
- **Python 3 + Flask** (not FastAPI — deps hard to build on Termux)
- **SQLite** (stdlib `sqlite3`) — durable outbox, unique message IDs, delivery states
- **requests** — uploader loop: detects internet, POSTs to HQ, marks `hq_confirmed` only after ack
- SOS page: **plain HTML/CSS/vanilla JS, fully inline, no CDNs** (page must work with zero internet)
- Android built-in **Wi-Fi hotspot** named SOS-HELP; **QR code** printed on poster/screen → page URL

### HQ (laptop, online)
- **Python 3.11 + FastAPI + Uvicorn**, Pydantic schema, **SQLite** (idempotent on `message_id`)
- **Claude API** (anthropic SDK) — severity ranking, one-line dispatch summary, translation, clustering duplicates
- **Retell API** — outbound voice call to iPhone 2 with SOS details (dynamic variables); recorded fallback
- Dashboard: **HTML + Leaflet.js** (OpenStreetMap tiles) with polling or Server-Sent Events for live pins
- **ngrok** (or Render) — public URL so the beacon can upload from any network

### Simulation & story
- Existing Python `node.py` / `schema.py` / `storage.py` + **NetworkX** (optional) + **matplotlib/Plotly** → "% SOS delivered vs. % phones with our software, with/without couriers & beacons"
- Poster: Canva/Figma · Submission: Devpost · Code: GitHub

### Roadmap only (pitch, not demo)
- Android relay SDK: **Kotlin + Google Nearby Connections** (Bluetooth/Wi-Fi Direct multi-hop)
- **ESP32** beacon with real captive-portal popup
- **LoRa + Meshtastic** long-range beacons; **Starlink** dishes on trucks/shelters as gateways
- Signed packets (Ed25519, e.g., PyNaCl), per-device rate limits

## Demo script (~2 min)
1. "Towers are down. No internet." Android's SOS-HELP is the only network.
2. Judge's iPhone joins SOS-HELP, scans QR, sends "Trapped, 2 people, 1 injured." Page shows **"Saved on beacon — not yet delivered."**
3. Teammate **walks the Android across the room** → turns off hotspot, joins Wi-Fi ("a car / fire truck reaching coverage").
4. Android auto-uploads → pin appears on HQ map, AI marks **CRITICAL** + summary → **iPhone 2 rings** (Retell).
5. Close on simulation chart: % SOS delivered vs. % phones with our software, with/without couriers & beacons.

## Technical gotchas
- Check Android version: **Termux needs Android 7+**; install from **F-Droid/GitHub**, not Play Store. (Android 4.3/API 18 too old → browser sender only.)
- **Flask on phone, FastAPI on laptop** (FastAPI deps painful on Termux).
- **iOS Safari blocks GPS on http://** → use beacon's GPS (`termux-location`, Termux:API) + user's landmark text.
- No auto captive-portal popup from Android hotspot → **QR code** to page (show actual IP; often `192.168.43.1:8080`). Production: $5 ESP32 beacon gives real popup.
- Expose HQ via **ngrok** or Render (venue Wi-Fi may block device-to-device).
- Some Androids disable hotspot in airplane mode → turn off mobile data / remove SIM instead.
- Android may prompt "No internet — stay connected?" → tap Yes (rehearse).
- Real phone-to-phone multi-hop needs 2+ Androids (Nearby Connections) → stretch goal only; city-scale multi-hop shown in Python simulation.
- Don't build a native iOS app (needs Mac/Xcode, 7-day signing, Multipeer is Apple-only).

## Team split
- **Person 1 – Beacon (Android):** Termux + Flask SOS page (Trapped/Injured/Safe, # people, note, landmark), SQLite with unique IDs, "saved on beacon" status, uploader loop that POSTs when internet appears and marks delivered after HQ ack.
- **Person 2 – HQ (laptop):** FastAPI `POST /api/v1/incidents` (idempotent on message_id), Leaflet map + list, LLM triage (severity, one-line summary, translation), Retell outbound call to iPhone 2 (+ recorded fallback).
- **Person 3 – Story:** adoption simulation chart (from `node.py`), **poster + Devpost by Sat 10 PM**, pitch script, **backup demo video** once flow works.

## Build order
1. Android serves SOS page; iPhone submits.
2. HQ receives manual POST → map.
3. Android auto-uploads to HQ → **record backup video**.
4. AI triage + Retell call.
5. Simulation chart, poster, Devpost by 10 PM, rehearse walk-across demo.

## SOS packet (target)
```json
{
  "message_id": "uuid",
  "beacon_id": "beacon-android-01",
  "status": "trapped|injured|safe",
  "people": 2,
  "injured": 1,
  "note": "<=100 chars",
  "landmark": "text",
  "beacon_lat": 0.0, "beacon_lon": 0.0,
  "created_at": 1792260000,
  "hops": ["beacon-android-01"]
}
```
Delivery states: `saved_on_beacon` → `uploaded` → `hq_confirmed` (never claim delivered before HQ ack).
