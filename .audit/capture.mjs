// Optional browser capture for a separately configured web adapter.
import { chromium } from "playwright";

const baseUrl = process.env.AUDIT_BASE_URL;
const outputDir = process.env.AUDIT_OUTPUT_DIR || ".audit/screenshots";

if (!baseUrl) {
  throw new Error("Set AUDIT_BASE_URL before running the browser audit.");
}

const pages = (process.env.AUDIT_PATHS || "/").split(",").map((path, index) => ({
  path,
  name: `${String(index).padStart(2, "0")}-${path.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "") || "root"}`,
}));

const browser = await chromium.launch();
const context = await browser.newContext({
  viewport: { width: 390, height: 844 },
  deviceScaleFactor: 2,
  isMobile: true,
  hasTouch: true,
});
const page = await context.newPage();

for (const target of pages) {
  try {
    await page.goto(new URL(target.path, baseUrl), { waitUntil: "networkidle", timeout: 15000 });
    await page.screenshot({ path: `${outputDir}/${target.name}.png`, fullPage: true });
    console.log("captured", target.name, page.url());
  } catch (error) {
    console.log("FAILED", target.name, error.message);
  }
}

await browser.close();
