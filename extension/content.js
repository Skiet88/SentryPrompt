// Content script (classic script, not a module — Manifest V3 does not allow
// "type": "module" content scripts). It NEVER fetches anything itself and
// NEVER sees the session token: it only sends the typed text to
// background.js over chrome.runtime.sendMessage and gets back a verdict.
//
// Site-agnostic by design: nothing here knows any one site's markup. All
// listeners sit on window in the capture phase, so they see Enter, clicks
// and form submits before the page's own handlers, and the prompt box is
// simply "whichever textarea or contenteditable the student is typing in".
// Supporting another AI site is therefore only a manifest.json change
// (its URL in content_scripts.matches and host_permissions).
(() => {
  const DEBOUNCE_MS = 800;
  const EDITABLE = "textarea, [contenteditable='true'], [contenteditable=''], [contenteditable='plaintext-only']";
  const BUTTON = "button, [role='button'], input[type='submit']";
  const SEND_HINT = /send|submit/i;

  function eventElement(event) {
    const node = event.composedPath ? event.composedPath()[0] : event.target;
    return node instanceof Element ? node : (node?.parentElement ?? null);
  }

  function editableFrom(event) {
    return eventElement(event)?.closest?.(EDITABLE) ?? null;
  }

  function isSendButton(btn) {
    if (btn.type === "submit" && btn.form) return true;
    return ["aria-label", "data-testid", "title", "id"].some((a) => SEND_HINT.test(btn.getAttribute(a) ?? ""));
  }

  // The nearest send-like button around the prompt box, if the site has one.
  function findSendButton(el) {
    for (let node = el.parentElement, depth = 0; node && depth < 10; node = node.parentElement, depth++) {
      const btn = [...node.querySelectorAll(BUTTON)].find((b) => isSendButton(b) && !b.disabled);
      if (btn) return btn;
    }
    return null;
  }

  function getText(el) {
    if (el.tagName === "TEXTAREA") return el.value;
    return el.innerText ?? el.textContent ?? "";
  }

  // insertText goes through the browser's own editing pipeline, so rich
  // editors (ProseMirror, Quill, Lexical) and React-controlled textareas
  // all see it as real typing and keep their internal state in sync.
  function setText(el, text) {
    el.focus();
    if (el.tagName === "TEXTAREA") {
      el.select();
    } else {
      const range = document.createRange();
      range.selectNodeContents(el);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
    }
    let ok = false;
    try {
      ok = document.execCommand("insertText", false, text);
    } catch {
      ok = false;
    }
    if (ok && getText(el).trim() === text.trim()) return;
    if (el.tagName === "TEXTAREA") {
      Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set.call(el, text);
    } else {
      el.textContent = text;
    }
    el.dispatchEvent(new InputEvent("input", { bubbles: true, data: text, inputType: "insertReplacementText" }));
  }

  // ---- banner (Shadow DOM: isolates our CSS from the host page, and the
  // host page's CSS from us) --------------------------------------------
  const host = document.createElement("div");
  host.setAttribute("data-sentryprompt", "");
  host.style.all = "initial";
  const shadow = host.attachShadow({ mode: "open" });
  shadow.innerHTML = `
    <style>
      .banner { position: fixed; z-index: 2147483647; max-width: 420px; font-family: system-ui, sans-serif;
        background: #fff; border: 1px solid #d8d4cc; border-radius: 10px; box-shadow: 0 8px 24px rgba(0,0,0,.18);
        padding: 12px 14px; color: #0b0b0b; display: none; }
      .banner.show { display: block; }
      .title { font-weight: 600; font-size: 13px; margin-bottom: 4px; display: flex; align-items: center; gap: 6px; }
      .dot { width: 8px; height: 8px; border-radius: 50%; background: #eb6834; flex: none; }
      ul { margin: 6px 0 10px; padding-left: 16px; font-size: 12px; }
      li { margin-bottom: 4px; }
      .cat { font-weight: 600; }
      .row { display: flex; gap: 6px; flex-wrap: wrap; }
      button { font-size: 12px; padding: 5px 10px; border-radius: 6px; border: 1px solid #ccc; background: #f3f1ec;
        cursor: pointer; }
      button.primary { background: #1baf7a; color: #fff; border-color: #1baf7a; }
      .notice { font-size: 11px; color: #52514e; margin-top: 8px; }
    </style>
    <div class="banner" part="banner">
      <div class="title"><span class="dot"></span><span class="headline"></span></div>
      <ul class="flags"></ul>
      <div class="notice"></div>
      <div class="row">
        <button class="hide primary" style="display:none">Hide details and send</button>
        <button class="edit">Edit my prompt</button>
        <button class="sendAnyway">Send anyway</button>
      </div>
    </div>
  `;
  document.documentElement.appendChild(host);
  const banner = shadow.querySelector(".banner");
  const headline = shadow.querySelector(".headline");
  const flagsEl = shadow.querySelector(".flags");
  const noticeEl = shadow.querySelector(".notice");
  const hideBtn = shadow.querySelector(".hide");
  const sendAnywayBtn = shadow.querySelector(".sendAnyway");
  const editBtn = shadow.querySelector(".edit");

  function showBanner(target) {
    banner.classList.add("show");
    const r = target.getBoundingClientRect();
    banner.style.left = `${Math.max(8, r.left)}px`;
    banner.style.top = `${Math.max(8, r.top - banner.offsetHeight - 10)}px`;
  }
  function hideBanner() {
    banner.classList.remove("show");
  }

  // ---- state -----------------------------------------------------------
  // "clear"    -> the screened text had nothing to warn about
  // "pending"  -> flags exist (or the check failed: fail closed, NFR-015);
  //               sending is blocked until the student chooses
  // "resolved" -> the student chose an action for the screened text
  let state = "clear";
  let lastScreenedText = "";
  let currentFlags = [];
  let debounceTimer = null;
  let activeInput = null;
  let inflight = null; // { text, promise } of the check now running
  let bypass = false; // true only while we replay a submit we held back

  // Same plain-language labels as frontend/src/chat/categories.ts, kept in
  // sync manually (the extension has no build step to share code with the
  // frontend); the explanation itself always comes from the server.
  const CATEGORY_LABELS = {
    SA_ID: "ID number",
    BANK_CARD: "Card number",
    BANK_ACCOUNT: "Account number",
    PHONE: "Phone number",
    EMAIL: "Email address",
    ADDRESS: "Street address",
    STUDENT_NUMBER: "Student number",
    MEDICAL: "Health information",
    INSTITUTIONAL: "Confidential university information",
  };
  function categoryLabel(category) {
    const known = CATEGORY_LABELS[category.toUpperCase()];
    if (known) return known;
    const words = category.toLowerCase().replace(/_/g, " ").trim();
    return words ? words.charAt(0).toUpperCase() + words.slice(1) : "Sensitive information";
  }

  function showUnchecked(el, kind) {
    state = "pending";
    currentFlags = [];
    headline.textContent = "We couldn't fully check this prompt";
    noticeEl.textContent =
      kind === "rate_limited"
        ? "Too many checks in the last minute. Wait a moment, or send anyway."
        : "The screening service did not answer in time.";
    flagsEl.innerHTML = "";
    hideBtn.style.display = "none";
    showBanner(el);
  }

  // Resolves to "clear", "pending", or "stale" (the text changed while the
  // check was running, so this answer says nothing about what is there now).
  async function runScreen(el, text) {
    let result;
    try {
      result = await chrome.runtime.sendMessage({ type: "SCREEN_PROMPT", text });
    } catch {
      result = { kind: "unavailable" };
    }
    if (getText(el).trim() !== text) return "stale";
    lastScreenedText = text;

    if (result?.kind === "not_logged_in") {
      // Logged-out visitors are not blocked (README: Known limitations).
      state = "clear";
      hideBanner();
      return "clear";
    }
    if (result?.kind !== "ok" || !result.data) {
      showUnchecked(el, result?.kind);
      return "pending";
    }
    const data = result.data;
    if (!data.requiresDecision) {
      state = "clear";
      hideBanner();
      return "clear";
    }
    state = "pending";
    currentFlags = data.flags;
    headline.textContent = "Check before you send";
    noticeEl.textContent = data.notice ?? "";
    flagsEl.innerHTML = "";
    for (const f of data.flags) {
      const li = document.createElement("li");
      const cat = document.createElement("span");
      cat.className = "cat";
      cat.textContent = categoryLabel(f.category) + ": ";
      const expl = document.createElement("span");
      expl.textContent = f.explanation; // textContent only — never innerHTML (SECURITY_RULES.md §1)
      li.append(cat, expl);
      flagsEl.appendChild(li);
    }
    hideBtn.style.display = data.flags.length > 0 ? "" : "none";
    showBanner(el);
    return "pending";
  }

  function screen(el) {
    const text = getText(el).trim();
    if (!text) return Promise.resolve("clear");
    if (inflight?.text === text) return inflight.promise;
    if (text === lastScreenedText) return Promise.resolve(state === "pending" ? "pending" : "clear");
    const promise = runScreen(el, text).finally(() => {
      if (inflight?.promise === promise) inflight = null;
    });
    inflight = { text, promise };
    return promise;
  }

  function scheduleScreen(el) {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => screen(el), DEBOUNCE_MS);
  }

  // ---- replaying a submit we held back ---------------------------------
  function replay(action) {
    bypass = true;
    try {
      action();
    } finally {
      bypass = false;
    }
  }

  function resubmit(el) {
    const btn = findSendButton(el);
    if (btn) {
      replay(() => btn.click());
      return;
    }
    el.focus();
    replay(() =>
      el.dispatchEvent(
        new KeyboardEvent("keydown", {
          key: "Enter",
          code: "Enter",
          keyCode: 13,
          which: 13,
          bubbles: true,
          cancelable: true,
          composed: true,
        }),
      ),
    );
  }

  // Once a prompt has gone out, forget it, so typing the same flagged text
  // again is screened again rather than waved through.
  function forgetAfterSend(el, text) {
    setTimeout(() => {
      if (getText(el).trim() !== text) {
        lastScreenedText = "";
        state = "clear";
      }
    }, 600);
  }

  // The gate every send attempt passes through. Returns true when the
  // attempt must be held back. Screening is debounced and asynchronous,
  // and a student who presses Enter right after the last letter always
  // beats it, so "has a check already flagged this?" is not enough: text
  // that has not been screened yet is held, checked now, and replayed
  // only if it comes back clear.
  function holdSubmit(el, replaySubmit) {
    if (bypass) return false;
    const text = getText(el).trim();
    if (!text) return false;
    if (text === lastScreenedText && !inflight) {
      if (state === "pending") {
        showBanner(el);
        return true;
      }
      forgetAfterSend(el, text);
      return false;
    }
    if (debounceTimer) clearTimeout(debounceTimer);
    activeInput = el;
    screen(el).then((verdict) => {
      if (verdict === "clear") {
        forgetAfterSend(el, text);
        replaySubmit();
      }
    });
    return true;
  }

  function block(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
  }

  // ---- banner actions --------------------------------------------------
  function resolveAndSend() {
    if (!activeInput) return;
    state = "resolved";
    hideBanner();
    const el = activeInput;
    // Let the page's editor absorb any text change before the send.
    setTimeout(() => {
      resubmit(el);
      // Sent: forget it, so the same text typed again is screened again.
      lastScreenedText = "";
      state = "clear";
    }, 50);
  }

  hideBtn.addEventListener("click", () => {
    if (!activeInput) return;
    let text = getText(activeInput).trim();
    // Replace from the end so earlier offsets stay valid.
    const sorted = [...currentFlags].sort((a, b) => b.startIndex - a.startIndex);
    for (const f of sorted) {
      text = text.slice(0, f.startIndex) + `[REDACTED_${f.category.toUpperCase()}]` + text.slice(f.endIndex);
    }
    lastScreenedText = text.trim();
    state = "resolved";
    setText(activeInput, text);
    if (debounceTimer) clearTimeout(debounceTimer);
    lastScreenedText = getText(activeInput).trim();
    resolveAndSend();
  });
  sendAnywayBtn.addEventListener("click", resolveAndSend);
  editBtn.addEventListener("click", () => {
    hideBanner();
    activeInput?.focus();
    lastScreenedText = "";
    state = "clear"; // the student is about to change the text; it is screened again
  });

  // ---- page-level listeners (capture: before the site's own handlers) --
  window.addEventListener(
    "input",
    (e) => {
      const el = editableFrom(e);
      if (!el) return;
      activeInput = el;
      if (getText(el).trim() !== lastScreenedText) {
        if (state !== "clear") hideBanner();
        state = "clear";
        scheduleScreen(el);
      }
    },
    true,
  );

  window.addEventListener(
    "keydown",
    (e) => {
      if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
      const el = editableFrom(e);
      if (!el) return;
      if (holdSubmit(el, () => resubmit(el))) block(e);
    },
    true,
  );

  window.addEventListener(
    "click",
    (e) => {
      if (e.composedPath().includes(host)) return; // our own banner buttons
      const btn = eventElement(e)?.closest?.(BUTTON);
      if (!btn || !isSendButton(btn)) return;
      const el = activeInput?.isConnected ? activeInput : null;
      if (!el) return;
      if (holdSubmit(el, () => replay(() => btn.click()))) block(e);
    },
    true,
  );

  window.addEventListener(
    "submit",
    (e) => {
      const form = e.target;
      const el = activeInput?.isConnected && form.contains?.(activeInput) ? activeInput : null;
      if (!el) return;
      if (holdSubmit(el, () => replay(() => form.requestSubmit()))) block(e);
    },
    true,
  );
})();
