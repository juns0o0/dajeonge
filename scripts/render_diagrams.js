// scripts/diagrams/*.html → docs/diagrams/*.png (Playwright, 2x)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
(async () => {
  const src = path.join(__dirname, 'diagrams'), out = path.join(__dirname, '..', 'docs', 'diagrams');
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1320, height: 900 }, deviceScaleFactor: 2 });
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  for (const f of fs.readdirSync(src).filter(n => /^\d\d_.*\.html$/.test(n)).sort()) {
    await page.goto('file://' + path.join(src, f));
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(200);
    const name = f.replace(/\.html$/, '.png');
    const h = await page.evaluate(() => document.getElementById('canvas').getBoundingClientRect().bottom + 24);
    await page.setViewportSize({ width: await page.evaluate(() => document.getElementById('canvas').getBoundingClientRect().right + 32), height: Math.ceil(h) });
    await page.screenshot({ path: path.join(out, name), fullPage: false });
    console.log('rendered', name, errs.length ? 'ERR ' + errs.join(' | ') : '');
    errs.length = 0;
  }
  await browser.close();
})();
