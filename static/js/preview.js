/**
 * SVG preview panel — display, zoom, pan, highlight.
 */

const Preview = (() => {
  let scale = 1.0;
  const MIN_SCALE = 0.3;
  const MAX_SCALE = 4.0;
  const SCALE_STEP = 0.15;

  function init() {
    document.getElementById("zoom-in").addEventListener("click", () => zoom(SCALE_STEP));
    document.getElementById("zoom-out").addEventListener("click", () => zoom(-SCALE_STEP));
    document.getElementById("zoom-reset").addEventListener("click", resetZoom);
    document.getElementById("download-btn").addEventListener("click", downloadPattern);
  }

  function update(svgString, highlightIds = []) {
    const container = document.getElementById("svg-container");
    const empty = document.getElementById("empty-state");

    if (!svgString) return;

    if (empty) empty.style.display = "none";
    container.style.display = "block";
    container.innerHTML = svgString;

    // Highlight changed points
    if (highlightIds && highlightIds.length > 0) {
      highlightIds.forEach(id => {
        const el = container.querySelector(`[data-id="${id}"]`);
        if (el) {
          el.setAttribute("fill", "#e63946");
          el.setAttribute("r", "5");
        }
      });
      // Clear highlights after 3 seconds
      setTimeout(() => clearHighlights(container), 3000);
    }

    applyScale();
  }

  function clearHighlights(container) {
    container.querySelectorAll("circle[data-id]").forEach(el => {
      el.setAttribute("fill", "#1a6496");
      el.setAttribute("r", "3");
    });
  }

  function zoom(delta) {
    scale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale + delta));
    applyScale();
  }

  function resetZoom() {
    scale = 1.0;
    applyScale();
  }

  function applyScale() {
    const container = document.getElementById("svg-container");
    container.style.transform = `scale(${scale})`;
    document.getElementById("zoom-level").textContent = Math.round(scale * 100) + "%";
  }

  async function downloadPattern() {
    const sessionId = App.getSessionId();
    try {
      const res = await fetch(`/api/patterns/download/${sessionId}`);
      if (!res.ok) {
        Chat.addError("Download failed — upload a pattern first.");
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "pattern_modified.val";
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      Chat.addError("Download error: " + e.message);
    }
  }

  return { init, update };
})();
