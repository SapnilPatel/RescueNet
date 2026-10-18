(function () {
  "use strict";
  var COLORS = { critical: "#e53935", high: "#fb8c00", medium: "#fdd835", low: "#43a047" };
  var params = new URLSearchParams(location.search);
  var token = params.get("token") || safeGet("rn_token") || "";
  if (params.get("token")) safeSet("rn_token", token);

  function safeGet(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function safeSet(k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  function el(tag, cls, text) { var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function ago(ts) {
    var s = Math.max(0, Math.floor(Date.now() / 1000 - ts));
    return s < 60 ? s + "s ago" : s < 3600 ? Math.floor(s / 60) + "m ago" : Math.floor(s / 3600) + "h ago";
  }

  var map = L.map("map").setView([34.0205, -118.2856], 15);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19, attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);
  var areaLayer = L.layerGroup().addTo(map);
  var fitted = false, seen = null, config = {};

  fetch("/api/v1/config").then(function (r) { return r.json(); }).then(function (c) {
    config = c;
    if (!fitted) map.setView(c.map_center, 15);
    var flags = document.getElementById("flags");
    [[c.claude_enabled ? "Rules + Claude triage" : "Rule triage", true], ["Retell calls", c.retell_enabled], ["Auto-call: " + c.auto_call, c.retell_enabled && c.auto_call !== "off"]]
      .forEach(function (f) { flags.appendChild(el("span", "flag" + (f[1] ? " on" : ""), f[0])); });
    if (c.dispatch_token_required && !token) {
      token = prompt("Dispatcher token") || "";
      safeSet("rn_token", token);
    }
  });

  function act(id, action, body) {
    return fetch("/api/v1/incidents/" + encodeURIComponent(id) + "/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Dispatch-Token": token },
      body: JSON.stringify(body || {})
    }).then(function (r) {
      return r.json().then(function (j) {
        if (!r.ok) alert(action + " failed: " + (j.detail || r.status));
        refresh();
      });
    });
  }

  var dlg = document.getElementById("assignDlg"), assignId = null;
  dlg.addEventListener("close", function () {
    if (dlg.returnValue !== "ok" || !assignId) return;
    var f = new FormData(document.getElementById("assignForm"));
    var eta = f.get("eta") === "" ? null : parseInt(f.get("eta"), 10);
    act(assignId, "assign", { team: f.get("team"), eta_min: eta });
    assignId = null;
  });

  function beep() {
    if (!document.getElementById("sound").checked) return;
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      [0, 0.25, 0.5].forEach(function (t) {
        var o = ctx.createOscillator(), g = ctx.createGain();
        o.frequency.value = 880; o.connect(g); g.connect(ctx.destination);
        g.gain.setValueAtTime(0.15, ctx.currentTime + t);
        g.gain.setValueAtTime(0, ctx.currentTime + t + 0.15);
        o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.16);
      });
    } catch (e) {}
  }

  function card(inc, fresh) {
    var c = el("div", "card " + inc.severity + (inc.dispatch_status === "closed" ? " closed" : "") + (fresh ? " fresh" : ""));
    var top = el("div", "top");
    top.appendChild(el("span", "sev " + inc.severity, inc.severity));
    top.appendChild(el("span", "code", inc.short_code));
    top.appendChild(el("span", "meta", inc.beacon_id));
    top.appendChild(el("span", "age", ago(inc.received_at)));
    c.appendChild(top);
    c.appendChild(el("div", "sum", inc.summary));
    if (inc.ai_summary) c.appendChild(el("div", "ai", "AI: " + inc.ai_summary));
    if (inc.ai_language && !/^en/i.test(inc.ai_language) && inc.ai_translation)
      c.appendChild(el("div", "ai", "Translated from " + inc.ai_language + ": " + inc.ai_translation));
    if (inc.note) c.appendChild(el("div", "meta", "Note: " + inc.note));
    var who = [];
    if (inc.name) who.push(inc.name);
    if (inc.callback) who.push("callback " + inc.callback);
    who.push("sent " + ago(inc.created_at) + " · route " + inc.hops.join(" → "));
    c.appendChild(el("div", "meta", who.join(" · ")));
    var ds = inc.dispatch_status === "assigned"
      ? "Assigned: " + inc.team + (inc.eta_min != null ? " · ETA " + inc.eta_min + " min" : "")
      : inc.dispatch_status.toUpperCase();
    c.appendChild(el("span", "ds " + inc.dispatch_status, ds));
    if (inc.call_status) c.appendChild(el("div", "meta", "Call: " + inc.call_status));

    var b = el("div", "btns");
    function btn(label, fn, cls) { var x = el("button", cls || "", label); x.onclick = fn; b.appendChild(x); }
    if (inc.dispatch_status === "new") btn("Acknowledge", function () { act(inc.message_id, "ack"); });
    if (inc.dispatch_status !== "closed") {
      btn("Assign team + ETA", function () {
        assignId = inc.message_id;
        dlg.returnValue = "";
        document.getElementById("assignCode").textContent = inc.short_code;
        dlg.showModal();
      }, "primary");
      btn("Rescued / Close", function () { if (confirm("Mark " + inc.short_code + " rescued/closed?")) act(inc.message_id, "close"); });
      btn("Call dispatcher", function () { act(inc.message_id, "call", { to: "dispatcher" }); });
      if (inc.callback) btn("Call victim", function () { act(inc.message_id, "call", { to: "callback" }); });
    }
    c.appendChild(b);
    return c;
  }

  function renderStats(list) {
    var open = list.filter(function (i) { return i.dispatch_status !== "closed"; });
    var count = function (f) { return open.filter(f).length; };
    var s = document.getElementById("stats");
    s.innerHTML = "";
    [["open SOS", open.length],
     ["critical", count(function (i) { return i.severity === "critical"; })],
     ["people", open.reduce(function (a, i) { return a + (i.status === "safe" ? 0 : i.people); }, 0)],
     ["unassigned", count(function (i) { return i.dispatch_status === "new" || i.dispatch_status === "acknowledged"; })]]
      .forEach(function (x) { var d = el("span", "stat"); d.appendChild(el("b", null, x[1])); d.appendChild(document.createTextNode(x[0])); s.appendChild(d); });
  }

  function renderAreas(areas) {
    areaLayer.clearLayers();
    var box = document.getElementById("areas");
    box.innerHTML = "";
    var pts = [];
    areas.forEach(function (a) {
      box.appendChild(el("div", null, a.summary));
      if (a.lat == null) return;
      pts.push([a.lat, a.lon]);
      L.circle([a.lat, a.lon], { radius: 80, color: COLORS[a.worst], fillOpacity: 0.12, weight: 1 }).addTo(areaLayer);
      L.circleMarker([a.lat, a.lon], { radius: 10 + Math.min(a.sos, 10) * 2, color: "#fff", weight: 2, fillColor: COLORS[a.worst], fillOpacity: 0.9 })
        .bindPopup(el("div", null, a.summary)).addTo(areaLayer);
    });
    if (!areas.length) box.appendChild(el("div", "empty", "No open SOS."));
    if (pts.length && !fitted) { map.fitBounds(pts, { maxZoom: 16, padding: [40, 40] }); fitted = true; }
  }

  function refresh() {
    var showClosed = document.getElementById("showClosed").checked;
    Promise.all([
      fetch("/api/v1/incidents").then(function (r) { return r.json(); }),
      fetch("/api/v1/areas").then(function (r) { return r.json(); })
    ]).then(function (res) {
      var all = res[0].incidents;
      var ids = {};
      var newCritical = false;
      all.forEach(function (i) {
        ids[i.message_id] = 1;
        if (seen && !seen[i.message_id] && i.severity === "critical") newCritical = true;
      });
      var list = document.getElementById("list");
      list.innerHTML = "";
      var shown = all.filter(function (i) { return showClosed || i.dispatch_status !== "closed"; });
      if (!shown.length) list.appendChild(el("p", "empty", "Waiting for SOS from beacons…"));
      shown.forEach(function (i) { list.appendChild(card(i, seen && !seen[i.message_id])); });
      if (newCritical) beep();
      seen = ids;
      renderStats(all);
      renderAreas(res[1].areas);
    }).catch(function () {});
  }

  document.getElementById("showClosed").onchange = refresh;
  refresh();
  setInterval(function () { if (!dlg.open) refresh(); }, 3000);
})();
