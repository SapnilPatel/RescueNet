# RescueNet

**Satellite SOS needs open sky. Mesh apps need you to install them before the disaster. RescueNet needs neither — you don't need our app to be rescued, but someone near you does: a beacon, a fire truck, or a neighbor's phone.**

When towers go down (Helene 2024: 74% of cell sites offline in affected NC counties; Maui 2023: cellular down, alerts never arrived), anyone can join the open **SOS-HELP** Wi-Fi from any phone, open a page, and send an SOS. The beacon stores it, carries it out of the dead zone, and uploads it to HQ the moment it finds signal. HQ triages it, puts it on a live map, rings the dispatcher via **Retell**, and sends "Help is on the way: Engine 23, ETA 15 min" back to the victim's page.

```
victim's phone ──Wi-Fi "SOS-HELP"──▶ beacon (Android/Termux, Flask + SQLite)
 (any browser,                         │ store-and-forward, most urgent first
  no app, no internet)                 ▼ when it reaches signal
                                     HQ (FastAPI) ──▶ map + AI triage + Retell call
                                       │
victim sees "Help is on the way" ◀─────┘ dispatcher assigns team + ETA
```

## Repo layout
| Path | What |
|---|---|
| `beacon/` | Flask SOS page (inline HTML, works offline, EN/ES), SQLite outbox, uploader loop, captive-portal probe routes |
| `hq/` | FastAPI API + Leaflet dashboard (bundled, no CDN), rule triage + optional Claude enrichment, Retell outbound calls |
| `sim/` | City-scale delivery simulation → `sim/out/delivery_vs_adoption.png` |
| `tests/` | End-to-end tests (real HQ server + beacon) |
| `docs/` | Concept, demo plan, research, runbooks |

## Run locally (5 minutes)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env                                   # fill in keys if you have them

uvicorn hq.main:app --port 8000                        # HQ dashboard: http://localhost:8000
HQ_URL=http://127.0.0.1:8000 python beacon/app.py      # SOS page:     http://localhost:8080
python -m pytest                                       # 8 end-to-end tests
```
Everything works without API keys: triage falls back to rules, and the dashboard shows Retell as off.

## Deploy
- **HQ → Render:** see [docs/render-deploy.md](docs/render-deploy.md). Backup: laptop + `ngrok http 8000`.
- **Beacon → Android:** see [docs/android-termux-setup.md](docs/android-termux-setup.md).
- **Retell agent:** see [docs/retell-agent-prompt.md](docs/retell-agent-prompt.md).
- **Demo:** see [docs/demo-script.md](docs/demo-script.md).

## API
| Method | Path | Who |
|---|---|---|
| POST | `/api/v1/incidents` | beacon upload (idempotent on `message_id`; header `X-Beacon-Key` if `BEACON_KEY` set) |
| GET | `/api/v1/updates?beacon_id=` | beacon pulls acks / assignments |
| GET | `/api/v1/incidents`, `/api/v1/areas` | dashboard |
| POST | `/api/v1/incidents/{id}/ack` · `/assign` `{team, eta_min}` · `/close` · `/call` `{to}` | dispatcher (header `X-Dispatch-Token` if `DISPATCH_TOKEN` set) |
| GET | `/api/v1/config`, `/api/v1/health` | — |

Delivery states on the beacon: `saved_on_beacon` → `uploaded` → `hq_confirmed`. The victim only sees "Delivered" after HQ acks.

## Rules we hold ourselves to
- AI triage can raise severity, never lower it, and never blocks an SOS.
- The SOS page has zero external assets.
- Secrets live only in env vars / `.env`.
