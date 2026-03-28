const MSG = {
  JOIN_ROOM: "JOIN_ROOM",
  PLACE_BET: "PLACE_BET",
  CANCEL_BET: "CANCEL_BET",
  CHAT_SEND: "CHAT_SEND",
  REDEEM_COUPON: "REDEEM_COUPON",
  ADMIN_ACTION: "ADMIN_ACTION",
  ROOM_STATE: "ROOM_STATE",
  GAME_START: "GAME_START",
  RACE_RESULT: "RACE_RESULT",
  LEADERBOARD_UPDATE: "LEADERBOARD_UPDATE",
  CHAT_EVENT: "CHAT_EVENT",
  SENTIMENT_UPDATE: "SENTIMENT_UPDATE",
  NOTIFICATION: "NOTIFICATION",
  BET_RESULT: "BET_RESULT",
  ADMIN_RESULT: "ADMIN_RESULT",
  ERROR: "ERROR",
};

const TRACK = {
  width: 940,
  height: 720,
  outerX: 42,
  outerY: 42,
  outerW: 840,
  outerH: 684,
  innerX: 242,
  innerY: 202,
  innerW: 440,
  innerH: 364,
  laneCount: 5,
  carW: 26,
  carH: 14,
};

const BUILD_VERSION = "web-20260328-r1";
const COUNTDOWN_SECONDS = 5;
const ENDPOINT_STORAGE_KEY = "domoneyracing_endpoints_v3";
const CONSENT_STORAGE_KEY = "domoneyracing_consent_v1";

const DEFAULT_PUBLIC_ENDPOINTS = [
  "wss://misfashioned-nora-unuxoriously.ngrok-free.dev",
  "wss://domoneyracing-default-rtdb.firebaseio.com/.ws",
];
const GOOGLE_FALLBACK_ENDPOINT = "wss://domoneyracing-default-rtdb.firebaseio.com/.ws";

const appState = {
  ws: null,
  connectedEndpoint: null,
  playerId: null,
  connecting: false,
  manualDisconnect: false,
  state: null,
  leaderboard: [],
  chatEvents: [],
  notifications: [],
  sentiment: "Waiting for sentiment signal...",
  selectedCar: "car1",
  selectedAmount: 50,
  selectedRigCar: "car1",
  warning: { x: 80, y: 70, vx: 2.4, vy: 1.9 },
  endpointItems: [],
  overlayEvents: [],
  audioEnabled: false,
  musicEnabled: false,
  audioCtx: null,
  musicTimer: null,
  lastPhase: "WAITING",
  lastCountdownBeep: -1,
  consentAccepted: false,
};

const els = {
  appShell: document.querySelector(".app-shell"),
  canvas: document.getElementById("raceCanvas"),
  consentOverlay: document.getElementById("consentOverlay"),
  consentEducation: document.getElementById("consentEducation"),
  consentAge: document.getElementById("consentAge"),
  consentAcceptBtn: document.getElementById("consentAcceptBtn"),
  consentDeclineBtn: document.getElementById("consentDeclineBtn"),
  connectBtn: document.getElementById("connectBtn"),
  reconnectBtn: document.getElementById("reconnectBtn"),
  placeBetBtn: document.getElementById("placeBetBtn"),
  queueBetBtn: document.getElementById("queueBetBtn"),
  cancelBetBtn: document.getElementById("cancelBetBtn"),
  askAiBtn: document.getElementById("askAiBtn"),
  chatSendBtn: document.getElementById("chatSendBtn"),
  chatInput: document.getElementById("chatInput"),
  nameInput: document.getElementById("nameInput"),
  roomInput: document.getElementById("roomInput"),
  endpointOptions: document.getElementById("endpointOptions"),
  customEndpointInput: document.getElementById("customEndpointInput"),
  addEndpointBtn: document.getElementById("addEndpointBtn"),
  addGgEndpointBtn: document.getElementById("addGgEndpointBtn"),
  resetEndpointsBtn: document.getElementById("resetEndpointsBtn"),
  connectCard: document.getElementById("connectCard"),
  carButtons: document.getElementById("carButtons"),
  amountButtons: document.getElementById("amountButtons"),
  walletBox: document.getElementById("walletBox"),
  sentimentBox: document.getElementById("sentimentBox"),
  rankingList: document.getElementById("rankingList"),
  leaderboardList: document.getElementById("leaderboardList"),
  chatLog: document.getElementById("chatLog"),
  notificationList: document.getElementById("notificationList"),
  betModeBox: document.getElementById("betModeBox"),
  connBadge: document.getElementById("connBadge"),
  phaseBadge: document.getElementById("phaseBadge"),
  raceMeta: document.getElementById("raceMeta"),
  endpointMeta: document.getElementById("endpointMeta"),
  formulaBox: document.getElementById("formulaBox"),
  adminTokenInput: document.getElementById("adminTokenInput"),
  adminMultiplierInput: document.getElementById("adminMultiplierInput"),
  adminRigButtons: document.getElementById("adminRigButtons"),
  adminPanel: document.getElementById("adminPanel"),
  setMultiplierBtn: document.getElementById("setMultiplierBtn"),
  setRigBtn: document.getElementById("setRigBtn"),
  clearRigBtn: document.getElementById("clearRigBtn"),
  adminPlayerInput: document.getElementById("adminPlayerInput"),
  adminDeltaInput: document.getElementById("adminDeltaInput"),
  adjustMoneyBtn: document.getElementById("adjustMoneyBtn"),
  audioToggleBtn: document.getElementById("audioToggleBtn"),
  musicToggleBtn: document.getElementById("musicToggleBtn"),
};

const ctx = els.canvas.getContext("2d");

function nowStr() {
  return new Date().toLocaleTimeString();
}

function hasSavedConsent() {
  return localStorage.getItem(CONSENT_STORAGE_KEY) === "accepted";
}

function setConsentLocked(locked) {
  if (document.body) {
    document.body.classList.toggle("consent-locked", locked);
  }
  if (els.appShell) {
    els.appShell.classList.toggle("locked", locked);
  }
  if (els.consentOverlay) {
    els.consentOverlay.classList.toggle("hidden", !locked);
  }
}

function updateConsentAcceptButton() {
  if (!els.consentAcceptBtn) return;
  const ok = !!(els.consentEducation?.checked && els.consentAge?.checked);
  els.consentAcceptBtn.disabled = !ok;
}

function initConsentGate() {
  const saved = hasSavedConsent();
  appState.consentAccepted = saved;
  setConsentLocked(!saved);

  if (saved) {
    return true;
  }

  els.consentEducation?.addEventListener("change", updateConsentAcceptButton);
  els.consentAge?.addEventListener("change", updateConsentAcceptButton);
  updateConsentAcceptButton();

  els.consentAcceptBtn?.addEventListener("click", () => {
    if (!els.consentEducation?.checked || !els.consentAge?.checked) {
      return;
    }
    appState.consentAccepted = true;
    localStorage.setItem(CONSENT_STORAGE_KEY, "accepted");
    setConsentLocked(false);
    pushNotification("ok", "Consent accepted. You can now connect and play.");
    connectAndJoin(false);
  });

  els.consentDeclineBtn?.addEventListener("click", () => {
    appState.consentAccepted = false;
    setConsentLocked(true);
    pushNotification("warn", "Consent is required to use this simulation.");
  });

  return false;
}

function pushNotification(kind, text) {
  appState.notifications.push({ kind: kind || "info", text: text || "", ts: nowStr() });
  appState.notifications = appState.notifications.slice(-28);
  renderNotifications();
}

function pushOverlay(kind, text, durationMs = 3400) {
  if (!text) return;
  appState.overlayEvents.push({
    kind: kind || "info",
    text,
    started: performance.now(),
    duration: durationMs,
  });
  appState.overlayEvents = appState.overlayEvents.slice(-6);
}

function cleanOverlayEvents() {
  const now = performance.now();
  appState.overlayEvents = appState.overlayEvents.filter((ev) => now - ev.started < ev.duration);
}

function normalizeEndpoint(url) {
  let value = String(url || "").trim();
  if (!value) return "";

  if (value.startsWith("https://")) {
    value = `wss://${value.slice("https://".length)}`;
  } else if (value.startsWith("http://")) {
    value = `ws://${value.slice("http://".length)}`;
  } else if (!value.startsWith("ws://") && !value.startsWith("wss://") && !value.includes("://")) {
    value = `wss://${value}`;
  }

  if (value.endsWith("/")) {
    value = value.slice(0, -1);
  }
  return value;
}

function isBlockedEndpoint(url) {
  return false;
}

function uniqueEndpointList(list) {
  const seen = new Set();
  const out = [];
  for (const raw of list) {
    const endpoint = normalizeEndpoint(raw);
    if (!endpoint || seen.has(endpoint.toLowerCase()) || isBlockedEndpoint(endpoint)) continue;
    seen.add(endpoint.toLowerCase());
    out.push(endpoint);
  }
  return out;
}

function saveEndpointList() {
  localStorage.setItem(
    ENDPOINT_STORAGE_KEY,
    JSON.stringify(appState.endpointItems.map((e) => e.url)),
  );
}

function loadEndpointList() {
  const saved = localStorage.getItem(ENDPOINT_STORAGE_KEY) || localStorage.getItem("domoneyracing_endpoints_v2");
  let endpoints = [];
  if (saved) {
    try {
      endpoints = JSON.parse(saved);
    } catch (err) {
      endpoints = [];
    }
  }

  if (!Array.isArray(endpoints) || !endpoints.length) {
    endpoints = [...DEFAULT_PUBLIC_ENDPOINTS];
  }

  endpoints = endpoints.map((u) => normalizeEndpoint(u)).filter(Boolean);

  for (const defaultUrl of DEFAULT_PUBLIC_ENDPOINTS) {
    const normalizedDefault = normalizeEndpoint(defaultUrl);
    if (!endpoints.some((u) => normalizeEndpoint(u).toLowerCase() === normalizedDefault.toLowerCase())) {
      endpoints.push(normalizedDefault);
    }
  }

  if (!endpoints.some((u) => normalizeEndpoint(u).toLowerCase() === GOOGLE_FALLBACK_ENDPOINT.toLowerCase())) {
    endpoints.push(GOOGLE_FALLBACK_ENDPOINT);
  }

  const isLocalBrowser = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1";
  if (isLocalBrowser) {
    endpoints.push("ws://localhost:8765");
  }

  endpoints = uniqueEndpointList(endpoints);
  if (!isLocalBrowser) {
    endpoints = endpoints.filter((u) => {
      const lower = String(u || "").toLowerCase();
      return !lower.startsWith("ws://localhost") && !lower.startsWith("ws://127.0.0.1");
    });
  }
  if (!endpoints.length) {
    endpoints = [...DEFAULT_PUBLIC_ENDPOINTS];
  }

  appState.endpointItems = endpoints.map((url, idx) => ({
    url,
    status: "idle",
    selected: idx === 0,
    reason: "",
  }));
}

function renderEndpointOptions() {
  els.endpointOptions.innerHTML = "";
  appState.endpointItems.forEach((item, idx) => {
    const row = document.createElement("div");
    row.className = `endpoint-item ${item.selected ? "active" : ""} ${item.status}`;
    row.title = item.reason || "Click to prioritize this endpoint";

    const dot = document.createElement("span");
    dot.className = "endpoint-dot";

    const text = document.createElement("span");
    text.className = "endpoint-text";
    const tag = item.selected ? "[FIRST]" : `[${idx + 1}]`;
    const isGg = normalizeEndpoint(item.url).toLowerCase() === GOOGLE_FALLBACK_ENDPOINT.toLowerCase();
    const pretty = isGg ? `${item.url} [GG Google fallback]` : item.url;
    text.textContent = item.reason ? `${tag} ${pretty} (${item.reason})` : `${tag} ${pretty}`;

    row.appendChild(dot);
    row.appendChild(text);
    row.addEventListener("click", () => {
      appState.endpointItems.forEach((x) => {
        x.selected = false;
      });
      appState.endpointItems[idx].selected = true;
      renderEndpointOptions();
      saveEndpointList();
    });

    els.endpointOptions.appendChild(row);
  });
}

function addEndpointOption(url, makeFirst = false) {
  const normalized = normalizeEndpoint(url);
  if (!normalized) return false;

  const existing = appState.endpointItems.find((e) => e.url.toLowerCase() === normalized.toLowerCase());
  if (existing) {
    if (makeFirst) {
      appState.endpointItems.forEach((e) => {
        e.selected = false;
      });
      existing.selected = true;
    }
    renderEndpointOptions();
    saveEndpointList();
    return false;
  }

  appState.endpointItems.push({ url: normalized, status: "idle", selected: false, reason: "" });
  if (makeFirst) {
    appState.endpointItems.forEach((e) => {
      e.selected = false;
    });
    appState.endpointItems[appState.endpointItems.length - 1].selected = true;
  }

  saveEndpointList();
  renderEndpointOptions();
  return true;
}

function getAttemptOrder() {
  const selected = appState.endpointItems.filter((e) => e.selected);
  const others = appState.endpointItems.filter((e) => !e.selected);
  return [...selected, ...others];
}

function setEndpointStatus(url, status, reason = "") {
  const item = appState.endpointItems.find((e) => e.url === url);
  if (!item) return;
  item.status = status;
  item.reason = reason;
  renderEndpointOptions();
}

function setConnectionBadge(isOnline) {
  els.connBadge.textContent = isOnline ? "CONNECTED" : "DISCONNECTED";
  els.connBadge.classList.toggle("badge-online", isOnline);
  els.connBadge.classList.toggle("badge-offline", !isOnline);
  updateConnectionControls();
}

function updateConnectionControls() {
  if (appState.connecting) {
    els.connectBtn.textContent = "Connecting...";
    els.connectBtn.disabled = true;
    els.reconnectBtn.disabled = true;
    els.reconnectBtn.classList.remove("hidden");
    els.nameInput.disabled = true;
    els.roomInput.disabled = true;
    els.customEndpointInput.disabled = true;
    els.addEndpointBtn.disabled = true;
    if (els.connectCard) els.connectCard.classList.add("card-locked");
    return;
  }

  const online = !!(appState.ws && appState.ws.readyState === WebSocket.OPEN);
  els.connectBtn.textContent = online ? "Connected (Click to Disconnect)" : "Connect + Join";
  els.reconnectBtn.classList.toggle("hidden", !online);
  els.reconnectBtn.disabled = !online;

  els.nameInput.disabled = online;
  els.roomInput.disabled = online;
  els.customEndpointInput.disabled = online;
  els.addEndpointBtn.disabled = online;
  if (els.connectCard) els.connectCard.classList.toggle("card-locked", online);
}

function setPhaseBadge(phase) {
  els.phaseBadge.textContent = String(phase || "WAITING").toUpperCase();
}

function setAdminPanelVisible(visible) {
  if (!els.adminPanel) return;
  els.adminPanel.classList.toggle("hidden", !visible);
}

async function ensureConnected() {
  if (appState.ws && appState.ws.readyState === WebSocket.OPEN) return true;
  await connectAndJoin(false);
  return !!(appState.ws && appState.ws.readyState === WebSocket.OPEN);
}

function sendMessage(type, payload) {
  if (!appState.ws || appState.ws.readyState !== WebSocket.OPEN) {
    pushNotification("warn", "No active connection.");
    return;
  }
  appState.ws.send(JSON.stringify({ type, payload }));
}

function parseMessage(raw) {
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

async function connectAndHandshake(endpoint, room, name, timeoutMs = 3200) {
  return new Promise((resolve, reject) => {
    let settled = false;
    const ws = new WebSocket(endpoint);
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      try {
        ws.close();
      } catch {
        // ignore
      }
      reject(new Error("join timeout"));
    }, timeoutMs);

    const fail = (reason) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      try {
        ws.close();
      } catch {
        // ignore
      }
      reject(new Error(reason));
    };

    ws.onerror = () => fail("socket error");
    ws.onclose = () => fail("closed before join ack");

    ws.onopen = () => {
      try {
        ws.send(JSON.stringify({ type: MSG.JOIN_ROOM, payload: { room_id: room, name } }));
      } catch {
        fail("send join failed");
      }
    };

    ws.onmessage = (ev) => {
      const data = parseMessage(ev.data);
      if (!data?.type) return;
      if (data.type === MSG.GAME_START) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        appState.playerId = data?.payload?.id || null;
        resolve(ws);
      }
    };
  });
}

async function connectAndJoin(forceReconnect = false) {
  if (!appState.consentAccepted) {
    pushNotification("warn", "Accept the educational 18+ consent first.");
    return;
  }

  if (appState.connecting) return;

  const name = (els.nameInput.value || "Player").trim() || "Player";
  const room = (els.roomInput.value || "Lobby1").trim() || "Lobby1";
  appState.connecting = true;
  updateConnectionControls();

  if (forceReconnect && appState.ws) {
    appState.manualDisconnect = true;
    appState.ws.close();
    appState.ws = null;
  }

  localStorage.setItem("domoneyracing_name", name);
  localStorage.setItem("domoneyracing_room", room);

  appState.endpointItems.forEach((e) => {
    e.status = "idle";
    e.reason = "";
  });
  renderEndpointOptions();

  const order = getAttemptOrder();
  setConnectionBadge(false);
  appState.playerId = null;
  pushNotification("info", `Trying ${order.length} endpoints...`);

  for (const item of order) {
    setEndpointStatus(item.url, "trying", "trying");
    try {
      const ws = await connectAndHandshake(item.url, room, name);
      appState.ws = ws;
      appState.connectedEndpoint = item.url;
      bindSocketEvents(ws);
      setEndpointStatus(item.url, "ok", "joined");
      setConnectionBadge(true);
      els.endpointMeta.textContent = `Endpoint: ${item.url}`;
      pushNotification("ok", `Joined via: ${item.url}`);
      appState.connecting = false;
      updateConnectionControls();
      return;
    } catch (err) {
      setEndpointStatus(item.url, "fail", err.message || "failed");
      pushNotification("warn", `Skipped ${item.url} (${err.message || "failed"})`);
    }
  }

  appState.connecting = false;
  updateConnectionControls();
  pushNotification("warn", "Could not connect to any endpoint.");
}

function bindSocketEvents(ws) {
  ws.onclose = () => {
    if (appState.ws !== ws) return;
    appState.ws = null;
    appState.connectedEndpoint = null;
    setConnectionBadge(false);
    els.endpointMeta.textContent = "Endpoint: disconnected";
    pushNotification("warn", "Connection closed. Click Reconnect.");
    appState.manualDisconnect = false;
  };

  ws.onerror = () => {
    pushNotification("warn", "WebSocket error occurred.");
  };

  ws.onmessage = (ev) => {
    const data = parseMessage(ev.data);
    if (!data?.type) return;
    const type = data.type;
    const payload = data.payload;

    if (type === MSG.GAME_START) {
      appState.playerId = payload?.id || null;
      pushNotification("ok", "Joined room successfully.");
      renderWallet();
      return;
    }

    if (type === MSG.ROOM_STATE) {
      appState.state = payload || null;
      setPhaseBadge(appState.state?.phase || "WAITING");
      els.raceMeta.textContent = `Race #${appState.state?.race_no || 0}`;
      renderRankings();
      renderWallet();
      renderBetMode();
      renderLeaderboard();
      renderFormulaBox();
      return;
    }

    if (type === MSG.LEADERBOARD_UPDATE) {
      appState.leaderboard = Array.isArray(payload) ? payload : [];
      renderLeaderboard();
      return;
    }

    if (type === MSG.CHAT_EVENT) {
      if (payload) {
        appState.chatEvents.push(payload);
        appState.chatEvents = appState.chatEvents.slice(-120);
        renderChat();
      }
      return;
    }

    if (type === MSG.SENTIMENT_UPDATE) {
      appState.sentiment = payload?.text || "No sentiment info";
      els.sentimentBox.textContent = appState.sentiment;
      return;
    }

    if (type === MSG.NOTIFICATION) {
      const kind = payload?.kind || "info";
      const text = payload?.text || "Notification";
      if (kind === "admin") {
        return;
      }
      pushNotification(kind, text);
      if (["flag", "alert", "bet", "coupon", "admin", "settlement", "race"].includes(kind)) {
        pushOverlay(kind, text, kind === "flag" ? 4600 : 3600);
      }
      return;
    }

    if (type === MSG.BET_RESULT) {
      const ok = !!payload?.ok;
      const text = payload?.message || "Bet update";
      pushNotification(ok ? "ok" : "warn", text);
      pushOverlay(ok ? "bet" : "warn", text, 3200);
      return;
    }

    if (type === MSG.ADMIN_RESULT) {
      return;
    }

    if (type === MSG.RACE_RESULT) {
      if (payload) {
        const sign = (payload.delta || 0) >= 0 ? "+" : "";
        pushNotification(
          "settlement",
          `${payload.player}: ${sign}${payload.delta} -> $${payload.money} (${payload.formula || ""})`,
        );
        pushOverlay(
          "settlement",
          `${payload.player} ${payload.win ? "WON" : "LOST"} ${sign}${payload.delta} | Winner ${String(payload.winner || "").toUpperCase()}`,
          5200,
        );
      }
      return;
    }

    if (type === MSG.ERROR) {
      pushNotification("warn", payload?.message || "Server error");
    }
  };
}

function getMyWallet() {
  if (!appState.state?.wallets) return null;
  if (!appState.playerId) return appState.state.wallets[0] || null;
  return appState.state.wallets.find((w) => w.player_id === appState.playerId) || null;
}

function renderWallet() {
  const wallet = getMyWallet();
  if (!wallet) {
    els.walletBox.textContent = "No wallet yet (connect and join).";
    return;
  }

  const bet = wallet.active_bet
    ? `Bet: ${wallet.active_bet.car_id.toUpperCase()} $${wallet.active_bet.amount}`
    : "Bet: none";
  const queue = wallet.queued_bet
    ? `Queued: ${wallet.queued_bet.car_id.toUpperCase()} $${wallet.queued_bet.amount} (Race #${wallet.queued_bet.race_no})`
    : "Queued: none";
  const badges = (wallet.badges || []).length ? wallet.badges.join(", ") : "none";
  const coupons = wallet.coupon_uses || {};

  els.walletBox.textContent = [
    `Name: ${wallet.name}`,
    `Money: $${wallet.money}`,
    `Wins: ${wallet.wins}`,
    `Streak: ${wallet.streak || 0}`,
    bet,
    queue,
    `Coupons: DO=${coupons.DOMONEY || 0}/3 | TD=${coupons.TROIDO || 0}/3 | KD=${coupons.KHONGDO || 0}/3 | DHKD=${coupons.DOHAYKHONGDO || 0}/1`,
    `Badges: ${badges}`,
  ].join("\n");
}

function renderBetMode() {
  if (!els.betModeBox) return;
  const phase = String(appState.state?.phase || "WAITING");
  if (phase === "COUNTDOWN") {
    els.betModeBox.textContent = "Mode: Current-race betting is OPEN. Place now to enter this race.";
    return;
  }
  if (phase === "RACING" || phase === "POST_RACE") {
    els.betModeBox.textContent = "Mode: Current race is locked. Place bet now to QUEUE for the next race.";
    return;
  }
  els.betModeBox.textContent = "Mode: Waiting for race state...";
}

function renderRankings() {
  const rankings = appState.state?.rankings || [];
  els.rankingList.innerHTML = "";
  if (!rankings.length) {
    const li = document.createElement("li");
    li.textContent = "Waiting for race data...";
    els.rankingList.appendChild(li);
    return;
  }

  rankings.slice(0, 5).forEach((r) => {
    const li = document.createElement("li");
    li.textContent = `${r.place}. ${r.name} | Lap ${r.lap} | Odds ${r.odds}`;
    els.rankingList.appendChild(li);
  });
}

function renderLeaderboard() {
  els.leaderboardList.innerHTML = "";

  const live = appState.state?.live_players || [];
  if (live.length) {
    const title = document.createElement("li");
    title.textContent = "Room players now:";
    title.style.color = "#70f4b5";
    els.leaderboardList.appendChild(title);
    live.forEach((p, i) => {
      const li = document.createElement("li");
      li.textContent = `${i + 1}. ${p.name} | $${p.money} | Wins ${p.wins} | Streak ${p.streak}`;
      els.leaderboardList.appendChild(li);
    });
  }

  if (appState.leaderboard.length) {
    const hist = document.createElement("li");
    hist.textContent = "All-time:";
    hist.style.color = "#ffd86b";
    els.leaderboardList.appendChild(hist);
    appState.leaderboard.slice(0, 10).forEach((row, i) => {
      const li = document.createElement("li");
      li.textContent = `${i + 1}. ${row.name} | Profit $${row.score} | Wins ${row.wins}`;
      els.leaderboardList.appendChild(li);
    });
  }

  if (!live.length && !appState.leaderboard.length) {
    const li = document.createElement("li");
    li.textContent = "No leaderboard entries yet.";
    els.leaderboardList.appendChild(li);
  }
}

function renderFormulaBox() {
  const mult = Number(appState.state?.payout_multiplier || 1).toFixed(2);
  const selectedOdds = Number(
    (appState.state?.rankings || []).find((r) => r.car_id === appState.selectedCar)?.odds || 0,
  );
  const selectedPayout = Math.round(appState.selectedAmount * selectedOdds * Number(mult || 1));
  const selectedDelta = selectedPayout - appState.selectedAmount;
  if (els.formulaBox) {
    els.formulaBox.innerHTML = [
      `Win payout formula: payout = bet_amount x live_odds x ${mult}.`,
      "Net win = payout - bet_amount.",
      "Loss = -bet_amount.",
      `Example now: ${appState.selectedCar.toUpperCase()} with $${appState.selectedAmount} at odds ${selectedOdds.toFixed(2)} -> payout $${selectedPayout}, net ${selectedDelta >= 0 ? "+" : ""}${selectedDelta}.`,
      "Coupons apply directly to wallet balance.",
    ].join("<br>");
  }
}

function renderChat() {
  els.chatLog.innerHTML = "";
  appState.chatEvents.slice(-120).forEach((item) => {
    const div = document.createElement("div");
    div.className = item.kind === "ai" ? "ai" : "player";
    div.textContent = `${item.sender}: ${item.message}`;
    els.chatLog.appendChild(div);
  });
  els.chatLog.scrollTop = els.chatLog.scrollHeight;
}

function renderNotifications() {
  els.notificationList.innerHTML = "";
  appState.notifications.slice(-28).forEach((n) => {
    const li = document.createElement("li");
    li.textContent = `[${n.ts}] ${n.text}`;
    if (["warn", "flag", "alert"].includes(n.kind)) li.style.color = "#ff9e9e";
    if (["ok", "admin"].includes(n.kind)) li.style.color = "#8df2bf";
    if (n.kind === "settlement") li.style.color = "#ffd86b";
    els.notificationList.appendChild(li);
  });
}

function makeChip(label, active, onClick) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = `chip${active ? " active" : ""}`;
  btn.textContent = label;
  btn.addEventListener("click", onClick);
  return btn;
}

function renderBetControls() {
  els.carButtons.innerHTML = "";
  for (let i = 1; i <= 5; i += 1) {
    const carId = `car${i}`;
    els.carButtons.appendChild(
      makeChip(carId.toUpperCase(), appState.selectedCar === carId, () => {
        appState.selectedCar = carId;
        renderBetControls();
      }),
    );
  }

  els.amountButtons.innerHTML = "";
  [25, 50, 100, 250, 500].forEach((amt) => {
    els.amountButtons.appendChild(
      makeChip(`$${amt}`, appState.selectedAmount === amt, () => {
        appState.selectedAmount = amt;
        renderBetControls();
      }),
    );
  });
}

function renderAdminRigButtons() {
  if (!els.adminRigButtons) return;
  els.adminRigButtons.innerHTML = "";
  for (let i = 1; i <= 5; i += 1) {
    const carId = `car${i}`;
    els.adminRigButtons.appendChild(
      makeChip(carId.toUpperCase(), appState.selectedRigCar === carId, () => {
        appState.selectedRigCar = carId;
        renderAdminRigButtons();
      }),
    );
  }
}

function sendAdminAction(action, payload = {}) {
  sendMessage(MSG.ADMIN_ACTION, {
    action,
    token: (els.adminTokenInput?.value || "").trim(),
    ...payload,
  });
}

function drawTrack() {
  ctx.clearRect(0, 0, TRACK.width, TRACK.height);
  const grd = ctx.createLinearGradient(0, 0, TRACK.width, TRACK.height);
  grd.addColorStop(0, "#141f30");
  grd.addColorStop(1, "#18283b");
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, TRACK.width, TRACK.height);

  ctx.strokeStyle = "#22d7ff";
  ctx.lineWidth = 3;
  ctx.strokeRect(TRACK.outerX, TRACK.outerY, TRACK.outerW, TRACK.outerH);
  ctx.strokeStyle = "#ff8e58";
  ctx.strokeRect(TRACK.innerX, TRACK.innerY, TRACK.innerW, TRACK.innerH);

  ctx.lineWidth = 1;
  for (let lane = 0; lane < TRACK.laneCount; lane += 1) {
    const inset = 20 + lane * 16;
    ctx.strokeStyle = "rgba(169, 193, 212, 0.28)";
    ctx.strokeRect(TRACK.outerX + inset, TRACK.outerY + inset, TRACK.outerW - inset * 2, TRACK.outerH - inset * 2);
  }
}

function drawCars() {
  const cars = appState.state?.cars || [];
  const wallet = getMyWallet();
  const activeBetCar = wallet?.active_bet?.car_id || null;
  const queuedBetCar = wallet?.queued_bet?.car_id || null;

  cars.forEach((car) => {
    const color = Array.isArray(car.color) ? `rgb(${car.color[0]},${car.color[1]},${car.color[2]})` : "#ffffff";
    const x = Number(car.x || 0);
    const y = Number(car.y || 0);

    ctx.fillStyle = color;
    ctx.fillRect(x, y, TRACK.carW, TRACK.carH);
    ctx.fillStyle = "rgba(10, 17, 25, 0.85)";
    ctx.fillRect(x + 4, y + 4, 8, 6);
    ctx.fillStyle = "#f7fbff";
    ctx.font = "11px JetBrains Mono";
    ctx.fillText(car.name || car.id || "CAR", x, y - 5);

    if (car.id === appState.selectedCar) {
      ctx.strokeStyle = "#6be8ff";
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 2, y - 2, TRACK.carW + 4, TRACK.carH + 4);
    }

    if (car.id === activeBetCar) {
      ctx.strokeStyle = "#ffd86b";
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 5, y - 5, TRACK.carW + 10, TRACK.carH + 10);
    } else if (car.id === queuedBetCar) {
      ctx.setLineDash([4, 3]);
      ctx.strokeStyle = "#9dc9ff";
      ctx.lineWidth = 2;
      ctx.strokeRect(x - 5, y - 5, TRACK.carW + 10, TRACK.carH + 10);
      ctx.setLineDash([]);
    }
  });
}

function drawEducationWarning() {
  const w = appState.warning;
  const boxW = 430;
  const boxH = 32;
  w.x += w.vx;
  w.y += w.vy;
  if (w.x <= 0 || w.x + boxW >= TRACK.width) w.vx *= -1;
  if (w.y <= 0 || w.y + boxH >= TRACK.height) w.vy *= -1;
  w.x = Math.max(0, Math.min(TRACK.width - boxW, w.x));
  w.y = Math.max(0, Math.min(TRACK.height - boxH, w.y));

  ctx.fillStyle = "rgba(255, 174, 87, 0.33)";
  ctx.fillRect(w.x, w.y, boxW, boxH);
  ctx.fillStyle = "#ffffff";
  ctx.font = "12px JetBrains Mono";
  ctx.fillText("EDUCATION PURPOSES ONLY: simulated race + wager mechanics", w.x + 10, w.y + 20);
}

function drawPhaseOverlay() {
  const phase = appState.state?.phase || "WAITING";
  const raceNo = appState.state?.race_no || 0;
  const phaseT = Number(appState.state?.phase_time || 0);

  ctx.fillStyle = "rgba(0, 0, 0, 0.25)";
  ctx.fillRect(12, 10, 260, 44);
  ctx.fillStyle = "#f0f7ff";
  ctx.font = "14px JetBrains Mono";
  ctx.fillText(`RACE #${raceNo} | ${phase}`, 20, 28);
  ctx.fillText(`PHASE T: ${phaseT.toFixed(1)}s`, 20, 46);

  if (phase === "COUNTDOWN") {
    const remain = Math.max(0, Math.ceil(COUNTDOWN_SECONDS - phaseT));
    if (remain >= 1 && remain <= 3) {
      ctx.fillStyle = "rgba(0,0,0,0.34)";
      ctx.fillRect(0, 0, TRACK.width, TRACK.height);
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 84px JetBrains Mono";
      ctx.textAlign = "center";
      ctx.fillText(String(remain), TRACK.width / 2, TRACK.height / 2);
      ctx.textAlign = "start";
    }
  }

  if (phase === "POST_RACE") {
    const winner = appState.state?.rankings?.[0]?.name || "UNKNOWN";
    ctx.fillStyle = "rgba(0,0,0,0.32)";
    ctx.fillRect(0, 0, TRACK.width, TRACK.height);
    ctx.fillStyle = "#ffd86b";
    ctx.font = "bold 44px JetBrains Mono";
    ctx.textAlign = "center";
    ctx.fillText(`WINNER: ${winner}`, TRACK.width / 2, TRACK.height / 2);
    ctx.textAlign = "start";
  }
}

function drawLiveEventOverlays() {
  cleanOverlayEvents();
  const now = performance.now();
  const events = appState.overlayEvents.slice(-3);
  events.forEach((ev, i) => {
    const age = now - ev.started;
    const left = Math.max(0, ev.duration - age);
    const t = left / ev.duration;
    const y = TRACK.height - 24 - i * 40;
    const alpha = 0.2 + t * 0.75;

    ctx.fillStyle = `rgba(0, 0, 0, ${0.28 * alpha})`;
    ctx.fillRect(20, y - 20, TRACK.width - 40, 28);

    let color = "#e8f3ff";
    if (["warn", "flag", "alert"].includes(ev.kind)) color = "#ffb2b2";
    if (["ok", "admin", "bet"].includes(ev.kind)) color = "#9bf2c7";
    if (["settlement", "race"].includes(ev.kind)) color = "#ffe08a";

    ctx.fillStyle = color;
    ctx.font = "13px JetBrains Mono";
    ctx.fillText(ev.text, 28, y - 2);
  });
}

function animate() {
  drawTrack();
  drawCars();
  drawPhaseOverlay();
  drawLiveEventOverlays();
  drawEducationWarning();
  requestAnimationFrame(animate);
}

function setupUI() {
  const storedName = localStorage.getItem("domoneyracing_name");
  const storedRoom = localStorage.getItem("domoneyracing_room");
  if (storedName) els.nameInput.value = storedName;
  if (storedRoom) els.roomInput.value = storedRoom;

  loadEndpointList();
  renderEndpointOptions();
  renderBetControls();
  renderAdminRigButtons();
  setAdminPanelVisible(false);
  renderWallet();
  renderRankings();
  renderLeaderboard();
  renderChat();
  renderNotifications();
  renderBetMode();
  renderFormulaBox();

  els.addEndpointBtn.addEventListener("click", () => {
    const url = normalizeEndpoint(els.customEndpointInput.value);
    if (!url) return;
    const created = addEndpointOption(url, true);
    if (!created) {
      pushNotification("info", "Endpoint already exists; moved to first.");
      return;
    }
    els.customEndpointInput.value = "";
    pushNotification("ok", "Endpoint added and selected first.");
  });

  els.addGgEndpointBtn.addEventListener("click", () => {
    const created = addEndpointOption(GOOGLE_FALLBACK_ENDPOINT, true);
    if (created) {
      pushNotification("ok", "GG endpoint added and selected first.");
    } else {
      pushNotification("info", "GG endpoint already exists; moved to first.");
    }
  });

  els.resetEndpointsBtn.addEventListener("click", () => {
    localStorage.removeItem(ENDPOINT_STORAGE_KEY);
    localStorage.removeItem("domoneyracing_endpoints_v2");
    loadEndpointList();
    renderEndpointOptions();
    pushNotification("ok", "Endpoint list reset. Default endpoints restored.");
  });

  els.connectBtn.addEventListener("click", () => {
    const online = !!(appState.ws && appState.ws.readyState === WebSocket.OPEN);
    if (online) {
      appState.manualDisconnect = true;
      appState.ws.close();
      pushNotification("info", "Disconnected by user.");
      return;
    }
    connectAndJoin(false);
  });

  els.reconnectBtn.addEventListener("click", () => connectAndJoin(true));

  els.placeBetBtn.addEventListener("click", () => {
    sendMessage(MSG.PLACE_BET, { car_id: appState.selectedCar, amount: appState.selectedAmount });
  });

  els.queueBetBtn.addEventListener("click", () => {
    sendMessage(MSG.PLACE_BET, { car_id: appState.selectedCar, amount: appState.selectedAmount, queue_next: true });
    pushNotification("info", `Queued request: ${appState.selectedCar.toUpperCase()} $${appState.selectedAmount} for next race.`);
  });

  els.cancelBetBtn.addEventListener("click", () => {
    sendMessage(MSG.CANCEL_BET, {});
  });

  document.querySelectorAll(".btn-coupon").forEach((btn) => {
    btn.addEventListener("click", () => {
      const code = btn.getAttribute("data-code") || "";
      sendMessage(MSG.REDEEM_COUPON, { code });
    });
  });

  const sendChat = () => {
    const text = (els.chatInput.value || "").trim();
    if (!text) return;

    sendMessage(MSG.CHAT_SEND, { message: text });
    els.chatInput.value = "";
  };

  els.chatSendBtn.addEventListener("click", sendChat);
  els.askAiBtn.addEventListener("click", async () => {
    const ok = await ensureConnected();
    if (!ok) {
      pushNotification("warn", "Ask AI requires a live connection.");
      return;
    }
    sendMessage(MSG.CHAT_SEND, { message: "/ai help exacta longshot odds track" });
    pushOverlay("ai", "Asked AI strategist for a betting read.", 2800);
  });

  els.chatInput.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") {
      ev.preventDefault();
      sendChat();
    }
  });

  window.addEventListener("keydown", (ev) => {
    if (ev.ctrlKey && ev.shiftKey && (ev.key === "A" || ev.key === "a")) {
      ev.preventDefault();
      setAdminPanelVisible(true);
      return;
    }
    if (ev.ctrlKey && ev.shiftKey && (ev.key === "B" || ev.key === "b")) {
      ev.preventDefault();
      setAdminPanelVisible(false);
    }
  });

  els.setMultiplierBtn?.addEventListener("click", () => {
    const value = Number(els.adminMultiplierInput.value || 1);
    sendAdminAction("set_multiplier", { value });
  });

  els.clearRigBtn?.addEventListener("click", () => {
    sendAdminAction("clear_rig", {});
  });

  els.setRigBtn?.addEventListener("click", () => {
    sendAdminAction("set_rig_winner", { car_id: appState.selectedRigCar });
  });

  els.adjustMoneyBtn?.addEventListener("click", () => {
    const player_name = (els.adminPlayerInput.value || "").trim();
    const delta = Number(els.adminDeltaInput.value || 0);
    sendAdminAction("adjust_player_money", { player_name, delta });
  });

  // Ops panel remains hidden unless explicitly toggled by keyboard shortcut.
}

setupUI();
const consentAlreadyAccepted = initConsentGate();
setConnectionBadge(false);
setPhaseBadge("WAITING");
els.endpointMeta.textContent = "Endpoint: not connected";
updateConnectionControls();
if (document.getElementById("buildMeta")) {
  document.getElementById("buildMeta").textContent = `Build: ${BUILD_VERSION}`;
}
pushNotification("info", `Client build ${BUILD_VERSION}`);
animate();
if (consentAlreadyAccepted) {
  connectAndJoin(false);
}
