// Tests content.js's site-agnostic send gate in a real Chromium with the
// real unpacked extension, against tests/fixture_generic.html. Unlike
// run_e2e.cjs, the backend and Supabase Auth here are a small in-process
// MOCK (flags any 13-digit number): this test is about the browser side —
// above all that a prompt sent the instant typing stops is still screened.
//
// Run: xvfb-run -a node extension/tests/run_generic_e2e.cjs
const { chromium } = require("playwright");
const { mkdtempSync, cpSync, writeFileSync, readFileSync, rmSync } = require("node:fs");
const { tmpdir } = require("node:os");
const path = require("node:path");
const http = require("node:http");

const EXT_SRC = path.resolve(__dirname, "..");
const ID = "8001015009087";
const FLAGGED = `My ID number is ${ID}, please help me write an email.`;

let failures = 0;
function assert(cond, msg) {
  if (!cond) failures++;
  console.log(`${cond ? "ok:  " : "FAIL:"} ${msg}`);
}

let backendDown = false;
let screenCalls = 0;
function startServer() {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      let body = "";
      req.on("data", (c) => (body += c));
      req.on("end", () => {
        const json = (code, obj) => {
          res.writeHead(code, { "Content-Type": "application/json" });
          res.end(JSON.stringify(obj));
        };
        if (req.url.startsWith("/auth/v1/token")) {
          return json(200, { access_token: "test-token", expires_at: Math.floor(Date.now() / 1000) + 3600, user: { email: "student.demo@example.com" } });
        }
        if (req.url.startsWith("/auth/v1/logout")) return json(204, {});
        if (req.url === "/api/prompts/screen") {
          screenCalls++;
          if (backendDown) return json(500, { error: "down" });
          const { text } = JSON.parse(body);
          const m = /\b\d{13}\b/.exec(text);
          return setTimeout(
            () =>
              json(200, {
                requiresDecision: !!m,
                notice: null,
                flags: m
                  ? [{ category: "SA_ID", startIndex: m.index, endIndex: m.index + 13, detectorSource: "rule", explanation: "This looks like a South African ID number." }]
                  : [],
              }),
            400, // a realistic network delay, so "Enter beats the check" is really exercised
          );
        }
        try {
          const file = path.join(__dirname, req.url.split("?")[0] === "/" ? "fixture_generic.html" : req.url.split("?")[0]);
          const content = readFileSync(file);
          res.writeHead(200, { "Content-Type": "text/html" });
          res.end(content);
        } catch {
          res.writeHead(404);
          res.end();
        }
      });
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

const bannerShown = (page) =>
  page.evaluate(() => !!document.querySelector("[data-sentryprompt]")?.shadowRoot?.querySelector(".banner.show"));
const bannerText = (page) =>
  page.evaluate(() => document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".banner").textContent);
const clickBanner = (page, cls) =>
  page.evaluate((c) => document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(c).click(), cls);
const logOf = (page) => page.textContent("#log");
const count = (s) => (s.match(/SUBMITTED/g) || []).length;

async function main() {
  const server = await startServer();
  const origin = `http://127.0.0.1:${server.address().port}`;

  const extDir = mkdtempSync(path.join(tmpdir(), "sentryprompt-ext-"));
  cpSync(EXT_SRC, extDir, { recursive: true, filter: (src) => !src.includes(`${path.sep}tests`) });
  const manifest = JSON.parse(readFileSync(path.join(EXT_SRC, "manifest.json")));
  manifest.content_scripts[0].matches.push(`${origin}/*`);
  manifest.host_permissions.push(`${origin}/*`);
  writeFileSync(path.join(extDir, "manifest.json"), JSON.stringify(manifest, null, 2));
  writeFileSync(
    path.join(extDir, "config.js"),
    `export const CONFIG = { BACKEND_URL: "${origin}", SUPABASE_URL: "${origin}", SUPABASE_PUBLISHABLE_KEY: "sb_publishable_test" };\n`,
  );

  const profileDir = mkdtempSync(path.join(tmpdir(), "sentryprompt-profile-"));
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    args: [`--disable-extensions-except=${extDir}`, `--load-extension=${extDir}`, "--no-sandbox"],
  });
  let [sw] = context.serviceWorkers();
  if (!sw) sw = await context.waitForEvent("serviceworker", { timeout: 10000 });
  const extensionId = sw.url().split("/")[2];

  const popup = await context.newPage();
  const login = async () => {
    await popup.goto(`chrome-extension://${extensionId}/popup.html`);
    await popup.waitForSelector("#loginBtn");
    await popup.fill("#email", "student.demo@example.com");
    await popup.fill("#password", "x");
    await popup.click("#loginBtn");
    await popup.waitForSelector("#logoutBtn");
  };
  await login();

  const open = async (mode) => {
    const p = await context.newPage();
    await p.goto(`${origin}/?mode=${mode}`);
    return p;
  };
  const RICH = ".box";

  // 1. THE reported bug: flagged text, Enter the instant typing stops.
  let p = await open("rich");
  await p.click(RICH);
  await p.keyboard.type(FLAGGED);
  await p.keyboard.press("Enter");
  await p.waitForTimeout(100);
  assert(count(await logOf(p)) === 0, "rich: instant Enter on flagged text is held back");
  await p.waitForFunction(() => !!document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".banner.show"), null, { timeout: 5000 });
  assert((await bannerText(p)).includes("ID number"), "rich: banner then names the ID number");
  await p.keyboard.press("Enter");
  await p.waitForTimeout(200);
  assert(count(await logOf(p)) === 0, "rich: Enter stays blocked while the banner is up");
  await clickBanner(p, ".hide");
  await p.waitForTimeout(500);
  let log = await logOf(p);
  assert(count(log) === 1 && log.includes("[REDACTED_SA_ID]") && !log.includes(ID), `rich: 'Hide details and send' sends the redacted text once (log: ${log.trim()})`);

  // 2. Clean text, instant Enter: held, checked, then sent exactly once.
  await p.click(RICH);
  await p.keyboard.type("What is a queue?");
  await p.keyboard.press("Enter");
  await p.waitForTimeout(1200);
  log = await logOf(p);
  assert(count(log) === 2 && log.includes("What is a queue?"), "rich: clean text with instant Enter is sent once, after the check");
  assert(!(await bannerShown(p)), "rich: no banner for clean text");

  // 3. Flagged text, instant click on the send button (which only exists once text is typed).
  p = await open("rich");
  await p.click(RICH);
  await p.keyboard.type(FLAGGED);
  await p.click("button[aria-label='Send prompt']");
  await p.waitForTimeout(100);
  assert(count(await logOf(p)) === 0, "rich: instant click on Send is held back");
  await p.waitForFunction(() => !!document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".banner.show"), null, { timeout: 5000 });
  await clickBanner(p, ".sendAnyway");
  await p.waitForTimeout(500);
  log = await logOf(p);
  assert(count(log) === 1 && log.includes(ID), "rich: 'Send anyway' sends the original once");
  // Same flagged text again must be screened again, not waved through.
  await p.waitForTimeout(700);
  await p.click(RICH);
  await p.keyboard.type(FLAGGED);
  await p.keyboard.press("Enter");
  await p.waitForTimeout(1200);
  assert(count(await logOf(p)) === 1 && (await bannerShown(p)), "rich: the same flagged text typed again is flagged again");

  // 4. Plain <textarea> in a <form>, unlabeled submit button.
  p = await open("plain");
  await p.click("textarea");
  await p.keyboard.type(FLAGGED);
  await p.keyboard.press("Enter");
  await p.waitForTimeout(1200);
  assert(count(await logOf(p)) === 0 && (await bannerShown(p)), "plain: instant Enter on flagged text is held and flagged");
  await clickBanner(p, ".edit");
  assert(!(await bannerShown(p)), "plain: 'Edit my prompt' closes the banner");
  await p.fill("textarea", "");
  await p.keyboard.type(FLAGGED);
  await p.click("button[type='submit']");
  await p.waitForTimeout(1200);
  assert(count(await logOf(p)) === 0 && (await bannerShown(p)), "plain: instant click on the unlabeled submit button is held and flagged");
  await clickBanner(p, ".hide");
  await p.waitForTimeout(500);
  log = await logOf(p);
  assert(count(log) === 1 && log.includes("[REDACTED_SA_ID]") && !log.includes(ID), "plain: 'Hide details and send' sends the redacted text once");
  await p.click("textarea");
  await p.keyboard.type("Explain recursion");
  await p.keyboard.press("Enter");
  await p.waitForTimeout(1200);
  assert(count(await logOf(p)) === 2, "plain: clean text with instant Enter is sent once");

  // 5. Screening service down: fail closed (NFR-015).
  backendDown = true;
  p = await open("rich");
  await p.click(RICH);
  await p.keyboard.type("Just a normal question");
  await p.keyboard.press("Enter");
  await p.waitForTimeout(1200);
  assert(count(await logOf(p)) === 0 && (await bannerText(p)).includes("couldn't fully check"), "service down: the prompt is held with a 'couldn't fully check' banner");
  backendDown = false;

  // 5b. Regression: an icon-only send button with no aria-label, no
  // data-testid, no title and no type="submit" — a bare <button> with an
  // <svg> inside, same as the real ChatGPT send button turned out to be.
  // isSendButton alone can never match this; findSendButton's "exactly one
  // enabled button nearby" fallback must be what holds it instead.
  p = await open("rich");
  await p.click(RICH);
  await p.keyboard.type(FLAGGED);
  await p.evaluate(() => {
    const btn = document.querySelector("button[aria-label='Send prompt']");
    btn.removeAttribute("aria-label");
    btn.innerHTML = "<svg><path d='M0 0'></path></svg>";
  });
  await p.click("#slot button");
  await p.waitForTimeout(100);
  assert(count(await logOf(p)) === 0, "icon-only send button: instant click on flagged text is held back");
  await p.waitForFunction(() => !!document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".banner.show"), null, { timeout: 5000 });
  await clickBanner(p, ".hide");
  await p.waitForTimeout(500);
  log = await logOf(p);
  assert(count(log) === 1 && log.includes("[REDACTED_SA_ID]") && !log.includes(ID), "icon-only send button: 'Hide details and send' sends the redacted text once");

  // 5c. Regression: more than one unlabelled button near the composer (a
  // microphone plus send, as on Gemini) — "the only enabled button nearby"
  // cannot disambiguate between them; the actual click must decide.
  p = await open("multi");
  await p.click(RICH);
  await p.keyboard.type(FLAGGED);
  await p.click("#send");
  await p.waitForTimeout(100);
  assert(count(await logOf(p)) === 0, "multiple buttons: instant click on the actual send button is still held back");
  await p.waitForFunction(() => !!document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".banner.show"), null, { timeout: 5000 });
  await clickBanner(p, ".sendAnyway");
  await p.waitForTimeout(500);
  log = await logOf(p);
  assert(count(log) === 1 && log.includes(ID), "multiple buttons: 'Send anyway' sends the original once, via the correct button");
  // The microphone is a different button in the same composer; clicking it
  // must never leak the typed prompt as a sent message.
  await p.click(RICH);
  await p.keyboard.type("Some unrelated draft");
  await p.click("#mic");
  await p.waitForTimeout(1200);
  log = await logOf(p);
  assert(!log.includes("Some unrelated draft"), "multiple buttons: clicking the microphone never sends the drafted text");

  // 6. Logged out: nothing is screened or blocked (documented limitation).
  await popup.click("#logoutBtn");
  await popup.waitForSelector("#loginBtn");
  const before = screenCalls;
  p = await open("rich");
  await p.click(RICH);
  await p.keyboard.type(FLAGGED);
  await p.keyboard.press("Enter");
  await p.waitForTimeout(1200);
  assert(count(await logOf(p)) === 1 && screenCalls === before, "logged out: sent normally, nothing sent for screening");

  await context.close();
  server.close();
  rmSync(extDir, { recursive: true, force: true });
  rmSync(profileDir, { recursive: true, force: true });
  console.log(failures === 0 ? "\nAll checks passed." : `\n${failures} check(s) FAILED.`);
  process.exit(failures === 0 ? 0 : 1);
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
