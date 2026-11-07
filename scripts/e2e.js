// 헤드리스 브라우저 점검 + 캡처.  사용: NODE_PATH=$(npm root -g) node scripts/e2e.js docs/captures http://localhost:8000  (playwright 필요)
const { chromium } = require('playwright');
const OUT = process.argv[2] || "docs/captures", B = process.argv[3] || "http://localhost:8000";
(async () => {
  const br = await chromium.launch(); const errs = [];
  const ctx = await br.newContext({ viewport: { width: 1280, height: 900 }, locale: 'ko-KR' });
  const p = await ctx.newPage(); p.on('pageerror', e => errs.push('PAGE ' + e.message)); p.on('console', m => m.type() === 'error' && errs.push('CONSOLE ' + m.text()));
  // 1 landing
  await p.goto(B + '/'); await p.waitForTimeout(500);
  await p.screenshot({ path: OUT + '/01_랜딩페이지.png', fullPage: true });
  await p.check('#applyForm input[name=type][value=org]'); await p.fill('#applyForm input[name=org]', '세종시 치매안심센터'); await p.fill('#nameInput', '테스트 담당자'); await p.fill('#applyForm input[name=contact]', '044-000-0000'); await p.check('#applyForm input[name=agree]');
  await p.click('#applyForm button[type=submit]'); await p.waitForTimeout(800); console.log('apply:', (await p.isVisible('#applyDone')) ? '접수 완료 화면 표시' : 'FAILED');
  // 2 tablet (text mode)
  const t = await ctx.newPage({ viewport: { width: 1024, height: 768 } }); t.on('pageerror', e => errs.push('TABLET ' + e.message));
  await t.setViewportSize({ width: 1024, height: 768 });
  await t.goto(B + '/tablet.html'); await t.fill('#code', 'DEMO1'); await t.fill('#pw', '0000'); await t.click('#loginForm button[type=submit]'); await t.waitForTimeout(500);
  const hasSR = await t.evaluate(() => !!(window.SpeechRecognition || window.webkitSpeechRecognition)); console.log('SR available:', hasSR);
  if (hasSR) await t.click('#toggleText');
  await t.click('#bigBtn'); await t.waitForTimeout(3500);
  await t.screenshot({ path: OUT + '/02_태블릿_대화시작.png' });
  for (const s of ['응 먹었지. 된장국에 밥 말아 먹었어.', '오늘 경로당 갔다 왔어. 영숙이랑 화투 쳤지.', '글쎄 그게 언제였더라… 잘 기억이 안 나네']) {
    await t.fill('#textIn', s); await t.press('#textIn', 'Enter'); await t.waitForTimeout(3500);
  }
  await t.screenshot({ path: OUT + '/03_태블릿_대화중.png' });
  await t.click('#endBtn'); await t.waitForTimeout(3000); console.log('tablet state:', await t.textContent('#stateT'));
  // 3 guardian app
  const g = await ctx.newPage(); g.on('pageerror', e => errs.push('APP ' + e.message)); g.on('console', m => m.type() === 'error' && errs.push('APPCONSOLE ' + m.text()));
  await g.setViewportSize({ width: 430, height: 932 }); await g.addInitScript(() => document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = '.app{position:relative}.tabbar{position:absolute}'; document.head.appendChild(s); }));
  await g.goto(B + '/app.html'); await g.fill('#code', 'DEMO1'); await g.fill('#pw', '1234'); await g.click('#loginForm button[type=submit]'); await g.waitForTimeout(1200);
  await g.screenshot({ path: OUT + '/04_보호자_홈.png', fullPage: true });
  await g.goto(B + '/app.html#talks'); await g.waitForTimeout(800); await g.screenshot({ path: OUT + '/05_보호자_대화기록.png', fullPage: true });
  await g.click('.list a'); await g.waitForTimeout(800);
  await g.click('#sumBtn'); await g.waitForTimeout(4000);
  await g.screenshot({ path: OUT + '/06_보호자_대화상세_AI요약.png', fullPage: true });
  console.log('conv summary:', (await g.textContent('#sumBox')).slice(0, 80));
  await g.goto(B + '/app.html#report'); await g.waitForTimeout(800); await g.click('#sumBtn'); await g.waitForTimeout(4000);
  await g.screenshot({ path: OUT + '/07_보호자_주간요약.png', fullPage: true });
  console.log('weekly summary:', (await g.textContent('#sumBox')).slice(0, 80));
  await g.goto(B + '/app.html#family'); await g.waitForTimeout(800); await g.screenshot({ path: OUT + '/08_보호자_가족정보.png', fullPage: true });
  await g.click('#addMem'); await g.fill('#m_title', '엄마 칠순 제주 여행'); await g.fill('#m_detail', '2022년 온 가족 제주도'); await g.fill('#m_keywords', '제주, 칠순'); await g.fill('#m_year', '2022'); await g.click('#memForm button[type=submit]'); await g.waitForTimeout(800);
  console.log('memories after add:', await g.$$eval('#memList > div', x => x.length));
  await g.goto(B + '/app.html#metric/avg_response_gap'); await g.waitForTimeout(800); await g.screenshot({ path: OUT + '/09_보호자_지표상세.png', fullPage: true });
  await g.goto(B + '/app.html#more'); await g.waitForTimeout(800); await g.screenshot({ path: OUT + '/10_보호자_설정_작업.png', fullPage: true });
  console.log('errors:', JSON.stringify(errs, null, 1)); await br.close();
})().catch(e => { console.error('E2E FAIL', e); process.exit(1); });
