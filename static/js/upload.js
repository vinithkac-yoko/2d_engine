/**
 * File upload handling — .val/.vit pattern files and image/PDF attachments.
 */

const Upload = (() => {
  let pendingAttachments = [];   // [{name, type, data (base64)}]
  let sessionId = null;

  function init(sid) {
    sessionId = sid;
    const label = document.getElementById("upload-label");
    const input = document.getElementById("file-input");

    // Click upload
    input.addEventListener("change", () => handleFiles(input.files));

    // Drag and drop
    label.addEventListener("dragover", e => {
      e.preventDefault();
      label.classList.add("drag-over");
    });
    label.addEventListener("dragleave", () => label.classList.remove("drag-over"));
    label.addEventListener("drop", e => {
      e.preventDefault();
      label.classList.remove("drag-over");
      handleFiles(e.dataTransfer.files);
    });
  }

  async function handleFiles(files) {
    const valFile = Array.from(files).find(f => f.name.endsWith(".val"));
    const vitFile = Array.from(files).find(f => f.name.endsWith(".vit"));
    const others = Array.from(files).filter(f =>
      !f.name.endsWith(".val") && !f.name.endsWith(".vit")
    );

    if (valFile) {
      await uploadPattern(valFile, vitFile);
    }

    for (const f of others) {
      await addAttachment(f);
    }
  }

  async function uploadPattern(valFile, vitFile) {
    setStatus("Uploading pattern...");
    const form = new FormData();
    form.append("session_id", sessionId);
    form.append("val_file", valFile);
    if (vitFile) form.append("vit_file", vitFile);

    try {
      const res = await fetch("/api/patterns/upload", { method: "POST", body: form });
      if (!res.ok) {
        const err = await res.json();
        setStatus("Upload failed: " + (err.detail || res.statusText));
        return;
      }
      const data = await res.json();
      setStatus(`Loaded: ${data.draw_names.join(", ")} | ${data.piece_names.length} piece(s) | ${data.measurement_count} measurements`);
      Preview.update(data.svg);
      Chat.addSystemMessage(`Pattern loaded: ${valFile.name}`);
    } catch (e) {
      setStatus("Upload error: " + e.message);
    }
  }

  async function addAttachment(file) {
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      Chat.addError("File too large (max 10MB): " + file.name);
      return;
    }
    const data = await readAsBase64(file);
    pendingAttachments.push({ name: file.name, type: file.type, data });
    renderAttachmentChips();
  }

  function readAsBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => {
        // Strip the data URL prefix
        const result = reader.result.split(",")[1];
        resolve(result);
      };
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  function renderAttachmentChips() {
    const area = document.getElementById("attachment-preview");
    if (pendingAttachments.length === 0) {
      area.style.display = "none";
      return;
    }
    area.style.display = "flex";
    area.innerHTML = pendingAttachments.map((a, i) =>
      `<div class="att-chip">
        ${a.name}
        <span class="remove" data-idx="${i}">×</span>
      </div>`
    ).join("");
    area.querySelectorAll(".remove").forEach(btn => {
      btn.addEventListener("click", () => {
        pendingAttachments.splice(parseInt(btn.dataset.idx), 1);
        renderAttachmentChips();
      });
    });
  }

  function consumeAttachments() {
    const result = [...pendingAttachments];
    pendingAttachments = [];
    renderAttachmentChips();
    return result;
  }

  function setStatus(msg) {
    const el = document.getElementById("upload-status");
    if (el) el.textContent = msg;
  }

  return { init, consumeAttachments };
})();
