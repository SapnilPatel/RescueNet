# Decisions & Research Log

## Constraints
- International student on team → **no defense/marine/military** projects or funding (dropped Hull Shazam, ZoneLock, Seabed Diff, Fishfinder Network).
- Twists are optional — include naturally, don't force.

## Ideas considered and why rejected
| Idea | Verdict |
|---|---|
| **ColdChain Clock** (prioritize reefer containers' backup power by hours-to-spoilage) | Rejected. Monitoring already solved (Identec Reefer Runner at TTI/Ports America/APMT/PSA, Maersk RCM, Carrier Lynx, ORBCOMM, RTE); power-cycling studied (J. Cleaner Production 2018). 69% of reefer incidents happen at sea, only 22% at port. No public LA outage-spoilage data → weak story. Numbers: LA ~1.9M t reefer cargo/yr, LB ~1.7–1.8M (2018); Port of LA 9 power outages by Aug 2024; global 141M t containerized reefer 2024; avg reefer claim ~$38K. |
| **Water Pump Runway** | Rejected as framed. LADWP report: Palisades pumps shut from low pressure (demand + ~4,800 leaking connections), **not** power loss. |
| **Fire-Mode Water** (auto-isolate burned homes' service lines) | Backup idea. Real (3 × ~1M gal tanks ran dry overnight; Louisville CO installing remote shutoff valves ~$800/meter; Mandell patent proposal ~$15M). Weak vertical fit. |
| **Device Runway** (live battery countdown for electricity-dependent medical device users) | Strong alternative. >3M Medicare electricity-dependent (4.6M incl. dialysis/oxygen/home health/hospice); device batteries 3–8 h; CA PSPS avg ~41 h; outages 9% more frequent & 56% longer 2014–2023; emPOWER is Medicare-only, monthly, mostly aggregate. |
| Others brainstormed | TriageLine (Retell triage), Call Them First, Silent Caller Detection, Callers Are Sensors, Tower Lifeline, EV Lifeboats, Pause the GPUs, Ships as Power Plants, Port Freeze Insurance, Stranded Cargo Rescue, Cascade Engine, Dialysis Lifeline. |

## Final choice: RescueNet (mesh/beacon SOS) — see `02-rescuenet-concept.md`

## v1 blueprint critique (old "RescueNet AI" doc)
Strengths kept: honest delivery states (relayed ≠ HQ confirmed), AI never blocks SOS, store-and-forward + gateway, dedup IDs, expiry separate from hop count, metrics table, admits localhost UDP simulation.
Fixes: no Life #1; ignored prior art; no density/adoption analysis; "AI" overclaim (keyword rules); 8-phase scope too big; undefined HQ; loose message format (location optional); no battery/spam policy; no twists/partners; formatting bugs (broken nested code fence in §9, table header in §6, collapsed Phase 3 diagram).
Existing code: Python `node.py`, `schema.py`, `storage.py`, `transport.py` — schema, SQLite, 3-node UDP relay on 127.0.0.1, dedup, TTL, route tracing, priority outbox, keyword DelayAI/PanicAI.

## Corrections made during research
- "No app needed" overstated → victims need no app; relays/beacons do run our software.
- Satellite is not blocked by smoke; buildings/roofs/trees/terrain are.
- LA Jan 2025 fires: comms disruption described by FCC as minimal → use Maui/Helene as lead examples.

## Key sources
- Helene cell outages: https://wirelessestimator.com/articles/2024/unprecedented-outage-no-hurricane-has-knocked-out-more-cell-sites-than-category-4-helene/
- Maui comms breakdown: https://www.npr.org/2024/04/17/1245396324/maui-fire-report-communications-breakdown
- LA fires comms: https://wirelessestimator.com/articles/2025/mount-wilson-towers-remain-intact-as-fcc-reports-minimal-communication-disruptions-from-deadly-la-fires/
- Why P2P mesh chats failed: https://blakesnotes.io/wiki/bitmesh-hybrid-mesh-chat
- Mesh messengers overview: https://www.kaspersky.com/blog/mesh-messengers/54192/
- Bridgefy security analysis: https://eprint.iacr.org/2021/214
- T-Satellite vs Apple: https://tidbits.com/2025/08/08/how-t‑mobiles-new-t‑satellite-compares-with-apples-free-satellite-features/
- Satellite D2C limits: https://5gstore.com/blog/2026/06/30/starlink-vs-big-3-why-satellite-wont-replace-cell-towers/ (vendor source, treat as approximate)
- T-Mobile Helene satellite test: https://www.mobileworldlive.com/t-mobile-us/t-mobile-us-employs-test-sat-service-in-hurricane-response/
- Hackathon: https://www.cs.usc.edu/newsletter/ug-ms-phd-dual-use-hackathon-at-usc-on-oct-16-18/ · https://tally.so/r/7R0APa
- Das Family winners: https://viterbischool.usc.edu/news/2025/05/students-pitch-transformative-ventures-for-los-angeles-and-beyond/
- SBIR reauthorization: https://www.mondaq.com/unitedstates/government-contracts-procurement-ppp/1774902/sbirsttr-programs-reauthorized-after-six-month-lapse
- emPOWER: https://empowerprogram.hhs.gov/faqs.html
- LADWP Palisades report: https://ladwpnews.com/ladwp-palisades-fire-water-system-preliminary-report-july-3-2025/
