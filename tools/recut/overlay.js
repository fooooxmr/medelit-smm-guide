const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer-core");

const cfg = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const mode = process.argv[3] || "full";
const outDir = mode === "full" ? "/tmp/recut/ov/" + cfg.key : "/tmp/recut/pv/" + cfg.key;

(async () => {
  fs.rmSync(outDir, { recursive: true, force: true });
  fs.mkdirSync(outDir, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: process.env.CHROME || "/usr/bin/google-chrome", headless: "new",
    args: ["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"]
  });
  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(__dirname, "overlay.html"), { waitUntil: "networkidle0" });
  await page.evaluate(c => window.setup(c), cfg);
  await page.evaluate(() => document.fonts.ready);
  const fps = 30;
  const times = mode === "full"
    ? Array.from({ length: Math.round(cfg.duration * fps) }, (_, i) => i / fps)
    : mode.split(",").map(Number);
  for (let i = 0; i < times.length; i++) {
    await page.evaluate(t => window.seek(t), times[i]);
    const name = mode === "full" ? String(i).padStart(4, "0") + ".png" : times[i].toFixed(2) + ".png";
    await page.screenshot({ path: path.join(outDir, name), type: "png", omitBackground: true });
  }
  await browser.close();
  console.log("overlay", cfg.key, times.length);
})().catch(e => { console.error(e); process.exit(1); });
