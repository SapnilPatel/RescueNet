# RescueNet v2 — Final Concept

## One-liner
When cell towers and internet go down, anyone can send an SOS from **any phone's browser** to a nearby **beacon / relay**, which stores it and carries or relays it to wherever there is connectivity. HQ receives it on a live map, AI ranks it, and a **Retell voice call** alerts the dispatcher and family.

**Correct wording (use this, not "no app needed"):**
"You don't need our app to be rescued — but someone near you does: a beacon, a fire truck, or a neighbor's phone. We make that 'someone' cheap and common, instead of asking everyone to download a disaster app."

## The problem (real numbers)
- **Hurricane Helene (2024):** 74% of cell sites in affected NC counties offline; peak 4,562 sites down (record).
- **Maui/Lahaina fire (2023):** cellular down → residents couldn't receive alerts; 911 overwhelmed; 101 deaths.
- **LA fires (Jan 2025):** FCC called comms disruption relatively minimal → **lead with Maui/Helene, not LA**.

## How it works
1. **Relays** — Android phones running our software (app/SDK) pass SOS packets phone-to-phone (Bluetooth / Wi-Fi Direct via Nearby Connections).
2. **No-install SOS** — a relay/beacon broadcasts open Wi-Fi **"SOS-HELP"**. Anyone joins (iPhone or Android), opens the page, taps Trapped / Injured / Safe + # people + note + landmark.
3. **Store-and-forward** — beacon saves every SOS (SQLite, unique IDs, dedup).
4. **Exit points** — any device that reaches cell/Wi-Fi/satellite uploads to HQ. **Cars and fire trucks act as couriers** (carry messages out of the dead zone).
5. **Beacons** — ~$30 LoRa boards (Meshtastic-compatible) + SOS-HELP Wi-Fi at schools, shelters, fire stations; km range.
6. **Tiny structured packets (~150 B)** — "Trapped" first, dedupe, rate limits, phones <20% battery stop relaying, signed packets.
7. **HQ** — AI clusters duplicate reports, translates, ranks severity, writes dispatch summary → live map + **Retell call** + SMS.

### User's phone vs. beacon
The user's phone never needs internet. It only hands the SOS to the beacon over SOS-HELP; the beacon does the rest.
- A phone joins one Wi-Fi at a time → user switches to SOS-HELP (their home Wi-Fi usually has no internet in a disaster anyway). Page says "Saved on beacon — you can leave this network."
- Android may ask "No internet — stay connected?" → tap Yes.
- Future scale idea: ISPs broadcast SOS-HELP as a second SSID on battery-backed home routers (precedent: Comcast's public "xfinitywifi" on home gateways).

### A → B → C scenarios (A in fire, B middle, C has internet)
- **B & C have our SDK in an everyday app** → relay is automatic, they don't need to know or do anything. Precedent: **Apple Find My / Google Find My Device** networks relay strangers' devices silently. Pitch: **"Find My for SOS."**
- **A has nothing, B has our software** → B auto-broadcasts SOS-HELP, A sends via browser.
- **Nobody has our software, no beacon** → it cannot work (no system can relay through phones with no software). Mitigation: fixed beacons, responder vehicles, satellite on A's phone if outdoors.

## Two Lives, One Tool
- **Life #1 (ordinary day):** relay SDK inside stadium / festival / campus (USC game days, **LA28 Olympics**) apps — message friends when crowds jam the network. Beacons at parks/trailheads = offline check-in & lost-hiker locator for rangers.
- **Life #2 (crisis):** same phones & beacons switch to SOS mode; anyone nearby can send SOS via SOS-HELP.

## Why it's different (competition)
| Existing | Problem | RescueNet |
|---|---|---|
| FireChat (shut 2019), Bridgefy (security flaws), bitchat (2025, vulns), Briar (Android only) | Everyone must pre-install a standalone disaster app; no everyday use; ~100 m range; iOS background limits | Victim needs only a browser; relays come from everyday-app SDKs + institutional beacons; gaps filled by LoRa, cars, trucks; iPhones only send |
| Meshtastic / goTenna | Extra hardware for every user | Hardware only at beacons; we interoperate with Meshtastic |
| Satellite to phone (Apple iPhone 14+, T-Mobile T-Satellite ~60+ models) | Needs open sky (fails indoors, under rubble, under trees/roofs); beam capacity ~low single-digit Mbps shared by everyone; newer phones only; Helene use was an early best-effort test | Works indoors for any phone; uses Starlink dishes on trucks/shelters as exit points |

Note: satellite is NOT blocked by smoke (earlier claim corrected) — blockers are buildings, roofs, trees, terrain.

**Judge line on satellite:** "Satellite-to-phone is amazing and we use it — but it needs open sky and a new phone, and one beam is shared by thousands. RescueNet gets the SOS from someone trapped indoors, on any phone, to the nearest fire truck with a Starlink dish."

## LoRa explained
- License-free long-range radio (915 MHz US): **1–5 km urban, 10+ km line of sight**, tiny messages (≤~255 B), days–weeks on battery.
- Phones can't do LoRa → needs a $20–40 board (Heltec LoRa 32, LilyGO T-Beam, RAK WisBlock) + free **Meshtastic** firmware (flash via flasher.meshtastic.org) + Meshtastic app for the operator only.
- Hackathon: pitch/poster/simulation only, not live demo (unless someone owns a board).

## How v2 beats v1 (old "RescueNet AI" blueprint)
- v1 needed everyone pre-installed → v2 victims use any browser.
- v1 had no everyday use → v2 has Life #1.
- v1 limited to ~100 m phone hops → v2 adds cars, trucks, LoRa beacons.
- v1 blocked by iOS background limits → iPhones only send; Android/beacons relay.
- v1 called keyword rules "AI" → v2 puts real AI at HQ; PanicAI cut; drop "AI" from name.
- v1 "HQ dashboard" undefined → v2 delivers via Retell call, SMS, map.
- v1 ignored competitors → v2 positions vs. bitchat, Meshtastic, satellite.
- v1 no battery/spam policy → v2: <20% battery stops relaying, signed packets, rate limits.
- v1 had 8 phases → v2 one demo-able core.

## Twists applied
- **Funding (civilian only):** FirstNet Authority, DHS Science & Technology (incl. Silicon Valley Innovation Program), NSF (SBIR, I-Corps via USC), NTIA. SBIR reauthorized through FY2031 (after ~6-month lapse) but requires majority US-citizen/permanent-resident ownership → NSF I-Corps via USC is easier for an international founder. Check with USC OIS.
- **Global:** Turkey–Syria earthquake 2023, Philippines typhoons, Helene-style tower collapse anywhere; runs on ordinary phones + cheap beacons.
- **Poster:** two-lives diagram, packet journey, comparison table, simulation chart, QR code to SOS page.

## Pitch line
"Satellite SOS needs open sky. Mesh apps need you to install them before the disaster. RescueNet needs neither."
