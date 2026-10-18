# Deploy HQ on Render (free tier)

**Live HQ:** https://rescuenet-r90o.onrender.com (dashboard at `/`, health at `/api/v1/health`).
It was created as a plain **Web Service** (not a Blueprint) with:
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn hq.main:app --host 0.0.0.0 --port $PORT`
- Env: `PYTHON_VERSION=3.12.8`, `AUTO_CALL=critical`, plus the keys below as they become available.

Every push to `main` redeploys it automatically (and wipes the SQLite data).

## Setting it up from scratch

1. Push the repo to GitHub.
2. Render dashboard → **New → Blueprint** → pick the repo. Render reads `render.yaml` and creates `rescuenet-hq`.
3. Fill the secret env vars it asks for (all optional):
   - `ANTHROPIC_API_KEY` — not used (team chose rule-based triage); leave unset
   - `RETELL_API_KEY`, `RETELL_FROM_NUMBER`, `RETELL_TO_NUMBER` (iPhone 2, E.164 `+1...`), `RETELL_AGENT_ID`
   - `BEACON_KEY` — shared secret; put the same value in the beacon's `.env`
   - `DISPATCH_TOKEN` — protects dashboard buttons; open the dashboard once as `https://rescuenet-r90o.onrender.com/?token=<value>`
4. Wait for the deploy, then open `https://rescuenet-r90o.onrender.com/api/v1/health`.

## Free-tier caveats
- **Sleeps after ~15 min idle**; the first request then takes ~30–60 s. Open `/api/v1/health` a few minutes before going on stage, and keep the dashboard tab open (it polls every 3 s, which keeps it awake).
- **SQLite resets** on every deploy/restart. Fine for a demo — don't redeploy right before presenting.

## Backup: laptop + ngrok
```bash
uvicorn hq.main:app --host 0.0.0.0 --port 8000
ngrok http 8000            # set the beacon's HQ_URL to the https URL ngrok prints
```
