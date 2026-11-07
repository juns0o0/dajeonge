/* 백오피스 (해시 라우팅). 화면: 현황 / 가족 / 가족 상세 / 대화 기록 / 대화 상세 / 신청 접수 / 처리 작업 / API 사용량 / 연동 안내
   모든 호출은 /api/admin/* 에 X-Admin-Token 헤더를 붙인다. 토큰은 sessionStorage 에만 둔다(탭을 닫으면 지워짐). */
const $ = s => document.querySelector(s), esc = API.esc;
const KEY = "dajeong.admin";
const token = () => { try { return sessionStorage.getItem(KEY) || ""; } catch { return ""; } };
const setToken = t => { try { t ? sessionStorage.setItem(KEY, t) : sessionStorage.removeItem(KEY); } catch {} };
const H = () => ({ headers: { "X-Admin-Token": token() } });
const A = {
  get: p => API.get("/admin" + p, H()),
  put: (p, b) => API.put("/admin" + p, b, H()),
  post: (p, b) => API.post("/admin" + p, b, H()),
  del: p => API.del("/admin" + p, H()),
};
const d = iso => iso ? API.fmtDate(iso, { year: "2-digit", month: "numeric", day: "numeric", hour: "numeric", minute: "2-digit" }) : "–";
const st = s => `<span class="st ${esc(s)}">${esc(STATUS[s] || s)}</span>`;
const STATUS = { open: "진행 중", finished: "종료", analyzed: "분석 완료", failed: "실패", queued: "대기", running: "처리 중", done: "완료",
  new: "신규", contacted: "연락함", ready: "고정", collecting: "수집 중", pending: "대기" };
const MLABEL = { avg_utterance_len: "발화 길이 평균(자)", repeat_rate: "동일 표현 반복률", uncertain_rate: "불확실 표현 비율", avg_response_gap: "응답 간격 평균(초)", participation: "대화 참여" };
const pct = v => v == null ? "–" : Math.round(v * 100) + "%";
const n1 = v => v == null ? "–" : (+v).toFixed(1);

/* ---------- 로그인 ---------- */
$("#mark").innerHTML = ILLUS.mark; $("#mark2").innerHTML = ILLUS.avatar;
async function enter() {
  try { await A.get("/stats"); } catch (e) { setToken(""); $("#loginErr").textContent = e.status === 403 ? "토큰이 맞지 않습니다." : e.message; return; }
  $("#login").hidden = true; $("#app").hidden = false; route();
}
if (token()) enter();
$("#loginForm").onsubmit = e => { e.preventDefault(); $("#loginErr").textContent = ""; setToken($("#token").value.trim()); enter(); };
$("#logout").onclick = e => { e.preventDefault(); setToken(""); location.hash = ""; location.reload(); };

/* ---------- 라우팅 ---------- */
window.addEventListener("hashchange", route);
async function route() {
  const [name, arg] = (location.hash.replace("#", "") || "home").split("/");
  const tab = { family: "families", talk: "talks" }[name] || name;
  document.querySelectorAll("#nav a").forEach(a => a.classList.toggle("on", a.dataset.t === tab));
  const fn = SCREENS[name] || SCREENS.home;
  $("#body").innerHTML = '<p class="empty">불러오는 중…</p>';
  try { await fn(arg); } catch (err) {
    if (err.status === 403) { setToken(""); location.reload(); return; }
    $("#body").innerHTML = `<p class="err">${esc(err.message)}</p>`;
  }
  window.scrollTo(0, 0);
}
function head(title, sub, action = "") { $("#head").innerHTML = `<div><h1>${esc(title)}</h1>${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</div><div>${action}</div>`; }
const SCREENS = {};

/* ---------- 현황 ---------- */
SCREENS.home = async () => {
  const s = await A.get("/stats");
  head("현황", `서버 시각 ${d(s.server_time)} · ${s.mock ? "AI 연동: MOCK (키 없음)" : "AI 연동: OpenAI"}`);
  const stat = (k, v, sub = "", warn = false) => `<div class="stat ${warn ? "warn" : ""}"><div class="k">${k}</div><div class="v">${v}${sub ? `<small>${sub}</small>` : ""}</div></div>`;
  const [jobs, apps] = await Promise.all([A.get("/jobs?limit=8"), A.get("/applications?status=new")]);
  $("#body").innerHTML = `
    <div class="stats">
      ${stat("등록 가족", s.families, `기준선 고정 ${s.baselines_fixed}`)}
      ${stat("대화 기록", s.conversations, `최근 7일 ${s.conversations_7d}`)}
      ${stat("신규 신청", s.applications_new, "", s.applications_new > 0)}
      ${stat("실패 작업", s.jobs_failed, `대기 ${s.jobs_queued}`, s.jobs_failed > 0)}
    </div>
    <div class="grid2">
      <div class="panel"><h2>최근 처리 작업</h2>${jobsTable(jobs, true)}</div>
      <div class="panel"><h2>연락 전 신청 (${apps.length})</h2>${apps.length ? `<table class="t"><tr><th>구분</th><th>이름</th><th>연락처</th><th>접수</th></tr>${apps.slice(0, 8).map(a => `<tr class="link" onclick="location.hash='#apps'"><td>${a.kind === "org" ? "기관" : "가정"}</td><td>${esc(a.name)}${a.org_name ? ` · ${esc(a.org_name)}` : ""}</td><td>${esc(a.phone)}</td><td>${d(a.created_at)}</td></tr>`).join("")}</table>` : '<p class="empty">연락 전 신청이 없습니다.</p>'}</div>
    </div>
    <div class="panel"><h2>외부 API (최근 7일)</h2><div class="kv"><b>호출</b><span>${s.api_calls_7d}회 · 오류 ${s.api_errors_7d}회</span><b>데이터 보관</b><span>음성 파일은 가족별 보관 일수(기본 30일) 뒤 삭제 배치로 정리 · 가족 삭제 시 대화·지표·요약을 함께 삭제</span></div></div>`;
};

/* ---------- 가족 ---------- */
SCREENS.families = async () => {
  head("가족", "가족 코드 단위로 모든 기록이 격리됩니다. 행을 누르면 상세로 갑니다.", `<button class="btn sm dark" onclick="newFamily()">+ 가족 등록</button>`);
  const rows = await A.get("/families");
  const render = list => `<table class="t"><tr><th>코드</th><th>부모님</th><th>보호자</th><th>지역</th><th class="r">대화</th><th class="r">가족 이야기</th><th>기준선</th><th>마지막 대화</th></tr>
    ${list.map(f => `<tr class="link" onclick="location.hash='#family/${f.id}'"><td><b>${esc(f.code)}</b></td><td>${esc(f.parent_name)}${f.parent_age ? ` (${f.parent_age})` : ""}</td><td>${esc(f.guardian_name)} · ${esc(f.guardian_relation)}</td><td>${esc(f.region || "–")}</td><td class="r">${f.conversations}</td><td class="r">${f.memories}</td><td>${f.baseline_fixed_at ? st("ready") : st("collecting")}</td><td>${d(f.last_conversation_at)}</td></tr>`).join("")}</table>`;
  $("#body").innerHTML = `<div class="panel"><div class="toolbar"><input id="q" placeholder="코드 · 이름 검색" style="width:260px"><span class="faint" id="cnt">${rows.length}가족</span></div><div id="list">${rows.length ? render(rows) : '<p class="empty">등록된 가족이 없습니다.</p>'}</div></div>`;
  $("#q").oninput = e => { const q = e.target.value.toLowerCase(); const l = rows.filter(f => [f.code, f.parent_name, f.guardian_name].join(" ").toLowerCase().includes(q)); $("#list").innerHTML = render(l); $("#cnt").textContent = l.length + "가족"; };
};
window.newFamily = async () => {
  const code = prompt("가족 코드 (영문·숫자 5자 권장)"); if (!code) return;
  const parent_name = prompt("부모님 성함"); if (!parent_name) return;
  const guardian_name = prompt("보호자 성함"); if (!guardian_name) return;
  const guardian_password = prompt("보호자 비밀번호 (4자 이상)"); const tablet_password = prompt("태블릿 비밀번호 (4자 이상)");
  if (!guardian_password || !tablet_password) return;
  try { const f = await A.post("/families", { code, parent_name, guardian_name, guardian_password, tablet_password }); API.toast("등록했습니다."); location.hash = "#family/" + f.id; }
  catch (e) { alert(e.message); }
};

SCREENS.family = async id => {
  const f = await A.get("/families/" + id);
  head(`${f.code} · ${f.parent_name}`, `등록 ${d(f.created_at)} · 보호자 ${f.guardian_name}(${f.guardian_relation})`,
    `<button class="btn sm" onclick="exportFamily(${f.id})">JSON 내보내기</button> <button class="btn sm" onclick="editFamily(${f.id})">정보 수정</button> <button class="btn sm" style="color:var(--notable)" onclick="deleteFamily(${f.id},'${esc(f.code)}')">삭제</button>`);
  const b = f.baseline, p = f.persona;
  const bl = b.status === "ready"
    ? `<div class="kv"><b>상태</b><span>${st("ready")} ${d(b.fixed_at)} · 유효 대화 ${b.n_conversations}회로 고정</span>${Object.entries(b.values || {}).map(([k, v]) => `<b>${esc(MLABEL[k] || k)}</b><span>평균 ${n1(v.mean)} · 편차 ${n1(v.sd)} (n=${v.n})</span>`).join("")}</div>`
    : `<div class="kv"><b>상태</b><span>${st("collecting")} 유효 대화 ${b.valid_conversations}/${b.need_conversations}회 · ${b.days}/${b.need_days}일</span></div>`;
  $("#body").innerHTML = `
    <div class="grid2">
      <div class="panel"><h2>가족 정보</h2><div class="kv">
        <b>부모님</b><span>${esc(f.parent_name)} ${f.parent_age ? `· ${f.parent_age}세` : ""} ${f.region ? `· ${esc(f.region)}` : ""}</span>
        <b>보호자</b><span>${esc(f.guardian_name)} · ${esc(f.guardian_relation)}</span>
        <b>음성 보관</b><span>${f.keep_audio_days}일</span>
        <b>페르소나</b><span>${p ? `${esc(p.display_name)} · 부모님 호칭 “${esc(p.calls_parent)}” · ${esc(p.formality)}` : '<span class="faint">미등록 (보호자 앱에서 등록)</span>'}</span>
        <b>가족 이야기</b><span>${f.memories_list.length}건 ${f.memories_list.slice(0, 3).map(m => `<span class="chip">${esc(m.title)}</span>`).join(" ")}</span>
      </div></div>
      <div class="panel"><h2>개인 기준선</h2>${bl}</div>
    </div>
    <div class="panel"><h2>대화 기록 (최근 30)</h2>${convTable(f.conversations_list)}</div>
    <div class="panel"><h2>처리 작업 (최근 20)</h2>${jobsTable(f.jobs)}</div>`;
};
window.exportFamily = async id => { const j = await A.get(`/families/${id}/export`); const blob = new Blob([JSON.stringify(j, null, 2)], { type: "application/json" }); const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = `dajeong_${j.family.code}_${j.exported_at.slice(0, 10)}.json`; a.click(); };
window.editFamily = async id => {
  const f = await A.get("/families/" + id);
  const parent_name = prompt("부모님 성함", f.parent_name); if (parent_name == null) return;
  const region = prompt("지역", f.region || ""); const keep = prompt("음성 보관 일수", f.keep_audio_days);
  const gp = prompt("보호자 비밀번호 재설정 (비우면 유지)", ""); const tp = prompt("태블릿 비밀번호 재설정 (비우면 유지)", "");
  const body = { parent_name, region: region || null, keep_audio_days: +keep }; if (gp) body.guardian_password = gp; if (tp) body.tablet_password = tp;
  try { await A.put("/families/" + id, body); API.toast("저장했습니다."); route(); } catch (e) { alert(e.message); }
};
window.deleteFamily = async (id, code) => {
  if (prompt(`가족 ${code} 의 대화·지표·요약·음성 파일을 모두 삭제합니다. 확인하려면 코드를 입력하세요.`) !== code) return;
  await A.del("/families/" + id); API.toast("삭제했습니다."); location.hash = "#families";
};

/* ---------- 대화 ---------- */
function convTable(list, withFamily = false) {
  if (!list.length) return '<p class="empty">대화가 없습니다.</p>';
  return `<table class="t"><tr>${withFamily ? "<th>가족</th>" : ""}<th>시작</th><th>상태</th><th>입력</th><th class="r">부모 발화</th><th class="r">발화 길이</th><th class="r">반복</th><th class="r">불확실</th><th class="r">응답 간격</th><th class="r">참여</th><th class="r">길이</th><th>유효</th></tr>
    ${list.map(c => { const m = c.metric || {}; return `<tr class="link" onclick="location.hash='#talk/${c.id}'">${withFamily ? `<td><b>${esc(c.family_code)}</b></td>` : ""}<td>${d(c.started_at)}</td><td>${st(c.status)}</td><td>${esc(c.source)}</td><td class="r">${c.parent_turns}</td><td class="r">${m.avg_utterance_len == null ? "–" : Math.round(m.avg_utterance_len) + "자"}</td><td class="r">${pct(m.repeat_rate)}</td><td class="r">${pct(m.uncertain_rate)}</td><td class="r">${m.avg_response_gap == null ? "–" : n1(m.avg_response_gap) + "초"}</td><td class="r">${pct(m.participation)}</td><td class="r">${m.duration_sec == null ? "–" : Math.round(m.duration_sec / 60) + "분"}</td><td>${c.metric ? (m.valid ? "유효" : '<span class="faint">짧음</span>') : "–"}</td></tr>`; }).join("")}</table>`;
}
SCREENS.talks = async () => {
  head("대화 기록", "모든 가족의 대화. 지표는 분석 작업이 끝난 뒤 채워집니다.");
  const fams = await A.get("/families");
  const load = async () => { const fid = $("#fid").value, s = $("#status").value; const q = []; if (fid) q.push("family_id=" + fid); if (s) q.push("status=" + s); q.push("limit=100"); $("#list").innerHTML = convTable(await A.get("/conversations?" + q.join("&")), true); };
  $("#body").innerHTML = `<div class="panel"><div class="toolbar"><select id="fid"><option value="">모든 가족</option>${fams.map(f => `<option value="${f.id}">${esc(f.code)} · ${esc(f.parent_name)}</option>`).join("")}</select>
    <select id="status"><option value="">모든 상태</option><option value="open">진행 중</option><option value="finished">종료(분석 대기)</option><option value="analyzed">분석 완료</option><option value="failed">실패</option></select></div><div id="list"></div></div>`;
  $("#fid").onchange = load; $("#status").onchange = load; await load();
};
SCREENS.talk = async id => {
  const c = await A.get("/conversations/" + id), m = c.metric;
  head(`대화 #${c.id} · ${c.family_code}`, `${d(c.started_at)} ~ ${c.ended_at ? d(c.ended_at) : "진행 중"} · ${STATUS[c.status] || c.status} · 입력 ${c.source}`, `<a class="btn sm" href="#talks">← 목록</a>`);
  $("#body").innerHTML = `
    ${c.error ? `<p class="err">오류: ${esc(c.error)}</p>` : ""}
    <div class="grid2">
      <div class="panel"><h2>지표</h2>${m ? `<table class="t"><tr><th>항목</th><th class="r">값</th></tr>
        <tr><td>부모 발화 수</td><td class="r">${m.parent_turns}</td></tr><tr><td>발화 길이 평균</td><td class="r">${Math.round(m.avg_utterance_len)}자</td></tr>
        <tr><td>동일 표현 반복률</td><td class="r">${pct(m.repeat_rate)}</td></tr><tr><td>불확실 표현 비율</td><td class="r">${pct(m.uncertain_rate)}</td></tr>
        <tr><td>응답 간격 평균</td><td class="r">${n1(m.avg_response_gap)}초</td></tr><tr><td>대화 참여</td><td class="r">${pct(m.participation)}</td></tr>
        <tr><td>대화 시간</td><td class="r">${Math.round(m.duration_sec / 60)}분</td></tr><tr><td>기준선 계산 포함</td><td class="r">${m.valid ? "예 (유효)" : "아니오 (발화 3회 미만)"}</td></tr></table>` : '<p class="empty">아직 분석되지 않았습니다.</p>'}</div>
      <div class="panel"><h2>기록 정보</h2><div class="kv"><b>conversation_id</b><span>${c.id}</span><b>family_id</b><span>${c.family_id} (${esc(c.family_code)})</span><b>발화 수</b><span>${c.turn_count} (부모 ${c.parent_turns})</span><b>계산 시각</b><span>${m ? d(m.computed_at) : "–"}</span></div>
        <p class="note" style="margin-top:12px">원문은 보호자 앱과 같은 기록입니다. 태그 <span class="tag repeat">반복</span><span class="tag uncertain">불확실</span>은 분석 작업이 붙인 것입니다.</p></div>
    </div>
    <div class="panel turns"><h2>원문</h2>${c.turns.map(t => `<div class="say ${t.speaker}"><div class="who">${t.speaker === "parent" ? "부모님" : "다정이"} · ${d(t.started_at)}${t.input_mode ? ` · ${esc(t.input_mode)}` : ""}${t.response_gap_sec != null ? ` · 간격 ${n1(t.response_gap_sec)}초` : ""}</div>${(t.tags || []).map(g => `<span class="tag ${g}">${g === "repeat" ? "반복" : "불확실"}</span>`).join("")}${esc(t.text)}</div>`).join("")}</div>`;
};

/* ---------- 신청 ---------- */
SCREENS.apps = async () => {
  head("신청 접수", "랜딩페이지 신청 폼으로 들어온 내역. 연락 상태와 메모를 남깁니다.");
  const load = async () => {
    const s = $("#status").value; const list = await A.get("/applications" + (s ? "?status=" + s : ""));
    $("#list").innerHTML = list.length ? `<table class="t"><tr><th>접수</th><th>구분</th><th>이름 · 기관</th><th>연락처</th><th>지역</th><th>문의 내용</th><th>상태</th><th>메모</th></tr>
      ${list.map(a => `<tr><td>${d(a.created_at)}</td><td>${a.kind === "org" ? "기관" : "가정"}</td><td><b>${esc(a.name)}</b>${a.org_name ? `<br>${esc(a.org_name)}` : ""}</td><td>${esc(a.phone)}${a.email ? `<br><span class="faint">${esc(a.email)}</span>` : ""}</td><td>${esc(a.region || "–")}</td><td style="max-width:260px">${esc(a.message || "–")}</td>
        <td><select onchange="setApp(${a.id},{status:this.value})"><option value="new" ${a.status === "new" ? "selected" : ""}>신규</option><option value="contacted" ${a.status === "contacted" ? "selected" : ""}>연락함</option><option value="done" ${a.status === "done" ? "selected" : ""}>완료</option></select></td>
        <td style="min-width:200px"><textarea class="note" onblur="setApp(${a.id},{note:this.value})" placeholder="통화 내용 등">${esc(a.note || "")}</textarea></td></tr>`).join("")}</table>` : '<p class="empty">신청이 없습니다.</p>';
  };
  $("#body").innerHTML = `<div class="panel"><div class="toolbar"><select id="status"><option value="">모든 상태</option><option value="new">신규</option><option value="contacted">연락함</option><option value="done">완료</option></select></div><div id="list"></div></div>`;
  $("#status").onchange = load; await load();
};
window.setApp = async (id, body) => { try { await A.put("/applications/" + id, body); API.toast("저장했습니다."); } catch (e) { alert(e.message); } };

/* ---------- 작업 ---------- */
function jobsTable(list, compact = false) {
  if (!list.length) return '<p class="empty">작업이 없습니다.</p>';
  return `<table class="t"><tr><th>#</th><th>종류</th>${list[0].family_code !== undefined ? "<th>가족</th>" : ""}<th>대상</th><th>상태</th><th class="r">시도</th>${compact ? "" : "<th>오류</th>"}<th>갱신</th><th></th></tr>
    ${list.map(j => `<tr><td>${j.id}</td><td>${j.kind === "analyze" ? "분석" : "AI 요약"}</td>${j.family_code !== undefined ? `<td>${esc(j.family_code || "–")}</td>` : ""}<td>${j.kind === "analyze" ? `<a href="#talk/${j.ref_id}">대화 #${j.ref_id}</a>` : `요약 #${j.ref_id}`}</td><td>${st(j.status)}</td><td class="r">${j.attempts}</td>${compact ? "" : `<td style="max-width:320px;color:var(--notable)">${esc(j.error || "")}</td>`}<td>${d(j.updated_at)}</td><td>${j.status === "failed" ? `<button class="btn sm" onclick="retryJob(${j.id})">다시 시도</button>` : ""}</td></tr>`).join("")}</table>`;
}
SCREENS.jobs = async () => {
  head("처리 작업", "대화 분석·AI 요약은 뒤에서 순서대로 처리됩니다. 실패 작업은 3회 자동 재시도 뒤 여기서 다시 시도합니다.");
  const load = async () => { const s = $("#status").value; $("#list").innerHTML = jobsTable(await A.get("/jobs?limit=200" + (s ? "&status=" + s : ""))); };
  $("#body").innerHTML = `<div class="panel"><div class="toolbar"><select id="status"><option value="">모든 상태</option><option value="queued">대기</option><option value="running">처리 중</option><option value="done">완료</option><option value="failed">실패</option></select><button class="btn sm" onclick="route()">새로고침</button></div><div id="list"></div></div>`;
  $("#status").onchange = load; await load();
};
window.retryJob = async id => { await A.post(`/jobs/${id}/retry`); API.toast("다시 대기열에 넣었습니다."); route(); };

/* ---------- 사용량 ---------- */
SCREENS.usage = async () => {
  head("API 사용량", "외부 AI API 호출을 목적별로 집계합니다 (계약 §13 · 사용량·오류 기록).");
  const [u, log] = await Promise.all([A.get("/usage?days=30"), A.get("/usage/log?limit=50")]);
  const P = { reply: "대화 응답", stt: "음성 변환", summary_conversation: "대화 요약", summary_weekly: "주간 요약" };
  $("#body").innerHTML = `<div class="panel"><h2>최근 30일 · ${u.mock ? "MOCK 모드 (실제 호출 없음)" : "OpenAI"}</h2>
    ${Object.keys(u.by_purpose).length ? `<table class="t"><tr><th>목적</th><th class="r">호출</th><th class="r">오류</th><th class="r">입력 토큰</th><th class="r">출력 토큰</th></tr>${Object.entries(u.by_purpose).map(([k, v]) => `<tr><td>${esc(P[k] || k)}</td><td class="r">${v.calls}</td><td class="r">${v.errors}</td><td class="r">${v.input_tokens.toLocaleString()}</td><td class="r">${v.output_tokens.toLocaleString()}</td></tr>`).join("")}</table>` : '<p class="empty">기록이 없습니다.</p>'}</div>
    <div class="panel"><h2>최근 호출 50건</h2>${log.length ? `<table class="t"><tr><th>시각</th><th>목적</th><th>모델</th><th class="r">가족</th><th class="r">입력</th><th class="r">출력</th><th>결과</th></tr>${log.map(r => `<tr><td>${d(r.created_at)}</td><td>${esc(P[r.purpose] || r.purpose)}</td><td>${esc(r.model || "–")}</td><td class="r">${r.family_id || "–"}</td><td class="r">${r.input_tokens}</td><td class="r">${r.output_tokens}</td><td>${r.ok ? "성공" : `<span class="err">${esc(r.error || "실패")}</span>`}</td></tr>`).join("")}</table>` : '<p class="empty">기록이 없습니다.</p>'}</div>`;
};

/* ---------- 연동 안내 ---------- */
SCREENS.api = async () => {
  head("연동 안내", "백오피스가 쓰는 API 를 외부 시스템에서 그대로 호출할 수 있습니다. 전체 명세는 /docs (Swagger) 와 /openapi.json.");
  const base = location.origin;
  $("#body").innerHTML = `
    <div class="panel"><h2>인증</h2><p class="muted" style="margin:0 0 8px">요청 헤더에 <code>X-Admin-Token</code> 을 넣습니다. 토큰은 서버 환경변수 <code>ADMIN_TOKEN</code> 입니다. HTTPS 에서만 사용합니다.</p>
      <pre class="code">curl -H "X-Admin-Token: $ADMIN_TOKEN" ${esc(base)}/api/admin/stats</pre></div>
    <div class="panel"><h2>엔드포인트</h2><table class="t"><tr><th>용도</th><th>메서드 · 경로</th><th>설명</th></tr>
      <tr><td>현황</td><td><code>GET /api/admin/stats</code></td><td>가족·대화·신청·작업·외부 API 호출 수</td></tr>
      <tr><td rowspan="5">가족</td><td><code>GET /api/admin/families?q=</code></td><td>목록 (코드·이름 검색)</td></tr>
      <tr><td><code>POST /api/admin/families</code></td><td>가족 등록 (코드·부모님·보호자·비밀번호 2종·페르소나)</td></tr>
      <tr><td><code>GET /api/admin/families/{id}</code></td><td>상세 (페르소나·가족 이야기·기준선·최근 대화·작업)</td></tr>
      <tr><td><code>PUT /api/admin/families/{id}</code> · <code>DELETE</code></td><td>정보 수정·비밀번호 재설정 · 삭제(기록 일괄 삭제)</td></tr>
      <tr><td><code>GET /api/admin/families/{id}/export</code></td><td>가족 전체 기록 JSON (이관·외부 분석)</td></tr>
      <tr><td rowspan="2">대화</td><td><code>GET /api/admin/conversations?family_id=&status=</code></td><td>대화 목록 + 지표</td></tr>
      <tr><td><code>GET /api/admin/conversations/{id}</code></td><td>원문·태그·응답 간격 포함 상세</td></tr>
      <tr><td rowspan="2">신청</td><td><code>GET /api/admin/applications?status=</code></td><td>랜딩 신청 목록</td></tr>
      <tr><td><code>PUT /api/admin/applications/{id}</code></td><td>상태(new·contacted·done)·메모</td></tr>
      <tr><td rowspan="2">작업</td><td><code>GET /api/admin/jobs?status=</code></td><td>분석·요약 작업 목록</td></tr>
      <tr><td><code>POST /api/admin/jobs/{id}/retry</code></td><td>실패 작업 재시도</td></tr>
      <tr><td rowspan="2">사용량</td><td><code>GET /api/admin/usage?days=</code></td><td>목적별 호출·오류·토큰 집계</td></tr>
      <tr><td><code>GET /api/admin/usage/log</code></td><td>최근 호출 기록</td></tr></table></div>
    <div class="panel"><h2>연동 예시</h2>
      <p class="muted">① 기관 관리 도구에서 가족 등록 → ② 태블릿·보호자 앱은 그 가족 코드로 로그인 → ③ 대화가 쌓이면 <code>/conversations</code> 와 <code>/families/{id}/export</code> 로 지표를 가져가 기관 대시보드에 표시 → ④ 알림 발송(이번 범위 밖)은 <code>/conversations?status=analyzed</code> 를 주기적으로 읽어 기준선 비교 결과로 보낸다.</p>
      <pre class="code">// 신규 가족 등록 (JSON)
POST ${esc(base)}/api/admin/families
{ "code": "SJ001", "parent_name": "김영희", "parent_age": 78, "region": "세종시",
  "guardian_name": "김보호", "guardian_relation": "딸",
  "guardian_password": "guardian-pw", "tablet_password": "tablet-pw" }

// 가족 기록 내보내기
GET ${esc(base)}/api/admin/families/1/export   →  { family, memories, baseline, conversations[ turns, metric ], summaries }</pre></div>`;
};
