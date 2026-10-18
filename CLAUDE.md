# RescueNet — Claude Code project memory

Team RescueNet, **Dual-Use Hackathon @ USC Viterbi** (LA Tech Week, Oct 16–18, 2026). Vertical 03 Communications + Retell (voice AI).

**Pitch:** "Satellite SOS needs open sky. Mesh apps need you to install them before the disaster. RescueNet needs neither — you don't need our app to be rescued, but someone near you does: a beacon, a fire truck, or a neighbor's phone."

## Deadlines
- Devpost + poster: **Sat Oct 17, 10 PM PT**
- Demo Day / final pitch: **Sun Oct 18**, event ends 5 PM

## Hard rules
- **Civilian framing only** — no defense / marine / military projects or funding (international student on team).
- Say "you don't need our app to be rescued", never just "no app needed".
- Never claim an SOS is delivered before the HQ ack (`saved_on_beacon` → `uploaded` → `hq_confirmed`).
- AI triage may raise severity, never lower it; AI never blocks an SOS.
- The SOS page must work with zero internet: inline HTML/CSS/JS, no CDNs. Dashboard bundles Leaflet locally.
- Secrets only in env vars / local `.env` — never commit them.
- Lead with Maui 2023 / Helene 2024 outage examples, not the LA 2025 fires.

## Architecture
- `beacon/` — Flask (runs on Android via Termux): SOS page, SQLite store-and-forward outbox, uploader loop (most urgent first), pulls dispatcher updates back, captive-portal probe routes.
- `hq/` — FastAPI + SQLite: `POST /api/v1/incidents` (idempotent on `message_id`), `GET /api/v1/updates?beacon_id=`, `/incidents`, `/areas`, `/incidents/{id}/ack|assign|close|call`, `/config`, `/health`. Leaflet dashboard, rule triage + optional Claude enrichment, Retell outbound call (`/v2/create-phone-call`, dynamic variables).
- `sim/simulate.py` → `sim/out/delivery_vs_adoption.png`.
- `tests/` — pytest end-to-end (real HQ server on a local port + beacon).
- Deploy: HQ on Render free tier (`render.yaml`), backup laptop + ngrok. Beacon: `git clone` + `python beacon/app.py` in Termux.

## Code status
Rebuilt Sat Oct 17 2026 (evening) after the original commit `11f630c` was lost. Run `python -m pytest` before pushing.

## Knowledge base (`docs/`)
| File | Contents |
|---|---|
| `00-README-start-here.md` | Overview, team constraints, devices |
| `01-hackathon-context.md` | Rules, verticals, judging criteria, twists, prizes |
| `02-rescuenet-concept.md` | Final concept v2, competition, LoRa, funding, pitch lines |
| `03-demo-and-build-plan.md` | Devices, stack, demo script, gotchas, build order, SOS packet schema |
| `04-decisions-and-research-log.md` | Rejected ideas, corrections, sources |
| `05-hq-identification-and-feedback-loop.md` | Who/where, reverse status path, API |
| `06-build-status.md` | What was built/tested, deploy, simulation results |
| `android-termux-setup.md`, `render-deploy.md`, `retell-agent-prompt.md`, `demo-script.md` | Runbooks |
