# HQ Identification & Two-Way Feedback Loop

## 1. How HQ knows WHO needs help and WHERE
SOS form fields (all tiny, ~150 B):
- **Status:** Trapped / Injured / Need evacuation / Safe
- **People count**, injured count, special needs (child, elderly, oxygen, wheelchair, pet)
- **Where exactly (required):** free-text landmark, e.g. "2nd floor, blue house, 123 Oak St, back bedroom"
- **Optional:** name + callback phone number (for family call / SMS when networks return)
- **Auto:** SOS short code (e.g. `A7K3`), timestamp, beacon ID, **beacon GPS**

Location precision (be honest in pitch): iPhone browsers block GPS on http pages, so location = **beacon GPS (person is within ~50–100 m Wi-Fi range) + their own description**. Fixed beacons have a known surveyed address. Enough for a crew to go to the right block and find the house.

HQ dashboard:
- Map pins per beacon area, incident cards sorted by AI severity.
- AI clusters: "Beacon 12 area: 5 SOS, 9 people, 2 trapped, 1 on oxygen."
- Dispatcher buttons: **Acknowledge → Assign team + ETA → Rescued/Closed.**

## 2. How victims know help is coming (reverse path)
Status stages shown to the victim:
1. **Saved on beacon** (instant)
2. **Delivered to HQ** (HQ ack received back on beacon)
3. **Help assigned** — team name + ETA
4. **Rescued / closed**

Mechanism: every upload from the beacon also **downloads acks/updates** for its SOS IDs (`GET /api/v1/updates?beacon_id=...`). The SOS-HELP page shows status by short code (stored in the phone's browser), so the victim reopens/refreshes the page to see updates.
- Beacon with live uplink (fixed beacon with Starlink/LoRa gateway): near real-time.
- Courier beacon (car/truck/our demo Android): update arrives when the courier returns — state this honestly.

Extra channels:
- **Retell call / SMS** to the callback number and family once any network returns.
- **Roadmap:** ESP32 beacons rename their Wi-Fi network as a billboard visible without connecting, e.g. "SOS-HELP | HELP COMING 15 MIN"; LED/buzzer on beacon.
- Responders mark **Rescued** on arrival, closing the incident.

## 3. Demo addition (closes the loop — strong for Best Demo)
After the Retell call rings, the dispatcher clicks **"Assign Engine 23 – ETA 15 min."** The teammate walks the Android back; the judge refreshes the SOS page → **"Help is on the way: Engine 23, ETA 15 min."**

## 4. API additions
- `POST /api/v1/incidents` — upload SOS (idempotent on message_id)
- `GET /api/v1/updates?beacon_id=X` — acks + assignments for that beacon's SOS IDs
- `POST /api/v1/incidents/{id}/assign` — dispatcher assigns team + ETA
- `POST /api/v1/incidents/{id}/close` — rescued/closed
