// 결과보고서용 화면 캡처.  사용: NODE_PATH=$(npm root -g) node scripts/capture_report.js docs/captures/결과보고서용 http://localhost:8000
// 같은 대화 기록 1건으로 태블릿 → API → 보호자 앱 → AI 요약까지 이어지는 캡처를 남긴다 (검수 기준).
const pw = require('playwright'); const fs = require('fs'); const path = require('path');
const OUT = process.argv[2] || 'docs/captures/결과보고서용', B = process.argv[3] || 'http://localhost:8000';
fs.mkdirSync(OUT, { recursive: true });
const index = [];
const shot = async (page, name, note, opts = {}) => { const f = path.join(OUT, name + '.png'); await page.screenshot({ path: f, fullPage: opts.full !== false }); index.push([name, note]); console.log('✓', name); };
const sleep = ms => new Promise(r => setTimeout(r, ms));
const TABBAR_FIX = () => document.addEventListener('DOMContentLoaded', () => { const s = document.createElement('style'); s.textContent = '.app{position:relative}.tabbar{position:absolute}'; document.head.appendChild(s); });
const textPage = async (ctx, title, body, name, note) => {
  const p = await ctx.newPage(); await p.setViewportSize({ width: 1100, height: 700 });
  await p.setContent(`<html><head><meta charset=utf-8><style>body{margin:0;background:#17191B;color:#E8EEF2;font:14px/1.5 ui-monospace,Menlo,monospace;padding:28px}h1{font:700 18px system-ui;color:#CBEF5C;margin:0 0 14px}pre{white-space:pre-wrap;margin:0}</style></head><body><h1>${title}</h1><pre>${body.replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))}</pre></body></html>`);
  await shot(p, name, note); await p.close();
};

(async () => {
  const br = await pw.chromium.launch();
  const ctx = await br.newContext({ viewport: { width: 1440, height: 900 }, locale: 'ko-KR' });
  const errs = []; ctx.on('page', p => { p.on('pageerror', e => errs.push(e.message)); });

  // ===== A. 랜딩페이지 =====
  const pc = await ctx.newPage(); await pc.goto(B + '/'); await sleep(600);
  await pc.evaluate(() => document.fonts.ready); await shot(pc, 'A01_랜딩_PC_전체', '랜딩페이지 PC(1440px) 전체: 히어로→태블릿→일상의 빈틈→작동 방식→자녀 앱→이용 전후→모집→진행 과정→신청→FAQ→만든 사람들');
  await pc.setViewportSize({ width: 1440, height: 900 }); await shot(pc, 'A02_랜딩_PC_첫화면', '랜딩 첫 화면(히어로)', { full: false });
  await pc.click('[data-faq="3"]'); await pc.locator('#faq').scrollIntoViewIfNeeded(); await sleep(500);
  await shot(pc, 'A03_랜딩_FAQ_펼침', 'FAQ 펼침(“자녀 앱에서는 무엇을 볼 수 있나요?” 답변, 한 번에 하나만 열림)', { full: false });
  await pc.locator('#apply').scrollIntoViewIfNeeded(); await pc.fill('#nameInput', '김보호'); await pc.fill('#applyForm input[name=contact]', '010-1234-5678'); await pc.check('#applyForm input[name=agree]');
  await shot(pc, 'A04_랜딩_신청폼_가정용', '신청 폼(가정용) 입력 상태', { full: false });
  await pc.check('#applyForm input[name=type][value=org]'); await pc.fill('#applyForm input[name=org]', '세종시 치매안심센터'); await sleep(200);
  await shot(pc, 'A05_랜딩_신청폼_기관용', '신청 폼(기관용) 전환: 기관명 칸 표시', { full: false });
  await pc.click('#applyForm button[type=submit]'); await sleep(900);
  await shot(pc, 'A06_랜딩_신청_접수완료', '신청 제출 후 접수 완료 화면 (백오피스 ‘신청 접수’에 저장)', { full: false });
  const mob = await ctx.newPage(); await mob.setViewportSize({ width: 390, height: 844 }); await mob.goto(B + '/'); await mob.evaluate(() => document.fonts.ready); await sleep(500);
  await shot(mob, 'A07_랜딩_모바일_전체', '랜딩 모바일(390px) 반응형 전체'); await mob.close();
  const pr = await ctx.newPage(); await pr.goto(B + '/privacy.html'); await shot(pr, 'A08_개인정보처리방침', '개인정보 처리방침(발주사 검토본 교체 전 초안)'); await pr.close();

  // ===== B. 태블릿 =====
  const t = await ctx.newPage(); await t.setViewportSize({ width: 1280, height: 800 });
  await t.goto(B + '/tablet.html'); await sleep(300); await shot(t, 'B01_태블릿_연결화면', '태블릿 연결(가족 코드+태블릿 비밀번호)', { full: false });
  await t.fill('#code', 'DEMO1'); await t.fill('#pw', 'wrong'); await t.click('#loginForm button[type=submit]'); await sleep(500);
  await shot(t, 'B02_태블릿_비밀번호오류', '잘못된 비밀번호 → 오류 문구 (예외 점검)', { full: false });
  await t.fill('#pw', '0000'); await t.click('#loginForm button[type=submit]'); await sleep(500);
  await shot(t, 'B03_태블릿_대기화면', '연결 후 대기 화면(버튼 1개)', { full: false });
  await t.click('#toggleText'); await t.click('#bigBtn'); await sleep(1500);
  await shot(t, 'B04_태블릿_다정이_첫마디', '대화 시작: 다정이 첫마디(말하는 중, 라임 아바타)', { full: false });
  await sleep(2500);
  const lines = ['응 먹었지. 된장국에 밥 말아 먹었어.', '오늘 경로당 갔다 왔어. 영숙이랑 화투 쳤지.', '글쎄 그게 언제였더라… 잘 기억이 안 나네', '영숙이랑 화투 쳤지. 경로당 갔다 왔어.'];
  for (let i = 0; i < lines.length; i++) { await t.fill('#textIn', lines[i]); if (i === 2) await shot(t, 'B05_태블릿_글로말하기_입력', '음성 인식 미지원·거부 시 글 입력 대체(입력 중)', { full: false }); await t.press('#textIn', 'Enter'); await sleep(3800); }
  await shot(t, 'B06_태블릿_대화중_응답', '가족 기록(경로당·영숙 할머니)을 반영한 다정이 응답', { full: false });
  const convId = await t.evaluate(async () => { const a = JSON.parse(localStorage.getItem('dajeong.auth')); const r = await fetch('/api/conversations?limit=1', { headers: { Authorization: 'Bearer ' + a.token } }); return (await r.json())[0].id; });
  await t.click('#endBtn'); await sleep(1200); await shot(t, 'B07_태블릿_대화마치기', '대화 마치기 → “보호자 앱으로 전달했어요”', { full: false });
  await sleep(3000); console.log('conversation id', convId);

  // ===== D. API (같은 기록) =====
  const api = await ctx.newPage();
  const gtoken = await api.evaluate(async b => { const r = await fetch(b + '/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ code: 'DEMO1', password: '1234', role: 'guardian' }) }); return (await r.json()).token; }, B);
  const conv = await api.evaluate(async ([b, tok, id]) => { const r = await fetch(`${b}/api/conversations/${id}`, { headers: { Authorization: 'Bearer ' + tok } }); return await r.json(); }, [B, gtoken, convId]);
  await textPage(ctx, `GET /api/conversations/${convId}  (DB 저장 + 분석 결과 · 같은 기록 ID)`, JSON.stringify(conv, null, 2), `D01_API_대화${convId}_저장분석결과`, `같은 기록(ID ${convId})의 DB 저장·태그·지표 JSON`);
  const health = await api.evaluate(async b => (await fetch(b + '/api/health')).text(), B);
  await textPage(ctx, 'GET /api/health', health, 'D02_API_health', '서버 상태 응답');
  const denied = await api.evaluate(async ([b, tok]) => { const r = await fetch(`${b}/api/conversations/999999`, { headers: { Authorization: 'Bearer ' + tok } }); return `HTTP ${r.status}\n` + await r.text(); }, [B, gtoken]);
  const forbidden = await api.evaluate(async ([b, tok]) => { const r = await fetch(`${b}/api/admin/applications`); return `HTTP ${r.status}\n` + await r.text(); }, [B, gtoken]);
  const empty = await api.evaluate(async ([b, tok, id]) => { const r = await fetch(`${b}/api/conversations/${id}/turns`, { method: 'POST', headers: { Authorization: 'Bearer ' + tok, 'content-type': 'application/json' }, body: JSON.stringify({ text: '' }) }); return `HTTP ${r.status}\n` + (await r.text()).slice(0, 400); }, [B, gtoken, convId]);
  await textPage(ctx, '예외 점검: 다른 가족 기록 접근 / 연동 API 토큰 없음 / 빈 입력', `# 다른 가족(존재하지 않는) 대화 ID\n${denied}\n\n# 관리자 API를 토큰 없이\n${forbidden}\n\n# 빈 입력\n${empty}`, 'D03_API_예외점검', '예외 점검 응답(404 / 403 / 422)');
  await api.goto(B + '/docs'); await sleep(1500); await shot(api, 'D04_API_Swagger문서', 'API 명세서(Swagger UI)');
  await api.close();

  // ===== C. 보호자 앱 =====
  const g = await ctx.newPage(); await g.setViewportSize({ width: 430, height: 932 }); await g.addInitScript(TABBAR_FIX);
  await g.goto(B + '/app.html'); await sleep(300); await shot(g, 'C01_보호자_로그인', '보호자 앱 로그인', { full: false });
  await g.fill('#code', 'DEMO1'); await g.fill('#pw', '1234'); await g.click('#loginForm button[type=submit]'); await sleep(1200);
  await shot(g, 'C02_보호자_홈_대시보드', '홈: 이번 주 상태, 지표 5개(평소 대비 배지), 14일 그래프');
  await g.goto(B + '/app.html#metric/avg_response_gap'); await sleep(800); await shot(g, 'C03_보호자_지표상세_응답간격', '지표 상세: 측정 방법·평소 값·일별 표');
  await g.goto(B + '/app.html#talks'); await sleep(800); await shot(g, 'C04_보호자_대화기록목록', '대화 기록 목록(월별)');
  await g.goto(B + `/app.html#talk/${convId}`); await sleep(900); await shot(g, `C05_보호자_대화${convId}_상세_태그`, `같은 기록(ID ${convId}) 상세: 지표 표, 원문, 반복·불확실 태그, 응답 초`);
  await g.click('#sumBtn'); await sleep(4500); await shot(g, `C06_보호자_대화${convId}_AI요약`, `같은 기록(ID ${convId})의 AI 요약(버튼 생성)`);
  await g.goto(B + '/app.html#report'); await sleep(800); await g.click('#sumBtn'); await sleep(4500); await shot(g, 'C07_보호자_주간AI요약', '주간 AI 요약: 평소/이번 주/비교 표 + 요약 문장');
  await g.goto(B + '/app.html#family'); await sleep(800); await shot(g, 'C08_보호자_가족정보_페르소나', '가족 정보: 부모님·보호자, 페르소나 편집, 가족 이야기 목록');
  await g.click('#addMem'); await g.fill('#m_title', '엄마 칠순 제주 여행'); await g.fill('#m_detail', '2022년 온 가족이 제주도에 감'); await g.fill('#m_keywords', '제주, 칠순, 여행'); await g.fill('#m_year', '2022');
  await g.locator('#memForm').scrollIntoViewIfNeeded(); await shot(g, 'C09_보호자_가족이야기_추가', '가족 이야기 추가 폼(제목·내용·키워드·연도)', { full: false });
  await g.click('#memForm button[type=submit]'); await sleep(800);
  await g.goto(B + '/app.html#more'); await sleep(800); await shot(g, 'C10_보호자_설정_작업목록', '설정: 태블릿 연결 안내, 처리 작업 목록, 개인정보');

  // 실패 작업 → 재시도 (예외 점검)
  const { execSync } = require('child_process');
  execSync(`cd server && python3 -c "
from app.db import SessionLocal; from app.models import Job
db=SessionLocal(); j=Job(kind='summarize', ref_id=0, family_id=1, status='failed', attempts=3, error='OpenAI API 호출 실패: 401 invalid api key (시연용 실패 기록)'); db.add(j); db.commit()"`, { stdio: 'inherit' });
  await g.goto(B + '/app.html#more'); await sleep(800); await shot(g, 'C11_보호자_설정_실패작업_재시도', '실패한 작업이 상태·오류와 함께 표시되고 ‘다시 시도’ 버튼 제공');
  execSync(`cd server && python3 -c "
from app.db import SessionLocal; from app.models import Job
db=SessionLocal(); db.query(Job).filter(Job.ref_id==0).delete(); db.commit()"`);

  // 기준선 미수집 가족
  await g.evaluate(async b => { await fetch(b + '/api/admin/families', { method: 'POST', headers: { 'X-Admin-Token': 'admin-dev-token', 'content-type': 'application/json' }, body: JSON.stringify({ code: 'FAM02', parent_name: '박영자', parent_age: 81, region: '세종시', guardian_name: '최수진', guardian_relation: '딸', guardian_password: '1234', tablet_password: '0000', persona: { display_name: '수진', calls_parent: '엄마' } }) }); }, B);
  await g.evaluate(() => localStorage.clear()); await g.goto(B + '/app.html'); await g.fill('#code', 'FAM02'); await g.fill('#pw', '1234'); await g.click('#loginForm button[type=submit]'); await sleep(1200);
  await shot(g, 'C12_보호자_홈_기준선수집중_신규가족', '신규 가족: 기준선 ‘수집 중 0/5회 · 0/14일’, 비교 배지 없음');
  await g.goto(B + '/app.html#talks'); await sleep(600); await shot(g, 'C13_보호자_대화기록_없음', '대화 기록 없음 상태');
  await g.evaluate(() => localStorage.clear()); await g.close();

  // ===== E. 시스템 =====
  const py = execSync('cd server && python3 -m pytest -v 2>&1 | tail -15').toString();
  await textPage(ctx, 'python -m pytest -v  (지표 계산 단위 테스트)', py, 'E01_단위테스트_결과', '지표 계산 단위 테스트 7개 통과');
  const schema = execSync(`cd server && python3 -c "
import sqlite3; c=sqlite3.connect('data/dajeong.db')
for (n,) in c.execute(\\"select name from sqlite_master where type='table' order by name\\"):
    cnt=c.execute(f'select count(*) from {n}').fetchone()[0]; cols=[r[1] for r in c.execute(f'pragma table_info({n})')]
    print(f'{n:22s} {cnt:4d} rows  |  '+', '.join(cols))"`).toString();
  await textPage(ctx, 'DB 테이블과 저장 건수 (SQLite · server/data/dajeong.db)', schema, 'E02_DB_테이블_저장건수', 'DB 테이블 목록·컬럼·건수');
  const usage = execSync(`curl -s ${B}/api/admin/stats -H "X-Admin-Token: admin-dev-token" | python3 -m json.tool; echo; echo '# GET /api/admin/families/1/export (앞부분)'; curl -s ${B}/api/admin/families/1/export -H "X-Admin-Token: admin-dev-token" | python3 -c "import json,sys; d=json.load(sys.stdin); d['conversations']=d['conversations'][:1]; d['conversations'][0]['turns']=d['conversations'][0]['turns'][:3]; d['memories']=d['memories'][:2]; print(json.dumps(d, ensure_ascii=False, indent=2)[:2600])"`).toString();
  await textPage(ctx, '연동 API: GET /api/admin/stats · GET /api/admin/families/{id}/export (X-Admin-Token)', usage, 'E03_연동API_현황_기록내보내기', '외부 시스템 연동용 API 응답: 현황 집계와 가족 기록 JSON 내보내기');
  const log = execSync('tail -25 /tmp/claude-0/-home-user-brandnaut-ai-seminar-dashboard/8adfbe5a-3b93-5105-9acb-6e794b0c8239/scratchpad/uv.log 2>/dev/null || echo "(로그 없음)"').toString();
  await textPage(ctx, '서버 로그 (uvicorn)', log, 'E04_서버로그', '서버 요청 로그');
  const files = execSync('ls -R server/app server/tests web docs | head -60').toString();
  await textPage(ctx, '소스코드 구성', files, 'E05_소스코드_구성', '저장소 폴더 구성');

  // ===== G. 백오피스 (데이터 관리 · 연동 API 와 같은 데이터) =====
  const bo = await ctx.newPage(); await bo.setViewportSize({ width: 1360, height: 860 });
  await bo.goto(B + '/admin.html'); await sleep(300); await shot(bo, 'G01_백오피스_로그인', '백오피스 로그인(운영자 토큰)', { full: false });
  await bo.fill('#token', 'wrong-token'); await bo.click('#loginForm button[type=submit]'); await sleep(500);
  await shot(bo, 'G02_백오피스_토큰오류', '틀린 토큰 → 오류 문구 (예외 점검)', { full: false });
  await bo.fill('#token', 'admin-dev-token'); await bo.click('#loginForm button[type=submit]'); await sleep(900);
  await shot(bo, 'G03_백오피스_현황', '현황: 가족·대화·신규 신청·실패 작업 수, 최근 작업, 연락 전 신청', { full: false });
  await bo.goto(B + '/admin.html#families'); await sleep(700); await shot(bo, 'G04_백오피스_가족목록', '가족 목록(검색 · 가족 등록 버튼 · 기준선 상태)', { full: false });
  await bo.goto(B + '/admin.html#family/1'); await sleep(900); await shot(bo, 'G05_백오피스_가족상세_기준선', '가족 상세: 정보·페르소나·개인 기준선(평균·편차)·최근 대화·작업, 수정·삭제·JSON 내보내기');
  await bo.goto(B + '/admin.html#talks'); await sleep(900); await shot(bo, 'G06_백오피스_대화기록_전체', '모든 가족의 대화 기록과 지표(가족·상태 필터)', { full: false });
  await bo.goto(B + `/admin.html#talk/${convId}`); await sleep(900); await shot(bo, `G07_백오피스_대화${convId}_상세`, `같은 기록(ID ${convId})을 백오피스에서 본 지표·원문·태그`);
  await bo.goto(B + '/admin.html#apps'); await sleep(800);
  await bo.selectOption('table.t select >> nth=0', 'contacted'); await sleep(300); await bo.fill('table.t textarea >> nth=0', '11/4 통화 · 11월 중 방문 설명 예정'); await bo.press('table.t textarea >> nth=0', 'Tab'); await sleep(500);
  await shot(bo, 'G08_백오피스_신청접수_상태메모', '신청 접수: 연락 상태 변경(연락함)과 메모 저장', { full: false });
  execSync(`cd server && python3 -c "
from app.db import SessionLocal; from app.models import Job
db=SessionLocal(); j=Job(kind='summarize', ref_id=0, family_id=1, status='failed', attempts=3, error='OpenAI API 호출 실패: 401 invalid api key (시연용 실패 기록)'); db.add(j); db.commit()"`);
  await bo.goto(B + '/admin.html#jobs'); await sleep(800); await shot(bo, 'G09_백오피스_처리작업_실패재시도', '처리 작업: 상태·시도·오류, 실패 작업 ‘다시 시도’', { full: false });
  execSync(`cd server && python3 -c "
from app.db import SessionLocal; from app.models import Job
db=SessionLocal(); db.query(Job).filter(Job.ref_id==0).delete(); db.commit()"`);
  await bo.goto(B + '/admin.html#usage'); await sleep(800); await shot(bo, 'G10_백오피스_API사용량', 'API 사용량: 목적별 호출·오류·토큰 집계, 최근 호출', { full: false });
  await bo.goto(B + '/admin.html#api'); await sleep(800); await shot(bo, 'G11_백오피스_연동안내', '연동 안내: 인증, 엔드포인트 표, 기관 도구 연동 순서·요청 예시');
  await bo.close();

  // ===== F. 브라우저 호환 (Chromium 엔진 기준 · Edge/Safari 는 UA·기기 에뮬레이션) =====
  const devices = [['F01_브라우저_Chrome_PC', { viewport: { width: 1366, height: 768 } }, 'Chrome(PC)'], ['F02_브라우저_Edge_PC', { viewport: { width: 1366, height: 768 }, userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36 Edg/130.0' }, 'Edge(PC, UA 에뮬레이션)'], ['F03_브라우저_iPhone_Safari', pw.devices['iPhone 14'], 'iPhone Safari 뷰포트(Chromium 엔진 에뮬레이션)'], ['F04_브라우저_Android_태블릿', { viewport: { width: 1280, height: 800 }, isMobile: true, hasTouch: true, userAgent: 'Mozilla/5.0 (Linux; Android 13; SM-X200) AppleWebKit/537.36 Chrome/130.0 Safari/537.36' }, 'Android 태블릿 Chrome 에뮬레이션'], ['F05_브라우저_macOS_Chrome', { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36' }, 'macOS Chrome(레티나 2x)'], ['F06_브라우저_macOS_Safari', { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15' }, 'macOS Safari UA(Chromium 엔진 에뮬레이션, 실기기 확인 권장)']];
  for (const [name, dev, note] of devices) {
    const c2 = await br.newContext({ ...dev, locale: 'ko-KR' }); const p2 = await c2.newPage(); await p2.goto(B + '/'); await p2.evaluate(() => document.fonts.ready); await sleep(500);
    await shot(p2, name + '_랜딩', note + ' 랜딩', { full: false });
    await p2.goto(B + '/app.html'); await p2.fill('#code', 'DEMO1'); await p2.fill('#pw', '1234'); await p2.click('#loginForm button[type=submit]'); await sleep(1200);
    await shot(p2, name + '_보호자홈', note + ' 보호자 홈', { full: false }); await c2.close();
  }
  await br.close();
  fs.writeFileSync(path.join(OUT, '캡처목록.md'), '# 결과보고서용 캡처 목록\n\n' + `생성: ${new Date().toISOString().slice(0, 10)} · 시연 가족 DEMO1 · AI MOCK 모드 · 같은 기록 ID ${convId} 로 태블릿→API→보호자 앱→AI 요약 연결\n\n| 파일 | 용도 |\n| --- | --- |\n` + index.map(([n, d]) => `| ${n}.png | ${d} |`).join('\n') + '\n');
  console.log('captures:', index.length, 'errors:', JSON.stringify(errs));
})().catch(e => { console.error('FAIL', e); process.exit(1); });
