# Android beacon setup (Termux + Termux:API)

Needs **Android 7+** (target phone: Android 12). Two apps, both downloaded from **GitHub** (no F-Droid store, no Play Store):
**Termux** (runs the beacon) and **Termux:API** (gives the beacon the phone's real GPS location).

## 1. Install the two apps (~3 min)
1. In Chrome on the Android, open **https://github.com/termux/termux-app/releases/latest** → under **Assets**, download the file ending in **`github-debug_arm64-v8a.apk`** (if it won't install, use the `universal` one) → open it → allow **"Install unknown apps"** for Chrome → **Install**.
2. Open **https://github.com/termux/termux-api/releases/latest** → under **Assets**, download the file ending in **`github-debug.apk`** → open → **Install**.
3. Both must come from GitHub. Don't install either from the Play Store (mixed sources won't talk to each other).

## 2. Set up the beacon (one command, ~3–5 min, needs internet)
Open **Termux** and paste:
```bash
curl -sL https://raw.githubusercontent.com/SapnilPatel/RescueNet/main/beacon/termux-setup.sh | bash
```
It installs Python, git and `termux-api`, downloads this repo, installs the beacon packages, writes `~/RescueNet/.env` pointing at the live HQ (https://rescuenet-r90o.onrender.com), and tests GPS at the end. Running it again later just updates the code.

## 3. Android 12 permissions (once)
- **Location on:** pull down quick settings → **Location** ON.
- **Termux:API location:** Settings → Apps → **Termux:API** → Permissions → **Location → Allow only while using the app** (or "Allow all the time" if offered) and **Use precise location ON**. Android may also pop this up the first time GPS is requested — tap **Allow**.
- **Keep it alive:** Settings → Apps → **Termux** → Battery → **Unrestricted**. Do the same for **Termux:API**.
- **Test:** in Termux run `termux-location -p network -r last` → it should print JSON with `latitude` / `longitude`. If it hangs, open the Termux:API app once and re-check the permission.

## 4. Run
```bash
~/start-beacon.sh
```
Leave Termux open. Within a few seconds it prints `[gps] 34.02…,-118.28… via termux-…` — **wait for that line before taking any SOS**, otherwise the first SOS has no map location (the victim's own description still goes through). GPS refreshes every 5 minutes. Check it in Chrome on the same phone: `http://127.0.0.1:8080` (SOS page) and `http://127.0.0.1:8080/api/beacon` (counts, last sync).

## 5. Hotspot = SOS-HELP
1. Settings → Connections → Mobile Hotspot → name **SOS-HELP**, security **Open** (no password) if allowed.
2. Turn **mobile data OFF** (not airplane mode — some phones disable the hotspot with it).
3. **Find the beacon's address:** join SOS-HELP from an iPhone → Settings → Wi-Fi → tap ⓘ next to SOS-HELP → **Router** (e.g. `192.168.43.1` or `10.x.x.1`). The SOS page is `http://<Router>:8080`. Make the QR code from that.

## 6. Demo walk ("the fire truck reaches signal")
1. Turn the hotspot **off** and join venue Wi-Fi (or turn mobile data on).
2. Within ~5 s the beacon uploads, most urgent first. Force it: `curl -X POST http://127.0.0.1:8080/api/sync` in a second Termux session.
3. After the dispatcher assigns a team, keep the beacon online until the next sync (~5 s), then turn SOS-HELP back on. The victim refreshes and sees "Help is on the way".

## Gotchas
- Victim's Android may say "No internet — stay connected?" → tap **Yes**.
- iPhone Safari blocks GPS on http pages, so location = the beacon's location + the victim's own description.
- No automatic sign-in popup from an Android hotspot; use the QR code.
- GPS indoors is weak: the beacon falls back to the network (Wi-Fi/cell) location, which is fine to the block level.
- If GPS can't work at all, a fixed fallback can be set in `~/RescueNet/.env` with `BEACON_LAT=` / `BEACON_LON=`.
