# Android beacon setup (Termux)

Needs **Android 7+** (tested target: Android 12). Only one app is required: **Termux**. No F-Droid store, no Play Store, no Termux:API (the beacon uses a fixed demo location instead of GPS).

## 1. Install Termux (on the phone, ~2 min)
1. In Chrome on the Android, open **https://github.com/termux/termux-app/releases/latest**.
2. Under **Assets**, download **`termux-app_..._github-debug_arm64-v8a.apk`** (almost every phone from the last 6+ years is arm64; if it won't install, try the `universal` APK).
3. Open the downloaded file. Allow **"Install unknown apps"** for Chrome when Android asks, then install.
4. Do **not** also install Termux from the Play Store (mixing sources breaks it).

## 2. Set up the beacon (one command, ~3–5 min, needs internet)
Open Termux and paste:
```bash
curl -sL https://raw.githubusercontent.com/SapnilPatel/RescueNet/main/beacon/termux-setup.sh | bash
```
It installs Python + git, downloads this repo, installs the beacon packages, and writes `~/RescueNet/.env` pointing at the live HQ (https://rescuenet-r90o.onrender.com). Running it again later just updates the code.

## 3. Android 12 settings (once)
- Settings → Apps → Termux → **Battery → Unrestricted** (otherwise Android may kill the beacon when the screen is off).
- Keep the Termux notification; `start-beacon.sh` takes a wake lock.

## 4. Run
```bash
~/start-beacon.sh
```
Leave Termux open. Check it in Chrome on the same phone: `http://127.0.0.1:8080` (SOS page) and `http://127.0.0.1:8080/api/beacon` (counts, last sync).

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
- Optional real GPS: install **Termux:API** from https://github.com/termux/termux-api/releases (same GitHub source as Termux), `pkg install termux-api`, then remove `BEACON_LAT`/`BEACON_LON` from `.env`.
