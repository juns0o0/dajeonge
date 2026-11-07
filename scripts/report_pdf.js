// docs/결과보고서/*.html → .pdf (A4). 사용: node scripts/report_pdf.js
const { chromium } = require('playwright'); const path = require('path'); const fs = require('fs');
(async () => {
  const dir = path.join(__dirname, '..', 'docs', '결과보고서');
  const b = await chromium.launch(); const p = await b.newPage();
  for (const f of fs.readdirSync(dir).filter(n => n.endsWith('.html'))) {
    await p.goto('file://' + path.join(dir, f)); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
    await p.pdf({ path: path.join(dir, f.replace(/\.html$/, '.pdf')), format: 'A4', printBackground: true, preferCSSPageSize: true });
    console.log('pdf', f);
  }
  await b.close();
})();
