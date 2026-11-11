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
  // Build tag, visible on every page this runs on (bottom-right corner, tiny,
  // out of the way). Bump the date whenever this file changes. If the page
  // doesn't show this exact tag after a reload, Chrome is still running an
  // older cached copy — that fact is now checkable by looking at the page,
  // not by guessing from symptoms.
  const BUILD = "2026-11-11-preview-v6";
  const tag = document.createElement("div");
  tag.textContent = `SentryPrompt build ${BUILD}`;
  tag.style.cssText =
    "position:fixed;bottom:4px;right:4px;z-index:2147483647;font:10px/1.4 monospace;" +
    "background:#1a1a1a;color:#9fe3b0;padding:2px 6px;border-radius:4px;opacity:.85;pointer-events:none;";
  document.documentElement.appendChild(tag);
  // Second line, directly under the build tag: the last Enter keypress this
  // script actually saw, and what it decided — on the page itself, so a
  // single screenshot after pressing Enter shows the real decision with no
  // DevTools step at all.
  const statusTag = document.createElement("div");
  statusTag.textContent = "last Enter: (none yet)";
  statusTag.style.cssText =
    "position:fixed;bottom:22px;right:4px;z-index:2147483647;font:10px/1.4 monospace;" +
    "background:#1a1a1a;color:#ffd27a;padding:2px 6px;border-radius:4px;opacity:.85;pointer-events:none;" +
    "max-width:420px;white-space:pre-wrap;text-align:right;";
  document.documentElement.appendChild(statusTag);
  function setStatus(text) {
    statusTag.textContent = `last Enter: ${text}`;
  }

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
    // type defaults to "submit" for ANY plain <button>, form or no form —
    // only meaningful as a signal when there is an actual form it submits.
    if (btn.type === "submit" && btn.form) return true;
    return ["aria-label", "data-testid", "title", "id"].some((a) => SEND_HINT.test(btn.getAttribute(a) ?? ""));
  }

  // The send button near the prompt box, used only to resubmit after Enter
  // was held back (there is no click event to reuse in that case, so one
  // has to be found). Many real composers use an icon-only button with no
  // label at all for isSendButton to match, so this also accepts a
  // container with exactly one enabled button — but a composer with
  // several buttons (a microphone, attachments, send) is genuinely
  // ambiguous here, which is exactly why the click path below does not
  // rely on this guess at all; it already knows which button was clicked.
  function findSendButton(el) {
    for (let node = el.parentElement, depth = 0; node && depth < 10; node = node.parentElement, depth++) {
      const candidates = [...node.querySelectorAll(BUTTON)].filter((b) => !b.disabled);
      const confident = candidates.find(isSendButton);
      if (confident) return confident;
      if (candidates.length === 1) return candidates[0];
    }
    return null;
  }

  // Is candidate inside the same nearby container as the prompt box —
  // without trying to also decide it is *the* send button among possibly
  // several (mic, attachments, send). A real click already answers "which
  // button," this only answers "is it part of this composer at all."
  function nearInput(el, candidate) {
    for (let node = el.parentElement, depth = 0; node && depth < 10; node = node.parentElement, depth++) {
      if (node.contains(candidate)) return true;
    }
    return false;
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
      .banner { position: fixed; z-index: 2147483647; width: 400px; max-width: calc(100vw - 32px);
        font-family: system-ui, sans-serif; background: #fff; border: 1px solid #d8d4cc; border-radius: 12px;
        box-shadow: 0 10px 32px rgba(0,0,0,.22); padding: 18px 20px; color: #0b0b0b; display: none; }
      .banner.show { display: block; }
      .title { font-weight: 700; font-size: 17px; margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
      .dot { width: 11px; height: 11px; border-radius: 50%; background: #eb6834; flex: none; }
      ul { margin: 8px 0 10px; padding-left: 20px; font-size: 14px; line-height: 1.4; }
      li { margin-bottom: 6px; }
      .cat { font-weight: 700; }
      .context { font-size: 13px; color: #45433f; margin-top: 10px; line-height: 1.5; }
      .preview-label { font-size: 12px; font-weight: 600; color: #52514e; margin-top: 12px; margin-bottom: 4px; }
      .preview { font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 13px; background: #f5f3ee;
        border: 1px solid #e3e0d8; border-radius: 8px; padding: 10px 12px; white-space: pre-wrap; word-break: break-word;
        max-height: 140px; overflow-y: auto; color: #1a1a1a; }
      .preview mark { background: #ffe6a3; color: inherit; border-radius: 3px; padding: 0 2px; }
      .row { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 14px; justify-content: flex-end; }
      button { font-size: 13px; padding: 7px 14px; border-radius: 7px; border: 1px solid #ccc; background: #f3f1ec;
        cursor: pointer; }
      button.primary { background: #1baf7a; color: #fff; border-color: #1baf7a; font-weight: 600; }
      .notice { font-size: 13px; color: #52514e; margin-top: 10px; line-height: 1.4; }
    </style>
    <div class="banner" part="banner">
      <div class="title"><span class="dot"></span><span class="headline"></span></div>
      <ul class="flags"></ul>
      <div class="context">
        AI providers can store or use what you send them, including to train future
        models — once sent, you can't take it back.
      </div>
      <div class="preview-label" style="display:none">If you hide the details, this is what will be sent instead:</div>
      <div class="preview" style="display:none"></div>
      <div class="notice"></div>
      <div class="row">
        <button class="sendAnyway">Send anyway</button>
        <button class="edit">Edit my prompt</button>
        <button class="hide primary" style="display:none">Hide details and send</button>
      </div>
    </div>
  `;
  document.documentElement.appendChild(host);
  const banner = shadow.querySelector(".banner");
  const previewLabel = shadow.querySelector(".preview-label");
  const previewEl = shadow.querySelector(".preview");
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
  // The exact resend action for whatever is currently held back (reuses the
  // real clicked button or submitted form, not a fresh guess at send time) —
  // set the instant something is held, used once the student resolves the
  // banner, so "Send anyway" after a button click clicks that same button
  // rather than falling back to a synthetic keypress real sites can ignore.
  let pendingResubmit = null;

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

  function showUnchecked(el, kind, detail) {
    state = "pending";
    currentFlags = [];
    headline.textContent = "We couldn't fully check this prompt";
    noticeEl.textContent =
      kind === "rate_limited"
        ? "Too many checks in the last minute. Wait a moment, or send anyway."
        : `The screening service did not answer in time.${detail ? ` (${detail})` : ""}`;
    flagsEl.innerHTML = "";
    hideBtn.style.display = "none";
    showPreview(null);
    showBanner(el);
  }

  // Resolves to "clear", "pending", or "stale" (the text changed while the
  // check was running, so this answer says nothing about what is there now).
  async function runScreen(el, text) {
    let result;
    try {
      result = await chrome.runtime.sendMessage({ type: "SCREEN_PROMPT", text });
    } catch (err) {
      // No response at all from background.js — e.g. the service worker
      // itself failed to start. detail: message-port errors look identical
      // to every other failure otherwise, so the real cause gets shown too.
      result = { kind: "unavailable", detail: `sendMessage threw: ${err?.message || err}` };
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
      showUnchecked(el, result?.kind, result?.detail);
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
    const hasFlags = data.flags.length > 0;
    hideBtn.style.display = hasFlags ? "" : "none";
    showPreview(hasFlags ? redact(text, data.flags) : null);
    showBanner(el);
    return "pending";
  }

  // Replaces each flagged span with [REDACTED_<CATEGORY>], returning both
  // the plain replacement text (what actually gets sent) and a version with
  // each placeholder wrapped for highlighting (what the preview shows) —
  // built from the same positions, so the two can never drift apart.
  function redact(text, flags) {
    const sorted = [...flags].sort((a, b) => b.startIndex - a.startIndex);
    let plain = text;
    let marked = text;
    for (const f of sorted) {
      const placeholder = `[REDACTED_${f.category.toUpperCase()}]`;
      plain = plain.slice(0, f.startIndex) + placeholder + plain.slice(f.endIndex);
      marked = marked.slice(0, f.startIndex) + "\u0000" + placeholder + "\u0001" + marked.slice(f.endIndex);
    }
    return { plain, marked };
  }

  function showPreview(redacted) {
    if (!redacted) {
      previewLabel.style.display = "none";
      previewEl.style.display = "none";
      return;
    }
    previewLabel.style.display = "";
    previewEl.style.display = "";
    previewEl.innerHTML = "";
    const parts = redacted.marked.split(/\u0000|\u0001/);
    parts.forEach((part, i) => {
      if (i % 2 === 1) {
        const mark = document.createElement("mark");
        mark.textContent = part;
        previewEl.appendChild(mark);
      } else if (part) {
        previewEl.appendChild(document.createTextNode(part));
      }
    });
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

  function dispatchEnter(el) {
    el.focus();
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
    );
  }

  // Per-site overrides for the one thing that genuinely does need to know
  // the real site: how it actually wants to be resubmitted. Generic
  // heuristics (nearInput, findSendButton) and a plain redispatched Enter
  // cover most composers, same as the open-source "Ctrl+Enter Sender"
  // extension's own coverage of ~19 sites found — but ChatGPT's own send
  // button lives in a real <form>, which a dispatched Enter does not
  // reliably trigger there (its keyboard shortcuts are user-configurable),
  // while every other site in that extension's table resends by dispatching
  // Enter directly, never clicking anything. Adapted from that project
  // (masachika-kamada/ChatGPT-Ctrl-Enter-Sender, content/ctrl-enter-handler.js).
  const RESUBMIT_OVERRIDES = {
    "chatgpt.com": (el) => {
      if (el.id !== "prompt-textarea" && !el.hasAttribute?.("data-composer-markdown")) return false;
      const button = el.closest("form")?.querySelector('button[type="submit"]:not([disabled])');
      if (!button) return false;
      replay(() => button.click());
      return true;
    },
    "chat.openai.com": (el) => RESUBMIT_OVERRIDES["chatgpt.com"](el),
    "gemini.google.com": (el) => {
      const isComposer =
        el.tagName === "TEXTAREA" || (el.tagName === "DIV" && el.classList.contains("ql-editor"));
      if (!isComposer) return false;
      replay(() => dispatchEnter(el));
      return true;
    },
  };

  function resubmit(el) {
    if (RESUBMIT_OVERRIDES[location.hostname]?.(el)) return;
    const btn = findSendButton(el);
    if (btn) {
      replay(() => btn.click());
      return;
    }
    replay(() => dispatchEnter(el));
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
        pendingResubmit = replaySubmit;
        showBanner(el);
        return true;
      }
      forgetAfterSend(el, text);
      return false;
    }
    if (debounceTimer) clearTimeout(debounceTimer);
    activeInput = el;
    pendingResubmit = replaySubmit;
    screen(el).then((verdict) => {
      if (verdict === "clear") {
        forgetAfterSend(el, text);
        pendingResubmit = null;
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
    // The exact click or submit that was held back, if there was one —
    // far more reliable than searching for a button fresh at this point,
    // or falling back to a synthetic keypress a real site may just ignore.
    const doResend = pendingResubmit ?? (() => resubmit(el));
    pendingResubmit = null;
    // Let the page's editor absorb any text change before the send.
    setTimeout(() => {
      doResend();
      // Sent: forget it, so the same text typed again is screened again.
      lastScreenedText = "";
      state = "clear";
    }, 50);
  }

  hideBtn.addEventListener("click", () => {
    if (!activeInput) return;
    const text = redact(getText(activeInput).trim(), currentFlags).plain;
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
      if (e.key !== "Enter") return;
      if (e.shiftKey || e.isComposing) {
        setStatus(`ignored (shiftKey=${e.shiftKey} isComposing=${e.isComposing})`);
        return;
      }
      const el = editableFrom(e);
      if (!el) {
        setStatus(`no editable found (event target: ${eventElement(e)?.tagName ?? "none"})`);
        return;
      }
      const held = holdSubmit(el, () => resubmit(el));
      setStatus(`editable=${el.tagName.toLowerCase()} held=${held} state=${state}`);
      if (held) block(e);
    },
    true,
  );

  window.addEventListener(
    "click",
    (e) => {
      if (e.composedPath().includes(host)) return; // our own banner buttons
      const btn = eventElement(e)?.closest?.(BUTTON);
      const el = activeInput?.isConnected ? activeInput : null;
      if (!btn || !el) {
        setStatus(`click ignored (button=${!!btn} activeInput=${!!el})`);
        return;
      }
      // The click itself already answers "which button" — no label
      // matching, no guessing between a mic/attachment/send button needed.
      // Only question left: is it actually part of this composer at all.
      if (!nearInput(el, btn)) {
        setStatus(`click on unrelated button ignored`);
        return;
      }
      const held = holdSubmit(el, () => replay(() => btn.click()));
      setStatus(`send-button click held=${held} state=${state}`);
      if (held) block(e);
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
  console.log("[SentryPrompt] content.js fully loaded, listeners attached");
})();
