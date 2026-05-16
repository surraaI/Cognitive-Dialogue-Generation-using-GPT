const STORAGE_USER = "cognitive_chat_user_id";
const STORAGE_CONV = "cognitive_chat_conversation_id";

function randomUuid() {
  if (crypto.randomUUID) return crypto.randomUUID();
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

function getUserId() {
  let id = localStorage.getItem(STORAGE_USER);
  if (!id) {
    id = randomUuid();
    localStorage.setItem(STORAGE_USER, id);
  }
  return id;
}

function getConversationId() {
  return localStorage.getItem(STORAGE_CONV);
}

function setConversationId(id) {
  if (id) localStorage.setItem(STORAGE_CONV, id);
  else localStorage.removeItem(STORAGE_CONV);
}

const messagesEl = document.getElementById("messages");
const form = document.getElementById("form");
const input = document.getElementById("input");
const modeSelect = document.getElementById("mode");
const sendBtn = document.getElementById("send");
const modeInfoEl = document.getElementById("modeInfo");

const MODE_DESCRIPTIONS = {
  socratic: "Guides you toward insights through questions",
  explanatory: "Provides detailed explanations and examples",
  concise: "Brief, to-the-point answers",
};

function appendBubble(role, text, meta = "") {
  const wrap = document.createElement("div");
  wrap.className = `bubble ${role}`;
  const metaEl = document.createElement("div");
  metaEl.className = "meta";
  metaEl.textContent = meta || (role === "user" ? "You" : "Assistant");
  const p = document.createElement("p");
  p.className = "text";
  p.textContent = text;
  wrap.appendChild(metaEl);
  wrap.appendChild(p);
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function systemLine(text) {
  const el = document.createElement("div");
  el.className = "system";
  el.textContent = text;
  messagesEl.appendChild(el);
}

async function sendMessage(text) {
  const userId = getUserId();
  const conversationId = getConversationId();
  const mode = modeSelect.value;

  const body = {
    user_id: userId,
    message: text,
    mode,
  };
  if (conversationId) body.conversation_id = conversationId;

  const res = await fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = await res.text();
    throw new Error(err || `HTTP ${res.status}`);
  }

  const data = await res.json();
  if (data.conversation_id) setConversationId(data.conversation_id);

  const attn = data.attention;
  const attnHint =
    attn && (attn.entities?.length || attn.keyphrases?.length)
      ? ` · attention: ${[
          ...(attn.entities || []).slice(0, 2).map((e) => e.text),
          ...(attn.keyphrases || []).slice(0, 1).map((k) => k.text),
        ]
          .filter(Boolean)
          .join(", ")}`
      : "";

  appendBubble(
    "assistant",
    data.assistant_message,
    `Assistant · ${data.mode}${attnHint ? attnHint : ""}`
  );
  return data;
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  appendBubble("user", text, "You");
  sendBtn.disabled = true;
  try {
    await sendMessage(text);
  } catch (err) {
    systemLine(String(err.message || err));
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
});

// Update mode description when mode changes
modeSelect.addEventListener("change", (e) => {
  const mode = e.target.value;
  modeInfoEl.textContent = MODE_DESCRIPTIONS[mode] || "";
});

// Initialize mode description
modeInfoEl.textContent = MODE_DESCRIPTIONS[modeSelect.value] || "";

systemLine(`User id: ${getUserId().slice(0, 8)}… — Open from the same host as the API (e.g. /ui/).`);
input.focus();
