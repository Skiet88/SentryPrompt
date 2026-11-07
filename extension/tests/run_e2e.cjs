// Loads the real unpacked extension in a real Chromium instance (the one
// pre-installed in this environment, via Playwright) against a local
// fixture page, and drives it exactly as a student would: type, get
// flagged, try to send, hide the flagged values, send for real. All
// screening calls go to the real backend started by the harness (see
// extension/README.md) — nothing here is mocked.
//
// Run: node extension/tests/run_e2e.mjs
const { chromium } = require("playwright");
const { mkdtempSync, cpSync, writeFileSync, readFileSync, mkdirSync, rmSync } = require("node:fs");
const { tmpdir } = require("node:os");
const path = require("node:path");
const http = require("node:http");

const EXT_SRC = path.resolve(__dirname, "..");
const FIXTURE_DIR = __dirname;

let failures = 0;
function assert(cond, msg) {
  if (!cond) {
    failures++;
    console.log(`FAIL: ${msg}`);
  } else {
    console.log(`ok:   ${msg}`);
  }
}

function serveFixture(dir) {
  return new Promise((resolve) => {
    const server = http.createServer((req, res) => {
      const file = path.join(dir, req.url === "/" ? "/fixture.html" : req.url);
      try {
        const body = readFileSync(file);
        res.writeHead(200, { "Content-Type": "text/html" });
        res.end(body);
      } catch {
        res.writeHead(404);
        res.end();
      }
    });
    server.listen(0, "127.0.0.1", () => resolve(server));
  });
}

async function main() {
  const server = await serveFixture(FIXTURE_DIR);
  const { port } = server.address();
  const fixtureOrigin = `http://127.0.0.1:${port}`;

  // Build a test copy of the extension: identical files, except the
  // manifest also matches the local fixture's origin (the real
  // manifest.json shipped to students only matches chatgpt.com).
  const extDir = mkdtempSync(path.join(tmpdir(), "sentryprompt-ext-"));
  cpSync(EXT_SRC, extDir, { recursive: true, filter: (src) => !src.includes(`${path.sep}tests`) });
  const manifest = JSON.parse(readFileSync(path.join(EXT_SRC, "manifest.json")));
  manifest.content_scripts[0].matches.push(`${fixtureOrigin}/*`);
  manifest.host_permissions.push(`${fixtureOrigin}/*`);
  writeFileSync(path.join(extDir, "manifest.json"), JSON.stringify(manifest, null, 2));

  const SHOTS = path.join(EXT_SRC, "screenshots");
  mkdirSync(SHOTS, { recursive: true });

  const profileDir = mkdtempSync(path.join(tmpdir(), "sentryprompt-profile-"));
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: false,
    viewport: { width: 760, height: 620 },
    deviceScaleFactor: 2,
    args: [`--disable-extensions-except=${extDir}`, `--load-extension=${extDir}`, "--no-sandbox"],
  });

  // Find the extension's id from its background service worker.
  let [sw] = context.serviceWorkers();
  if (!sw) sw = await context.waitForEvent("serviceworker", { timeout: 10000 });
  const extensionId = sw.url().split("/")[2];
  console.log("extension id:", extensionId);

  const page = await context.newPage();
  await page.setViewportSize({ width: 300, height: 260 });

  // ---- log in via the real popup UI, against the real Supabase stand-in --
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  await page.waitForSelector("#loginBtn");
  await page.screenshot({ path: path.join(SHOTS, "ext01_popup_login.png") });
  await page.fill("#email", "student.demo@example.com");
  await page.fill("#password", "Demo-Passw0rd!");
  await page.click("#loginBtn");
  await page.waitForSelector("#status");
  const status = await page.textContent("#status");
  assert(status.includes("student.demo@example.com"), `popup shows logged-in status (got: "${status}")`);
  await page.screenshot({ path: path.join(SHOTS, "ext02_popup_logged_in.png") });

  // ---- clean prompt: no banner, Enter submits immediately ---------------
  const fx1 = await context.newPage();
  await fx1.goto(fixtureOrigin);
  await fx1.click("#prompt-textarea");
  await fx1.keyboard.type("What is the difference between a stack and a queue?");
  await fx1.waitForTimeout(1500);
  const bannerShown1 = await fx1.evaluate(() =>
    document.querySelector("[data-sentryprompt]")?.shadowRoot?.querySelector(".banner.show") !== null,
  );
  assert(!bannerShown1, "a clean prompt shows no banner");
  await fx1.keyboard.press("Enter");
  await fx1.waitForTimeout(300);
  let logText1 = await fx1.textContent("#log");
  assert(logText1.includes("SUBMITTED: What is the difference"), "a clean prompt submits on Enter");

  // ---- flagged prompt: banner blocks Enter, Hide & continue redacts -----
  const fx2 = await context.newPage();
  await fx2.goto(fixtureOrigin);
  await fx2.click("#prompt-textarea");
  await fx2.keyboard.type("My ID number is 8001015009087, please help me write an email.");
  await fx2.waitForFunction(
    () => document.querySelector("[data-sentryprompt]")?.shadowRoot?.querySelector(".banner.show") !== null,
    { timeout: 10000 },
  );
  const bannerText = await fx2.evaluate(
    () => document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".flags").textContent,
  );
  assert(bannerText.includes("Id number") || bannerText.toLowerCase().includes("id number"), "banner names the ID number category");
  assert(bannerText.toLowerCase().includes("identity fraud"), `banner shows the real backend explanation (got: "${bannerText}")`);
  await fx2.screenshot({ path: path.join(SHOTS, "ext03_flagged_banner.png"), clip: { x: 0, y: 0, width: 650, height: 280 } });

  await fx2.keyboard.press("Enter");
  await fx2.waitForTimeout(300);
  let logText2 = await fx2.textContent("#log");
  assert(!logText2.includes("SUBMITTED"), "Enter is blocked while the banner is pending");

  await fx2.evaluate(() =>
    document.querySelector("[data-sentryprompt]").shadowRoot.querySelector(".hide").click(),
  );
  await fx2.waitForTimeout(300);
  const redactedText = await fx2.textContent("#prompt-textarea");
  assert(redactedText.includes("[REDACTED_SA_ID]"), `"Hide details and send" redacts the ID number (got: "${redactedText}")`);
  assert(!redactedText.includes("8001015009087"), "the real ID number no longer appears in the input");
  await fx2.screenshot({ path: path.join(SHOTS, "ext04_redacted_before_send.png"), clip: { x: 0, y: 0, width: 650, height: 200 } });

  await fx2.keyboard.press("Enter");
  await fx2.waitForTimeout(300);
  logText2 = await fx2.textContent("#log");
  assert(logText2.includes("SUBMITTED") && logText2.includes("[REDACTED_SA_ID]"), "Enter submits the redacted text once resolved");

  // ---- logged out: no banner, nothing blocked (documented limitation) ---
  await page.goto(`chrome-extension://${extensionId}/popup.html`);
  await page.click("#logoutBtn");
  await page.waitForSelector("#loginBtn");

  const fx3 = await context.newPage();
  await fx3.goto(fixtureOrigin);
  await fx3.click("#prompt-textarea");
  await fx3.keyboard.type("My ID number is 8001015009087 again.");
  await fx3.waitForTimeout(1500);
  const bannerShown3 = await fx3.evaluate(
    () => document.querySelector("[data-sentryprompt]")?.shadowRoot?.querySelector(".banner.show") !== null,
  );
  assert(!bannerShown3, "logged out: no banner is shown (screening is skipped, not blocking)");
  await fx3.keyboard.press("Enter");
  await fx3.waitForTimeout(300);
  const logText3 = await fx3.textContent("#log");
  assert(logText3.includes("SUBMITTED"), "logged out: Enter still submits (documented limitation, not fail-closed)");

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
