/**
 * Chat panel — WebSocket connection, message rendering, input handling.
 */

const Chat = (() => {
  let ws = null;
  let sessionId = null;
  let thinkingEl = null;

  function init(sid) {
    sessionId = sid;
    connect();

    const input = document.getElementById("msg-input");
    const sendBtn = document.getElementById("send-btn");

    sendBtn.addEventListener("click", sendMessage);
    input.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    input.addEventListener("input", () => {
      input.style.height = "auto";
      input.style.height = Math.min(input.scrollHeight, 120) + "px";
    });
  }

  function connect() {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/api/chat/ws/${sessionId}`;
    ws = new WebSocket(url);

    ws.onopen = () => {
      setConnectionStatus(true);
    };

    ws.onclose = () => {
      setConnectionStatus(false);
      // Reconnect after 3 seconds
      setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      setConnectionStatus(false);
    };

    ws.onmessage = e => {
      const data = JSON.parse(e.data);
      handleServerMessage(data);
    };
  }

  function handleServerMessage(data) {
    switch (data.type) {
      case "svg_update":
        Preview.update(data.svg, data.changed_ids || []);
        break;

      case "done":
        removeThinking();
        addMessage("assistant", data.reply);
        setInputEnabled(true);
        break;

      case "chunk":
        // Streaming text chunk (future enhancement)
        appendThinkingText(data.text);
        break;

      case "error":
        removeThinking();
        addError(data.message);
        setInputEnabled(true);
        break;
    }
  }

  function sendMessage() {
    const input = document.getElementById("msg-input");
    const text = input.value.trim();
    if (!text) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      addError("Not connected — retrying...");
      return;
    }

    const attachments = Upload.consumeAttachments();

    addMessage("user", text);
    if (attachments.length > 0) {
      addSystemMessage(`Sending ${attachments.length} attachment(s)...`);
    }

    input.value = "";
    input.style.height = "auto";
    setInputEnabled(false);
    showThinking();

    ws.send(JSON.stringify({
      type: "message",
      text,
      attachments: attachments.map(a => ({ type: a.type, data: a.data, name: a.name })),
    }));
  }

  function addMessage(role, text) {
    const messages = document.getElementById("messages");
    const div = document.createElement("div");
    div.className = `message ${role}`;
    // Simple markdown-like rendering
    div.innerHTML = formatText(text);
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function addSystemMessage(text) {
    const messages = document.getElementById("messages");
    const div = document.createElement("div");
    div.className = "message system";
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function addError(text) {
    const messages = document.getElementById("messages");
    const div = document.createElement("div");
    div.className = "message error";
    div.textContent = "Error: " + text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
  }

  function showThinking() {
    const messages = document.getElementById("messages");
    thinkingEl = document.createElement("div");
    thinkingEl.className = "message thinking";
    thinkingEl.textContent = "Thinking...";
    messages.appendChild(thinkingEl);
    messages.scrollTop = messages.scrollHeight;
  }

  function appendThinkingText(text) {
    if (thinkingEl) thinkingEl.textContent += text;
  }

  function removeThinking() {
    if (thinkingEl) {
      thinkingEl.remove();
      thinkingEl = null;
    }
  }

  function setInputEnabled(enabled) {
    document.getElementById("msg-input").disabled = !enabled;
    document.getElementById("send-btn").disabled = !enabled;
  }

  function setConnectionStatus(connected) {
    const badge = document.getElementById("status-badge");
    if (connected) {
      badge.textContent = "● Connected";
      badge.className = "connected";
    } else {
      badge.textContent = "○ Disconnected";
      badge.className = "";
    }
  }

  function formatText(text) {
    // Basic markdown: **bold**, `code`, newlines
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\n/g, "<br>");
  }

  return { init, addMessage, addSystemMessage, addError };
})();
