// Content script (classic script, not a module — Manifest V3 does not allow
// "type": "module" content scripts). Runs in the page's own context, so it
// NEVER fetches anything itself and NEVER sees the session token: it only
// sends the typed text to background.js over chrome.runtime.sendMessage and
// gets back a verdict. This also sidesteps the host page's own
// Content-Security-Policy, which may block a page-context fetch to a
// different origin even when the extension itself is allowed to reach it.
//
// DOM selectors below are best-effort guesses at ChatGPT's current markup
// (a contenteditable "ProseMirror" prompt box, submitted by Enter or a send
// button). Sites like this change their markup without notice, so every
// lookup tries several candidates in order and gives up quietly — logging
// one line to the console, never throwing — if none match (documented
// fail-silent fallback, PROJECT_BACKLOG.md Increment 18).
(() => {
  const INPUT_SELECTORS = [
    "#prompt-textarea",
    "div[contenteditable='true'][id*='prompt']",
    "form textarea",
    "textarea",
  ];
  const SEND_BUTTON_SELECTORS = [
    "button[data-testid='send-button']",
    "button[aria-label='Send prompt']",
    "button[aria-label*='Send' i]",
    "form button[type='submit']",
  ];
  const DEBOUNCE_MS = 800;

  function query(selectors) {
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) return el;
    }
    return null;
  }

  function getText(el) {
    if (el.tagName === "TEXTAREA") return el.value;
    return el.innerText ?? el.textContent ?? "";
  }

  function setText(el, text) {
    if (el.tagName === "TEXTAREA") {
      const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
      setter.call(el, text);
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
      .dot.warn { background: #fab219; }
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
        <button class="edit">Edit my prompt</button>
        <button class="sendAnyway">Send anyway</button>
        <button class="hide" style="display:none">Hide details and send</button>
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
    const r = target.getBoundingClientRect();
    banner.style.left = `${Math.max(8, r.left)}px`;
    banner.style.top = `${Math.max(8, r.top - banner.offsetHeight - 10)}px`;
    banner.classList.add("show");
  }
  function hideBanner() {
    banner.classList.remove("show");
  }

  // ---- per-input state ----------------------------------------------
  // "clear"    -> nothing to warn about, sending proceeds normally
  // "pending"  -> flags exist (or the check failed / fails closed), and
  //               nothing has been sent to the page yet: sending is blocked
  // "resolved" -> the student chose an action for the current text; the
  //               next edit to the text goes back to "clear"/debounce again
  let state = "clear";
  let lastScreenedText = "";
  let currentFlags = [];
  let debounceTimer = null;
  let activeInput = null;

  // Same plain-language labels as frontend/src/chat/categories.ts, kept in
  // sync manually since the extension has no build step to share code with
  // the frontend; the server-sent explanation is what actually matters, and
  // it is never hard-coded here.
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

  async function screen(el) {
    const text = getText(el).trim();
    if (!text || text === lastScreenedText) return;
    lastScreenedText = text;
    const result = await chrome.runtime.sendMessage({ type: "SCREEN_PROMPT", text });
    if (getText(el).trim() !== text) return; // the student kept typing; a newer screen is already queued

    if (result?.kind === "not_logged_in") {
      // Logged-out visitors are reminded, not blocked (README: Known limitations).
      state = "clear";
      hideBanner();
      return;
    }
    if (result?.kind === "rate_limited" || result?.kind === "unavailable") {
      state = "pending";
      currentFlags = [];
      headline.textContent = "We couldn't fully check this prompt";
      noticeEl.textContent =
        result.kind === "rate_limited"
          ? "Too many checks in the last minute. Wait a moment, or send anyway."
          : "The screening service did not answer in time.";
      flagsEl.innerHTML = "";
      hideBtn.style.display = "none";
      showBanner(el);
      return;
    }
    const data = result.data;
    if (!data.requiresDecision) {
      state = "clear";
      hideBanner();
      return;
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
  }

  function scheduleScreen(el) {
    activeInput = el;
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => screen(el), DEBOUNCE_MS);
  }

  function applyHideAndContinue() {
    if (!activeInput) return;
    let text = getText(activeInput);
    // Replace from the end so earlier offsets stay valid.
    const sorted = [...currentFlags].sort((a, b) => b.startIndex - a.startIndex);
    for (const f of sorted) {
      text = text.slice(0, f.startIndex) + `[REDACTED_${f.category.toUpperCase()}]` + text.slice(f.endIndex);
    }
    setText(activeInput, text);
    lastScreenedText = text.trim();
    resolveAndHide();
  }

  function resolveAndHide() {
    state = "resolved";
    hideBanner();
  }

  hideBtn.addEventListener("click", applyHideAndContinue);
  sendAnywayBtn.addEventListener("click", resolveAndHide);
  editBtn.addEventListener("click", () => {
    hideBanner();
    activeInput?.focus();
    state = "clear"; // the student is about to change the text; re-screen once they do
  });

  // Screening is debounced and asynchronous (DEBOUNCE_MS, then a network
  // round trip), but a student who finishes a short sentence and presses
  // Enter right away will beat that every time — 800ms plus a network call
  // is longer than most people pause between typing and submitting. So
  // Enter/Send cannot simply check "is the result already in" (state ===
  // "pending"); if the current text has never been screened, this forces
  // an immediate check and holds the submit until it resolves, giving a
  // fast typist the same fail-closed-until-cleared guarantee the debounced
  // path already gives a slower one.
  function interceptSubmit(el, resubmit) {
    if (state === "pending") return true; // already known-flagged: block, banner is up
    const currentText = getText(el).trim();
    if (!currentText || currentText === lastScreenedText) return false; // already screened (or resolved) for this exact text
    if (debounceTimer) clearTimeout(debounceTimer);
    activeInput = el;
    screen(el).then(() => {
      if (state === "clear") resubmit();
      // else "pending": screen() already showed the banner, nothing more to do.
    });
    return true; // block this attempt; the recheck above will resubmit if clear
  }

  function attach(el) {
    if (el.dataset.sentrypromptAttached) return;
    el.dataset.sentrypromptAttached = "true";
    el.addEventListener("input", () => {
      if (getText(el).trim() !== lastScreenedText) state = "clear";
      scheduleScreen(el);
    });
    // Capture phase: see Enter before the page's own React handler does.
    el.addEventListener(
      "keydown",
      (e) => {
        if (e.key !== "Enter" || e.shiftKey) return;
        if (interceptSubmit(el, () => query(SEND_BUTTON_SELECTORS)?.click())) {
          e.preventDefault();
          e.stopPropagation();
          if (state === "pending") showBanner(el);
        }
      },
      true,
    );
  }

  function attachSendButton(btn) {
    if (!btn || btn.dataset.sentrypromptAttached) return;
    btn.dataset.sentrypromptAttached = "true";
    btn.addEventListener(
      "click",
      (e) => {
        const el = activeInput || query(INPUT_SELECTORS);
        if (!el) return;
        if (interceptSubmit(el, () => btn.click())) {
          e.preventDefault();
          e.stopPropagation();
          if (state === "pending") showBanner(el);
        }
      },
      true,
    );
  }

  function scan() {
    const input = query(INPUT_SELECTORS);
    if (input) attach(input);
    attachSendButton(query(SEND_BUTTON_SELECTORS));
  }

  scan();
  new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
})();
