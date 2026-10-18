# RescueNet — Demo Video Production Brief

> **For the AI video platform.** This brief contains everything needed to produce a ~2:45 professional demo video for RescueNet, a hackathon project (Dual-Use Hackathon @ USC Viterbi, LA Tech Week, Oct 2026). Read every section. **Section 9 (Accuracy rules) is mandatory** — the video is judged on technical honesty, and several tempting visuals would be false.

---

## 1. One-paragraph summary of the product

When a disaster knocks out cell towers and internet, people trapped in their homes cannot call for help. **RescueNet** lets anyone send an SOS from the ordinary web browser on any phone — **no app install, no internet, no cell signal** — by joining a nearby open Wi-Fi network called **SOS-HELP**. That network is broadcast by a **beacon**: an Android phone running RescueNet software (in the product: a relay SDK inside everyday apps, plus cheap fixed beacons at schools and fire stations). The beacon **stores** every SOS and **carries or forwards** it until it touches any internet connection — a passer-by's phone hotspot, a fire truck, a shelter's satellite dish. The SOS then reaches **RescueNet HQ**, a live dispatcher dashboard that ranks it by urgency with **rule-based triage**, pins it on a map, and **rings the dispatcher's phone with a Retell AI voice call** that reads the SOS aloud. When the dispatcher assigns a rescue team, the update travels back the same way and the victim's screen changes to **"Help is on the way: Engine 23 · ETA 15 min."**

**Tagline (use in the video):** *"Satellite SOS needs open sky. Mesh apps need you to install them before the disaster. RescueNet needs neither."*
**Secondary line:** *"You don't need our app to be rescued — but someone near you does: a beacon, a fire truck, or a neighbor's phone."*

---

## 2. Why it matters (real facts — use exactly as written)

- **Hurricane Helene, 2024:** **74%** of cell sites in the hardest-hit North Carolina counties went offline; at the peak, **4,562** cell sites were down — a record.
- **Maui / Lahaina wildfire, 2023:** cellular service collapsed, residents never received alerts, 911 was overwhelmed; **101 people died**.
- Satellite-to-phone SOS exists but needs **open sky** (fails indoors, under roofs, rubble, trees), a **new phone**, and one satellite beam is shared by thousands.
- Mesh-chat apps (FireChat, Bridgefy, bitchat) require **everyone to install the same app before the disaster** — almost nobody does.

---

## 3. Video specifications

| Item | Value |
|---|---|
| Length | **2:30 – 2:50** |
| Aspect ratio | 16:9, 1080p (also export a 9:16 cut of scenes 4–8 if possible) |
| Tone | Cinematic, urgent but hopeful; documentary realism, not action-movie |
| Narration | One calm, warm, confident narrator (neutral American English). Spanish lines for Elena with English subtitles. |
| Music | Low, tense ambient pulse in the storm scenes → swells gently when "Help is on the way" appears → hopeful, minimal outro |
| Sound design | Rain, wind, distant sirens, water dripping, phone notification chimes, a phone ringing (the Retell call) |
| Color | Storm scenes: desaturated blue-grey, night. UI/HQ scenes: clean dark dashboard. Rescue/outro: warm dawn light. Brand accent: **emergency red #E53935**, secondary blue #4F8CFF |
| Typography | Clean sans-serif (Inter / SF Pro style). Lower-thirds white on 70% black. |
| Captions | Burned-in captions for all narration and dialogue (judges may watch muted) |

---

## 4. Setting and characters (fictional, civilian)

**Place:** *Mill Creek*, a fictional riverside neighborhood in western North Carolina. **Time:** 2:10 AM, the night a Helene-strength hurricane hits. Power is out. River water is rising into the streets. Every phone shows **"No Service"**.

| Character | Who | Device | Role in the chain |
|---|---|---|---|
| **Elena Ruiz** (68) | Grandmother, Spanish speaker, on **home oxygen (about 3 hours of battery left)**, trapped on the 2nd floor with grandson **Mateo (9)** as water climbs the stairs | **iPhone**, no RescueNet app, "No Service" | **Victim / sender (X)** |
| **Dev Patel** (21) | College student, **broken ankle**, alone on the top floor of an apartment building | Android phone, no RescueNet app | Second victim |
| **The Okafor family** (4) | Grandfather uses a **wheelchair**, family dog; their car flooded | iPhone | Third victim — need evacuation |
| **The Chen family** (3) | Already safe at the school shelter | iPhone | Sends an "I'm safe" check-in (shows the system also reduces panic calls) |
| **Marcus Hill** (35) | Neighbor, high-school coach. His Android runs RescueNet (in the product: inside an everyday app; in our demo: Termux) | **Android = the beacon** | **Beacon / courier (Y)** |
| **Priya Nair** (29) | Power-company line worker parked on the ridge road with one bar of LTE | Any phone with a normal **hotspot** — **no RescueNet app** | **Internet exit point (Z)** |
| **Sam Torres** (40s) | Dispatcher at the county Emergency Operations Center | Laptop with **RescueNet HQ** dashboard + a phone | **HQ / dispatcher** |
| **Engine 23** | County fire-rescue crew with a high-water vehicle | — | Rescuers |

The chain the video must make crystal clear:
```
Elena (iPhone, browser only) ──Wi-Fi "SOS-HELP"──▶ Marcus's Android beacon (stores + carries)
        ──joins Priya's phone hotspot──▶ internet ──▶ RescueNet HQ (map, triage, Retell call)
        ──▶ dispatcher assigns Engine 23 ──▶ update flows back ──▶ Elena's screen: "Help is on the way"
```

---

## 5. Scene-by-scene script (with timings, visuals, narration, exact on-screen text)

### Scene 1 — Cold open: the blackout (0:00–0:15)
**Visual:** Night. Heavy rain on a window. Power out. Dark street with water rising past mailboxes. Inside, close-up of an iPhone lock screen: status bar shows **"No Service"**, time **2:10 AM**, battery 41%. Elena (68) sits on a bed holding the phone; the clear tube of her **oxygen concentrator** is visible; Mateo (9) holds a flashlight. Water sound from the stairwell.
**Elena (Spanish, subtitled):** *"No hay señal… no puedo llamar a nadie."* → subtitle: *"No signal… I can't call anyone."*
**On-screen text (fade in):** *Hurricane Helene, 2024: 74% of cell sites in the hardest-hit NC counties went dark.*

### Scene 2 — The problem (0:15–0:30)
**Visual:** Quick montage: a dead cell tower against storm clouds; a "Call failed" screen; a satellite icon with a roof and trees crossing it out; an app-store page with "Download required" crossed out.
**Narrator:** *"When towers fail, 911 goes silent. Satellite SOS needs open sky — not a bedroom under a roof. And mesh-chat apps only work if everyone installed them before the storm. Almost no one did."*
**On-screen text:** *Maui 2023: cell service collapsed. Alerts never arrived. 101 lives lost.*

### Scene 3 — The beacon next door (0:30–0:45)
**Visual:** Next house over. Marcus checks his Android. On screen, a small status: **"RescueNet beacon active · SOS-HELP"**. His phone's hotspot list shows the network name **SOS-HELP**.
**Narrator:** *"But Elena's neighbor Marcus carries a RescueNet beacon — software on an ordinary Android phone. It broadcasts an open Wi-Fi network called SOS-HELP. No internet. Just a place to leave an SOS."*

### Scene 4 — Elena sends the SOS, no app (0:45–1:10)
**Visual:** Elena's iPhone → Settings → Wi-Fi list shows **SOS-HELP**. She taps it. Mateo scans a QR code from a "SOS-HELP" flyer taped to the window across the street (in the product this page pops up automatically like airport Wi-Fi — see Accuracy rules). Safari opens the RescueNet SOS page — **in Spanish**, because her phone is set to Spanish.

**SOS page (use the real screenshot; Spanish version):**
- Title (red): **"SOS — Pedir ayuda"**
- Subtitle: *"Funciona sin internet. Tu mensaje se guarda en esta baliza y se lleva a los rescatistas."*
- Four large buttons: **Atrapado** (red when selected) · **Herido** · **Necesito evacuar** · **Estoy a salvo** → she taps **Atrapado**
- **"¿Dónde estás exactamente? (obligatorio)"** → she types: *"Casa amarilla, 2do piso, 41 Mill Creek Rd, cuarto de atrás"*
- **Personas contigo:** 2 · **Heridos:** 0
- **Necesidades especiales:** ✔ Niño · ✔ Adulto mayor · ✔ Oxígeno / equipo médico
- Note: *"El agua sube por la escalera. Oxígeno para 3 horas."*
- Big red button: **ENVIAR SOS**

**After tapping:** a card appears — **"Tu código: K7QM"**, a 4-step progress bar with **step 1 filled**, and the text **"Guardado en la baliza — aún no entregado. Se enviará cuando la baliza tenga señal."** (English subtitle: *"Saved on beacon — not yet delivered. It will upload as soon as this beacon reaches signal."*)
**Narrator:** *"No app. No account. No signal. Just a browser. And RescueNet never pretends: this SOS is saved on the beacon — not delivered — and Elena can see exactly that."*

### Scene 5 — More SOS arrive at the same beacon (1:10–1:20)
**Visual:** Split screen, three phones lighting up in different homes, each on SOS-HELP:
- Dev (Android): **Injured** — *"Riverside Apts B, unit 3C, top floor"* — note *"Broken ankle, cannot walk. Bleeding stopped."*
- Okafor family (iPhone): **Need evacuation**, 4 people, ✔ Wheelchair ✔ Pet — *"Blue duplex, 18 Mill Creek Rd, porch"*
- Chen family: **I'm safe**, 3 people — *"Lincoln Elementary gym"*
Then Marcus's beacon screen: **"4 SOS stored · 0 delivered · waiting for signal"**.
**Narrator:** *"One beacon, four homes, ten people — all waiting in a dead zone."*

### Scene 6 — The courier and a stranger's hotspot (1:20–1:40)
**Visual:** Marcus wades to his truck and drives up the ridge road. Headlights find a power-company truck. Priya, the line worker, has one bar of LTE and her phone hotspot on. Marcus's Android joins **Priya's hotspot** from the Wi-Fi list. Within seconds his beacon shows **"HQ connected ✓ · uploaded 4"** — the **trapped** SOS goes first.
**Narrator:** *"Marcus drives toward the ridge. Priya doesn't have RescueNet — she doesn't need it. Her phone's ordinary hotspot is enough. The moment the beacon touches internet, it uploads every SOS — most urgent first."*
**On-screen label (small):** *Victim → beacon → any internet → HQ. Only the beacon runs RescueNet.*

### Scene 7 — HQ: triage, map, and the Retell call (1:40–2:05)
**Visual:** County EOC at night. Sam's laptop shows **RescueNet HQ** (use the real dashboard screenshot/recording). A red pin appears on the map at Mill Creek; a soft triple beep plays.

**Dashboard (exact text):**
- Header: **RescueNet HQ** · **4** open SOS · **1** critical · **7** people · **4** unassigned · badges **"Rule triage"** · **"Retell calls: ON · 12 min left"** (red pill)
- Top card (red edge): **CRITICAL** · **K7QM** · beacon-millcreek-07
  *"TRAPPED · 2 people · oxygen/medical device, child, elderly, agua sub · at Casa amarilla, 2do piso, 41 Mill Creek Rd, cuarto de atrás"*
  Note: *"El agua sube por la escalera. Oxígeno para 3 horas."* · route: **beacon-millcreek-07 → hq** · status **NEW**
  Buttons: **Acknowledge** · **Assign team + ETA** (blue) · **Rescued / Close** · **Call dispatcher**
- Second card: **HIGH** · *"INJURED · 1 person (1 injured) · bleed · at Riverside Apts B, unit 3C, top floor"*
- Third card: **HIGH** · *"NEEDS EVACUATION · 4 people · wheelchair, flood · at Blue duplex, 18 Mill Creek Rd, porch"*
- Fourth card: **LOW** · *"SAFE · 3 people · at Lincoln Elementary gym"*
- Cluster line under the map: **"beacon-millcreek-07 area: 4 SOS, 7 people, 1 trapped, 1 injured, 1 child, 1 elderly, 1 on oxygen, 1 pet, 1 wheelchair"**

**Then Sam's phone rings** — caller "RescueNet Alert". He answers on speaker. A calm AI voice (Retell):
*"RescueNet alert. CRITICAL SOS, code K7QM. Trapped, two people, oxygen and medical device, child, elderly. Location: Casa amarilla, second floor, 41 Mill Creek Road, back bedroom. Note: water is rising up the stairs, oxygen for three hours. It came in through beacon Mill Creek 07. Details are on the RescueNet map."*
**Narrator:** *"HQ ranks every SOS instantly with transparent rules — trapped, oxygen, a child, rising water: critical. And because nobody can watch a screen every second, Retell turns the most urgent one into a phone call."*

### Scene 8 — Assign, and the answer travels back (2:05–2:25)
**Visual:** Sam clicks **Assign team + ETA** → dialog: Team **"Engine 23"**, ETA **15** → **Assign**. Card status turns green: **"Assigned: Engine 23 · ETA 15 min"**. Cut to Marcus's beacon: **"updates received: 1"**. Marcus drives back down; his beacon's SOS-HELP is on again. Cut to Elena's phone: she pulls to refresh. Progress bar fills to **step 3**, card turns green:
**"La ayuda viene en camino: Engine 23 · llega en 15 min"** (subtitle: *"Help is on the way: Engine 23 · ETA 15 min"*).
Elena exhales, hugs Mateo.
**Narrator:** *"The answer rides back the same way. For the first time all night, Elena knows someone is coming."*

### Scene 9 — Rescue (2:25–2:32)
**Visual:** Dawn light. Engine 23's high-water truck at the yellow house; firefighters help Elena (with her oxygen) and Mateo into the truck. Sam clicks **Rescued / Close**; the card greys out.
**Narrator:** *"Engine 23 arrives with time to spare."*

### Scene 10 — Scale and the two lives (2:32–2:45)
**Visual:** The real simulation chart (`sim/out/delivery_vs_adoption.png`): three lines — grey "Phones only", blue "+ LoRa beacons", red "+ evacuating cars".
**On-screen text:** *16 km² dead zone · 300 trapped people · 60 minutes. With 5% of phones carrying RescueNet and cars carrying messages out: ~91% of SOS reach responders. Victims install nothing.*
Then quick cut: a packed stadium / music festival (no signal bars) where friends message each other through the same relay — **"Life #1: crowds jam the network every weekend. Life #2: the same phones and beacons save lives when the towers fall."**
**Narrator:** *"Every day, RescueNet keeps friends connected when crowds jam the network. On the worst day, it's already in everyone's pocket."*

### Scene 11 — Close (2:45–2:50)
**Visual:** Black screen, red RescueNet wordmark with a small radio-wave icon.
**Text:** *"Satellite SOS needs open sky. Mesh apps need you to install them before the disaster. RescueNet needs neither."*
Small text: *RescueNet · Dual-Use Hackathon @ USC Viterbi · github.com/SapnilPatel/RescueNet*

---

## 6. Full narration (continuous, for the voice track)

> When towers fail, 911 goes silent. Satellite SOS needs open sky — not a bedroom under a roof. And mesh-chat apps only work if everyone installed them before the storm. Almost no one did.
>
> But Elena's neighbor Marcus carries a RescueNet beacon — software on an ordinary Android phone. It broadcasts an open Wi-Fi network called SOS-HELP. No internet. Just a place to leave an SOS.
>
> No app. No account. No signal. Just a browser. And RescueNet never pretends: this SOS is saved on the beacon — not delivered — and Elena can see exactly that.
>
> One beacon, four homes, ten people — all waiting in a dead zone.
>
> Marcus drives toward the ridge. Priya doesn't have RescueNet — she doesn't need it. Her phone's ordinary hotspot is enough. The moment the beacon touches internet, it uploads every SOS — most urgent first.
>
> HQ ranks every SOS instantly with transparent rules — trapped, oxygen, a child, rising water: critical. And because nobody can watch a screen every second, Retell turns the most urgent one into a phone call.
>
> The answer rides back the same way. For the first time all night, Elena knows someone is coming.
>
> Engine 23 arrives with time to spare.
>
> Every day, RescueNet keeps friends connected when crowds jam the network. On the worst day, it's already in everyone's pocket.
>
> Satellite SOS needs open sky. Mesh apps need you to install them before the disaster. RescueNet needs neither.

---

## 7. Key messages the viewer must leave with (in priority order)

1. Victims need **only a browser** — no app, no internet, no signal.
2. The SOS is **stored and carried** by a beacon until it touches **any** internet — even a stranger's ordinary hotspot.
3. RescueNet is **honest about delivery**: "saved on beacon" ≠ "delivered"; "delivered" only after HQ confirms.
4. HQ **ranks by urgency** (rule-based) and **Retell calls** the dispatcher for critical SOS.
5. The loop **closes**: the victim sees "Help is on the way" with team and ETA.
6. It **scales** (simulation) and has an **everyday use** (crowded events), so it's already installed when disaster hits.

---

## 8. Assets we will supply (use these instead of inventing UI)

| Asset | Where | Use in |
|---|---|---|
| SOS page screenshots / screen recording (English + Spanish) | recorded on iPhone from the real beacon | Scenes 4, 5, 8 |
| HQ dashboard screen recording (cards, map pin, Assign dialog, closed state) | https://rescuenet-r90o.onrender.com | Scenes 7, 8, 9 |
| Real Retell call audio (if available) or the script in Scene 7 | recorded on the dispatcher phone | Scene 7 |
| Simulation chart | `sim/out/delivery_vs_adoption.png` in the GitHub repo | Scene 10 |
| Termux / beacon terminal (optional, small inset) | recorded on the Android | Scene 6 |
| Beacon status screen ("RescueNet beacon active · 4 SOS stored…") | **not built yet — illustrative**; keep it simple and small | Scenes 3, 5, 6, 8 |

If a real asset is missing, recreate the UI **exactly** with the text in Section 5 — same wording, same colors (red #E53935 critical, orange #FB8C00 high, yellow #FDD835 medium, green #43A047 low; dark dashboard background #0F1115).

---

## 9. Accuracy rules — DO NOT violate

1. **No military, defense, police-tactical, or weapons imagery.** Civilian disaster response only (fire-rescue, county emergency operations, utility workers, neighbors).
2. **Don't show iPhones relaying messages to other phones.** iPhones only *send*. The beacon (Android / fixed beacon) is the only device that stores and forwards.
3. **Don't show an automatic pop-up of the SOS page in the live demo.** In the demo, people scan a QR code. You *may* say: "Production beacons open the SOS page automatically, like airport Wi-Fi."
4. **Don't call the triage "AI".** Say **"rule-based triage"** or "ranks by urgency". The **voice call** is by **Retell AI** — that's the only AI in the product.
5. **Never show "Delivered" before HQ confirms.** Sequence must be: *Saved on beacon* → *Delivered to HQ* → *Help assigned* → *Rescued*.
6. **Don't show satellites delivering the SOS** or claim satellite is blocked by smoke. Satellite is mentioned only as a limitation (needs open sky, new phones).
7. **Say "You don't need our app to be rescued"**, never just "no app needed" — the beacon does run our software.
8. **Priya (Z) has no RescueNet app** — she only turns on a normal hotspot. Make this explicit.
9. **Don't promise the victim is called back automatically** or that family gets texts — not built.
10. **Use the statistics exactly as given** (74%, 4,562, 101, ~91% at 5% adoption). Don't invent other numbers. Don't use the 2025 LA fires as an example of comms failure.
11. **Show honest latency:** the update reaches the victim only when the courier beacon is back in range ("the answer rides back the same way").
12. All people and places are **fictional**; no real company logos except Retell named in narration.

---

## 10. On-screen glossary (optional end-card or tooltip overlays)

- **Beacon:** a phone or $5–30 device running RescueNet that broadcasts SOS-HELP Wi-Fi, stores SOS, and forwards them.
- **Store-and-forward:** keep the message safely until any route to the internet appears.
- **Courier:** a beacon that physically carries messages out of the dead zone (car, fire truck).
- **HQ:** the dispatcher dashboard (map, ranked SOS cards, assign/close buttons).
- **Retell:** the voice-AI service that phones the dispatcher with the SOS details.
- **LoRa (roadmap):** long-range radio boards (1–5 km in cities) that link fixed beacons.
