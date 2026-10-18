# Build Status (Sat Oct 17, 2026, evening)

> The original commit `11f630c` was never pushed and its cloud workspace is gone. The MVP was **rebuilt from these docs** on Sat Oct 17 evening and tested locally. Push it to GitHub before anything else.

## Repo
- GitHub: https://github.com/SapnilPatel/RescueNet (public)

## What's built and tested
- `beacon/` Flask SOS page: mobile, offline, inline HTML/JS, no external assets, English/Spanish toggle. SQLite store-and-forward with unique message IDs (double taps don't duplicate), 4-character SOS code, uploads most urgent first, pulls dispatcher updates back, per-device rate limit, captive-portal probe routes, `termux-location` beacon GPS with env fallback.
- `hq/` FastAPI: `POST /api/v1/incidents` (idempotent), `/updates`, `/incidents`, `/areas` (cluster lines like "beacon-android-01 area: 1 SOS, 3 people, 1 trapped, 1 on oxygen"), `/ack`, `/assign`, `/close`, `/call`, `/config`, `/health`. Optional `BEACON_KEY` / `DISPATCH_TOKEN`. Dashboard with **bundled Leaflet 1.9.4** (no CDN), severity-sorted cards, beep on new critical.
- Triage: rules (English + Spanish keywords) run instantly; optional Claude (`claude-opus-5-5`, structured JSON output) adds a dispatch summary + translation and can only **raise** severity.
- Retell outbound call via `/v2/create-phone-call` with dynamic variables; auto-call on critical (60 s cooldown) + manual "Call dispatcher" / "Call victim" buttons.
- `tests/test_e2e.py` (8 tests, real HQ server): full loop SOS → beacon → HQ → assign "Engine 23, ETA 15" → victim sees "Help is on the way: Engine 23 · ETA 15 min" → closed; HQ offline → SOS waits → delivers when HQ returns; duplicates ignored; urgent first; validation + rate limit; page has no external URLs; AI never lowers severity; tokens enforced.
- Not live-tested (no keys on the build machine): the real Claude API call and the real Retell call. Test both with keys before the demo.

## Deployment
- HQ → **Render** free tier via `render.yaml` (sleeps after ~15 min idle; SQLite resets on deploy). Backup: laptop + ngrok. See `render-deploy.md`.
- Beacon → Android via Termux (`git clone`, `python beacon/app.py`). See `android-termux-setup.md`.
- Secrets only in Render env vars / local `.env` (never committed).

## Simulation results (rebuilt model; 16 km² dead zone, 300 trapped victims, 60 min, 5 seeds)
| Adoption | Phones only | + LoRa beacons | + evacuating cars |
|---|---|---|---|
| 0.5% | 0.1% | 2.3% | 25.1% |
| 1% | 0.7% | 3.0% | 45.1% |
| 2% | 1.3% | 3.9% | 66.5% |
| 5% | 5.9% | 11.6% | **91.1%** |
| 10% | 58.4% | 69.3% | 98.5% |
| 20% | 99.9% | 100.0% | 100.0% |

Assumptions: density 2000/km², 80 m phone/beacon Wi-Fi range, 1.5 km LoRa, beacons on a 1 km grid (~1 per school) with edge beacons reaching an outside gateway, 40% of relay phones in the zone evacuate by car at ~15 km/h to the nearest edge, 300 m populated band with signal around the zone. Victims need no app: their SOS enters any relay/beacon within 80 m. Run: `python sim/simulate.py --seeds 5`.

**Pitch line (updated to match the rebuilt model):** "With 5% of phones carrying our SDK and cars carrying messages out, ~90% of SOS messages reach responders within an hour — and about two-thirds at just 2%." The old line ("2% → ~85%") came from the lost simulation and isn't reproduced by this one, so don't use it.
