#!/data/data/com.termux/files/usr/bin/bash
# One-command beacon setup for Termux (Android 7+).
#   curl -sL https://raw.githubusercontent.com/SapnilPatel/RescueNet/main/beacon/termux-setup.sh | bash
# Safe to run again: it updates the code and keeps an existing .env.
set -e

echo "== Installing Python, git and termux-api (takes a few minutes the first time)"
pkg install -y python git termux-api

cd "$HOME"
if [ -d RescueNet/.git ]; then
  echo "== Updating RescueNet"
  git -C RescueNet pull --ff-only
else
  echo "== Downloading RescueNet"
  git clone https://github.com/SapnilPatel/RescueNet.git
fi
cd RescueNet

echo "== Installing beacon packages"
pip install -q -r beacon/requirements.txt

if [ ! -f .env ]; then
  echo "== Writing .env"
  cat > .env <<'EOF'
BEACON_ID=beacon-android-01
HQ_URL=https://rescuenet-r90o.onrender.com
SYNC_INTERVAL=5
EOF
fi

cat > "$HOME/start-beacon.sh" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
cd "$HOME/RescueNet"
termux-wake-lock 2>/dev/null || true
python beacon/app.py
EOF
chmod +x "$HOME/start-beacon.sh"

echo
echo "== Testing GPS (Termux:API). If this hangs or errors, check the Termux:API app + location permission."
timeout 30 termux-location -p network -r last || echo "   (no location yet - see docs/android-termux-setup.md step 3)"
echo
echo "Done. Start the beacon any time with:   ~/start-beacon.sh"
echo "Then open http://127.0.0.1:8080 in Chrome on this phone to check it."
