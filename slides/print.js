// node print.js DECK.html DECK.pdf: prints a deck, one slide per 1920×1080 page, with Chromium (Playwright).
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
(async () => {
  const [inp, out] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + require('path').resolve(inp), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({ path: out, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: true });
  await browser.close();
})();
