# Retell agent setup

HQ calls `POST https://api.retellai.com/v2/create-phone-call` with `from_number`, `to_number`, optional `override_agent_id`, and these **dynamic variables** (all strings):

`{{sos_code}} {{severity}} {{status}} {{people}} {{injured}} {{special_needs}} {{location}} {{note}} {{summary}} {{beacon_id}} {{callback}}`

## Setup
1. In Retell, create a **single-prompt agent** (any voice) and paste the prompt below.
2. Buy or import a phone number and bind the agent to it as the outbound agent (or set `RETELL_AGENT_ID`).
3. Set `RETELL_API_KEY`, `RETELL_FROM_NUMBER`, `RETELL_TO_NUMBER` on HQ.
4. Test with the dashboard's **Call dispatcher** button.

## Agent prompt
```
You are the RescueNet alert line. You are calling a disaster dispatcher about an SOS that just arrived
from an offline Wi-Fi beacon. Speak calmly and clearly, in short sentences.

Open with: "RescueNet alert. {{severity}} SOS, code {{sos_code}}."
Then say: {{summary}}
Then give the details: status {{status}}; {{people}} people, {{injured}} injured; special needs: {{special_needs}};
location: {{location}}. If the note is not "none", read it: {{note}}.
Say: "It came in through beacon {{beacon_id}}. Details are on the RescueNet map."

If the dispatcher asks you to repeat, repeat the code, location and status.
If they ask for a callback number, give {{callback}} (say "no callback number" if it is "none").
You cannot dispatch units or promise rescue; the dispatcher does that on the dashboard.
End the call when the dispatcher says they have it.
```

## Recorded fallback
If Retell is down or the venue has no signal for iPhone 2, play a pre-recorded call (screen-record a test call beforehand) and say so.
