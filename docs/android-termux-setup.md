# Android beacon setup (Termux)

Needs **Android 7+**. Install Termux and Termux:API from **F-Droid** (or their GitHub releases), not the Play Store; the two must come from the same source.

## 1. Install (do this on venue Wi-Fi, once)
```bash
pkg update -y && pkg install -y python git termux-api
git clone https://github.com/SapnilPatel/RescueNet.git
cd RescueNet
pip install -r beacon/requirements.txt
termux-location -p network -r once     # grant location permission when prompted
```

## 2. Configure
```bash
cat > .env <<'EOF'
BEACON_ID=beacon-android-01
HQ_URL=https://rescuenet-r90o.onrender.com
BEACON_KEY=<same value as on Render, or leave empty>
SYNC_INTERVAL=5
EOF
```
If GPS is slow indoors, add `BEACON_LAT=` / `BEACON_LON=` as a fallback (the beacon still tries `termux-location`).

## 3. Run
```bash
termux-wake-lock            # keep running with the screen off
python beacon/app.py        # serves on port 8080
```
Leave this Termux session open. `http://127.0.0.1:8080/api/beacon` shows counts, GPS and last sync.

## 4. Hotspot = SOS-HELP
1. Settings → Hotspot → name **SOS-HELP**, **open** (no password) if your phone allows it, otherwise a simple printed password.
2. Turn **mobile data OFF** (don't use airplane mode — some phones disable the hotspot with it).
3. Find the phone's hotspot IP: `ip -4 addr show | grep inet` (often `192.168.43.1`; Samsung/Pixel can differ, e.g. `192.168.x.1`).
4. Make the QR code for `http://<that-ip>:8080` and print it or show it on a laptop.

## 5. Demo walk ("the fire truck reaches signal")
1. Turn the hotspot **off** and join venue Wi-Fi (or turn mobile data on).
2. Within `SYNC_INTERVAL` seconds the beacon uploads, most urgent first. Force it with `curl -X POST http://127.0.0.1:8080/api/sync`.
3. After the dispatcher assigns a team, keep the beacon online until the next sync has pulled the update, then turn the hotspot back on. The victim refreshes the page and sees "Help is on the way".

## Gotchas
- Android may say "No internet — stay connected?" on the victim's Android phone → tap **Yes**.
- iPhone Safari blocks GPS on http pages, so location = the beacon's GPS (victim is within Wi-Fi range) + the victim's own description.
- No automatic captive-portal popup from an Android hotspot (it doesn't hijack DNS); the probe routes are there for an ESP32/dnsmasq beacon later. Use the QR code.
