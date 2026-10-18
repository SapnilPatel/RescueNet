"""Retell outbound voice call: the dispatcher's (or family's) phone rings and
the agent reads the SOS aloud using dynamic variables.

Env:
  RETELL_API_KEY      secret
  RETELL_FROM_NUMBER  Retell-purchased number, E.164 (+1...)
  RETELL_TO_NUMBER    dispatcher phone (iPhone 2), E.164
  RETELL_AGENT_ID     optional; overrides the agent bound to the from-number
"""
import os

import httpx

API = "https://api.retellai.com/v2/create-phone-call"


def configured():
    return bool(os.environ.get("RETELL_API_KEY") and os.environ.get("RETELL_FROM_NUMBER"))


def dynamic_variables(inc):
    needs = ", ".join(inc.get("needs") or []) or "none reported"
    return {  # Retell requires string values
        "sos_code": inc["short_code"],
        "severity": inc["severity"].upper(),
        "status": inc["status"],
        "people": str(inc["people"]),
        "injured": str(inc["injured"]),
        "special_needs": needs,
        "location": inc["landmark"],
        "note": inc.get("note") or "none",
        "summary": inc.get("ai_summary") or inc["summary"],
        "beacon_id": inc["beacon_id"],
        "callback": inc.get("callback") or "none",
    }


def place_call(inc, to_number=None):
    """Returns {"ok", "call_id"|"error", "to"}. Never raises."""
    to = to_number or os.environ.get("RETELL_TO_NUMBER")
    if not configured() or not to:
        return {"ok": False, "error": "Retell not configured (RETELL_API_KEY / RETELL_FROM_NUMBER / RETELL_TO_NUMBER)"}
    body = {
        "from_number": os.environ["RETELL_FROM_NUMBER"],
        "to_number": to,
        "retell_llm_dynamic_variables": dynamic_variables(inc),
        "metadata": {"message_id": inc["message_id"], "short_code": inc["short_code"]},
    }
    if os.environ.get("RETELL_AGENT_ID"):
        body["override_agent_id"] = os.environ["RETELL_AGENT_ID"]
    try:
        r = httpx.post(API, json=body, timeout=15,
                       headers={"Authorization": "Bearer " + os.environ["RETELL_API_KEY"]})
        if r.status_code >= 300:
            return {"ok": False, "error": "Retell HTTP %d: %s" % (r.status_code, r.text[:200]), "to": to}
        return {"ok": True, "call_id": r.json().get("call_id"), "to": to}
    except httpx.HTTPError as e:
        return {"ok": False, "error": "Retell request failed: %s" % e, "to": to}
