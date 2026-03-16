/**
 * App initialization — session management, module wiring.
 */

const App = (() => {
  let sessionId = null;

  function getSessionId() {
    return sessionId;
  }

  function generateId() {
    return "sess_" + Math.random().toString(36).slice(2, 11) +
           Date.now().toString(36);
  }

  function init() {
    // Restore or generate session ID
    sessionId = sessionStorage.getItem("seamly_session_id");
    if (!sessionId) {
      sessionId = generateId();
      sessionStorage.setItem("seamly_session_id", sessionId);
    }

    // Initialize modules
    Chat.init(sessionId);
    Upload.init(sessionId);
    Preview.init();

    // Welcome message
    Chat.addSystemMessage("Welcome! Upload a .val pattern file to get started, then describe changes in the chat.");

    // Register service worker (optional, for offline caching)
    // if ('serviceWorker' in navigator) navigator.serviceWorker.register('/sw.js');
  }

  return { init, getSessionId };
})();

document.addEventListener("DOMContentLoaded", App.init);
