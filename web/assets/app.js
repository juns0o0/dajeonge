/* 보호자 앱 (해시 라우팅 SPA). 화면: 홈 / 대화 기록 / 대화 상세 / 가족 정보 / 설정 */
const $ = s => document.querySelector(s), esc = API.esc;
const LEVEL = { same: "평소", watch: "관찰", notable: "확인", collecting: "기준 수집 중" };
const KEYS = ["avg_response_gap", "avg_utterance_len", "repeat_rate", "uncertain_rate", "participation"];
let LABELS = {}, FAM = null;

const fmt = (k, v) => v == null ? "–" : (k.endsWith("rate") || k === "participation") ? Math.round(v * 100) : k === "avg_response_gap" ? v.toFixed(1) : Math.round(v);
const unit = k => (LABELS[k] && LABELS[k].unit) || "";
const pill = lv => `<span class="pill ${lv}">${LEVEL[lv] || lv}</span>`;
const worst = cmp => { const r = { same: 0, watch: 1, notable: 2 }; return Object.values(cmp || {}).reduce((a, v) => r[v.level] > r[a] ? v.level : a, "same"); };

/* ---------- 로그인 ---------- */
$("#mark").innerHTML = ILLUS.mark;
function enter() { $("#login").hidden = true; $("#app").hidden = false; FAM = API.auth().family; route(); }
if (API.auth() && API.auth().role === "guardian") enter();
$("#loginForm").onsubmit = async e => { e.preventDefault(); $("#loginErr").textContent = "";
  try { await API.login($("#code").value, $("#pw").value, "guardian"); enter(); } catch (err) { $("#loginErr").textContent = err.message; } };
const onUnauthorized = () => { $("#app").hidden = true; $("#login").hidden = false; };

/* ---------- 라우팅 ---------- */
window.addEventListener("hashchange", route);
async function route() {
  if (!API.auth()) return onUnauthorized();
  const [name, arg] = (location.hash.replace("#", "") || "home").split("/");
  const tab = { talk: "talks" }[name] || name;
  document.querySelectorAll("#tabbar a").forEach(a => a.classList.toggle("on", a.dataset.t === tab));
  const fn = SCREENS[name] || SCREENS.home;
  $("#body").innerHTML = '<p class="faint" style="padding:40px 0;text-align:center">불러오는 중…</p>';
  try { await fn(arg); } catch (err) { if (err.status === 401) return onUnauthorized(); $("#body").innerHTML = `<p class="err">${esc(err.message)}</p>`; }
  window.scrollTo(0, 0);
}
function head(title, sub, back, action = "") {
  $("#head").innerHTML = `${back ? `<button class="back" onclick="history.back()" aria-label="뒤로">‹</button>` : ""}<h1>${esc(title)}${sub ? `<div class="sub">${esc(sub)}</div>` : ""}</h1>${action}`;
}
const SCREENS = {};

/* ---------- 홈 ---------- */
SCREENS.home = async () => {
  const d = await API.get("/dashboard/overview", { onUnauthorized }); LABELS = d.metric_labels; FAM = d.family;
  const b = d.baseline, w = d.week, lv = b.status === "ready" ? worst(d.compare) : "collecting";
  const headline = lv === "same" ? "평소와 같습니다" : lv === "collecting" ? "평소 기준을<br>모으는 중입니다" : lv === "watch" ? "관찰이 필요한<br>지표가 있습니다" : "확인이 필요한<br>지표가 있습니다";
  head(`${FAM.parent_name}님`, "최근 7일");
  const cards = KEYS.map((k, i) => { const c = d.compare && d.compare[k]; const v = w[k];
    return `<button class="metric ${i === 1 ? "dark" : ""}" onclick="location.hash='#metric/${k}'"><span class="label" ${i === 1 ? 'style="color:#A39C90"' : ""}>${LABELS[k].name}</span><span class="mv num">${fmt(k, v)}<small>${unit(k)}</small></span>${c ? pill(c.level) : `<span class="mb">${b.status === "ready" ? "이번 주 데이터 없음" : "기준 수집 중"}</span>`}</button>`; }).join("");
  $("#body").innerHTML = `<div class="stack">
    <div class="hero-card"><div class="label" style="color:var(--ink-2)">이번 주</div><h2 style="font-size:22px;margin-top:6px">${headline}</h2>
      <p class="muted" style="font-size:13.5px;margin-top:8px">대화 ${w.conversations}회 · ${w.total_minutes}분${b.status === "ready" ? "" : ` · 유효 대화 ${b.valid_conversations}/${b.need_conversations}회 · ${b.days}/${b.need_days}일`}</p>
      <div class="illus">${ILLUS.grandma}</div></div>
    ${b.status !== "ready" ? `<div class="note">첫 대화 후 14일, 유효 대화 5회가 모이면 평소 기준이 정해지고 비교가 표시됩니다.</div>` : ""}
    <div class="grid2">${cards}<button class="metric" style="background:var(--lime-soft)" onclick="location.hash='#report'"><span class="label">AI 요약</span><span style="font-weight:800;font-size:16px;margin-top:4px">이번 주 요약<br>만들기 ›</span></button></div>
    <div class="card"><div class="row"><h3 style="font-size:16px">최근 14일 대화</h3><span class="faint" style="font-size:12px">막대 = 대화 시간(분) · 선 = 응답 간격(초)</span></div>${chart(d.series)}</div>
    ${d.last_conversation ? `<div class="list"><a href="#talk/${d.last_conversation.id}"><div class="date-b"><b>${d.last_conversation.started_at.slice(8, 10)}</b><span>최근</span></div><div><b>마지막 대화</b><div class="faint" style="font-size:12.5px">${API.fmtDate(d.last_conversation.started_at)} · 주고받은 말 ${d.last_conversation.turn_count}번</div></div><span class="chev">›</span></a></div>` : ""}
    <p class="faint" style="font-size:12px">지표는 부모님 본인의 초반 2주와 비교한 참고 정보이며 의료 진단이 아닙니다.</p></div>`;
};
function chart(series) {
  const w = 400, h = 150, L = 28, R = 28, T = 10, B = 24, n = series.length, bw = (w - L - R) / n;
  const maxM = Math.max(5, ...series.map(s => s.minutes)), gaps = series.filter(s => s.avg_response_gap != null), maxG = Math.max(3, ...gaps.map(s => s.avg_response_gap));
  const x = i => L + i * bw + bw / 2, yM = v => T + (h - T - B) * (1 - v / maxM), yG = v => T + (h - T - B) * (1 - v / maxG);
  let g = series.map((s, i) => `<rect x="${x(i) - bw * .3}" y="${yM(s.minutes)}" width="${bw * .6}" height="${h - B - yM(s.minutes)}" rx="4" fill="${s.minutes ? "var(--lime)" : "var(--line)"}"><title>${s.date} · ${s.conversations}회 ${s.minutes}분</title></rect>`).join("");
  const pts = series.map((s, i) => s.avg_response_gap == null ? null : [x(i), yG(s.avg_response_gap)]).filter(Boolean);
  if (pts.length > 1) g += `<path d="M${pts.map(p => p.join(",")).join("L")}" fill="none" stroke="var(--ink)" stroke-width="2.2" stroke-linejoin="round"/>` + pts.map(p => `<circle cx="${p[0]}" cy="${p[1]}" r="3" fill="var(--ink)"/>`).join("");
  g += series.map((s, i) => i % 2 ? "" : `<text x="${x(i)}" y="${h - 6}" text-anchor="middle">${+s.date.slice(8)}</text>`).join("");
  g += `<text x="${L - 4}" y="${T + 8}" text-anchor="end">${maxM}분</text><text x="${w - R + 4}" y="${T + 8}">${maxG}초</text>`;
  return `<svg class="chart" viewBox="0 0 ${w} ${h}" style="width:100%;height:auto;margin-top:8px">${g}</svg>`;
}

/* ---------- 지표 상세 ---------- */
SCREENS.metric = async k => {
  const d = await API.get("/dashboard/overview"); LABELS = d.metric_labels; const m = LABELS[k]; if (!m) return (location.hash = "#home");
  const c = d.compare && d.compare[k], b = d.baseline;
  head(m.name, "최근 7일 · 평소 대비", true);
  const rows = d.series.filter(s => s[k] != null).reverse().map(s => `<tr><td>${s.date.slice(5).replace("-", "/")}</td><td class="num">${fmt(k, s[k])}${unit(k)}</td></tr>`).join("");
  $("#body").innerHTML = `<div class="stack">
    <div class="card"><div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">${c ? pill(c.level) : pill("collecting")}<span class="num" style="font-size:28px;font-weight:800">${fmt(k, d.week[k])}${unit(k)}</span>${b.status === "ready" && b.values[k] ? `<span class="muted">평소 ${fmt(k, b.values[k].mean)}${unit(k)}</span>` : ""}</div>
      <p class="muted" style="margin-top:10px;font-size:14px"><b>이렇게 재요.</b> ${esc(m.how)}</p>
      <p class="faint" style="font-size:12.5px;margin-top:6px">평소보다 1편차 이상 벗어나면 ‘관찰’, 1.5편차 이상이면 ‘확인’으로 표시합니다.</p></div>
    <div class="card"><div class="label">최근 14일 일별</div>${rows ? `<table class="t" style="margin-top:8px"><tr><th>날짜</th><th>${m.name}</th></tr>${rows}</table>` : '<p class="faint" style="margin-top:8px">아직 데이터가 없어요.</p>'}</div></div>`;
};

/* ---------- 대화 기록 ---------- */
SCREENS.talks = async () => {
  const list = await API.get("/conversations?limit=100");
  head("대화 기록", `${list.length}회`);
  if (!list.length) return ($("#body").innerHTML = `<div class="card" style="text-align:center"><div style="max-width:200px;margin:0 auto">${ILLUS.bubbles}</div><p class="muted">아직 대화가 없습니다.</p></div>`);
  const groups = {}; list.forEach(c => (groups[c.started_at.slice(0, 7)] = groups[c.started_at.slice(0, 7)] || []).push(c));
  $("#body").innerHTML = `<div class="stack">` + Object.entries(groups).map(([ym, cs]) => `<div class="label">${ym.replace("-", "년 ")}월</div><div class="list">${cs.map(row).join("")}</div>`).join("") + `</div>`;
};
function row(c) {
  const m = c.metric; const st = c.status === "analyzed" ? "" : c.status === "open" ? ' <span class="chip" style="font-size:11px;padding:0 7px">진행 중</span>' : c.status === "failed" ? ' <span class="tag repeat">분석 실패</span>' : ' <span class="chip" style="font-size:11px;padding:0 7px">분석 중</span>';
  const d = new Date(c.started_at + "Z");
  return `<a href="#talk/${c.id}"><div class="date-b"><b>${d.getDate()}</b><span>${"일월화수목금토"[d.getDay()]}</span></div><div><b>${d.toLocaleTimeString("ko-KR", { hour: "numeric", minute: "2-digit" })}</b>${st}<div class="faint" style="font-size:12.5px">${m ? `${Math.round(m.duration_sec / 60)}분 · 말 ${m.parent_turns}번 · 응답 간격 ${m.avg_response_gap != null ? m.avg_response_gap.toFixed(1) + "초" : "–"}${m.valid ? "" : " · 짧은 대화"}` : `주고받은 말 ${c.turn_count}번`}</div></div><span class="chev">›</span></a>`;
}

/* ---------- 대화 상세 ---------- */
SCREENS.talk = async id => {
  const c = await API.get(`/conversations/${id}`); const sums = await API.get(`/summaries?kind=conversation&conversation_id=${id}`);
  head(API.fmtDate(c.started_at, { month: "long", day: "numeric", weekday: "short" }) + " 대화", `${API.fmtDate(c.started_at, { hour: "numeric", minute: "2-digit" })} · 주고받은 말 ${c.turn_count}번`, true,
       `<button class="icon-btn" id="delBtn" title="이 대화 삭제" aria-label="삭제">🗑</button>`);
  const m = c.metric;
  const metricHtml = m ? `<table class="t"><tr><th>지표</th><th>이 대화</th></tr>${KEYS.map(k => `<tr><td>${(LABELS[k] || {}).name || k}</td><td class="num">${fmt(k, m[k])}${unit(k)}</td></tr>`).join("")}</table>${m.valid ? "" : '<p class="faint" style="font-size:12.5px;margin-top:6px">부모님 발화 3회 미만: 평소 기준 계산에서 제외</p>'}`
    : `<p class="muted">${c.status === "open" ? "아직 진행 중인 대화예요." : "분석 중이에요. 잠시 후 다시 열어 주세요."}</p>`;
  const sum = sums[0];
  const turns = c.turns.map(t => `<div class="bub ${t.speaker}"><span class="who">${t.speaker === "bot" ? "다정이" : FAM.parent_name}</span>${esc(t.text)}${t.speaker === "parent" ? `<div style="margin-top:5px">${(t.tags || []).map(x => `<span class="tag ${x}">${x === "repeat" ? "같은 말 반복" : "불확실 표현"}</span>`).join("")}${t.response_gap_sec != null ? `<span class="tag gap">응답 ${t.response_gap_sec.toFixed(1)}초</span>` : ""}${t.input_mode === "text" ? '<span class="tag gap">글로 입력</span>' : ""}</div>` : ""}</div>`).join("");
  $("#body").innerHTML = `<div class="stack">
    <div class="card"><div class="label">이 대화의 지표</div><div style="margin-top:8px">${metricHtml}</div></div>
    <div class="card soft"><div class="row"><h3 style="font-size:16px">AI 요약</h3><button class="btn sm dark" id="sumBtn" ${m ? "" : "disabled"}>${sum ? "다시 만들기" : "요약 만들기"}</button></div>
      <div id="sumBox" style="margin-top:10px">${sum ? sumHtml(sum) : '<p class="faint" style="font-size:13.5px">버튼을 누르면 이 대화를 요약합니다.</p>'}</div></div>
    <div class="card"><div class="label">대화 원문</div><div class="tx" style="margin-top:10px">${turns}</div></div></div>`;
  if (!LABELS.avg_response_gap) { const d = await API.get("/dashboard/overview"); LABELS = d.metric_labels; }
  $("#sumBtn").onclick = () => makeSummary({ kind: "conversation", conversation_id: c.id }, $("#sumBox"), $("#sumBtn"));
  $("#delBtn").onclick = async () => { if (!confirmBox("이 대화와 지표, 음성 파일을 모두 지울까요?")) return; await API.del(`/conversations/${c.id}`); API.toast("삭제되었습니다"); location.hash = "#talks"; };
};
function sumHtml(s) {
  if (s.status === "done") return `<p style="font-size:14.5px;line-height:1.65">${esc(s.text)}</p><p class="faint" style="font-size:11.5px;margin-top:6px">${API.fmtDate(s.created_at)} · ${s.model || ""}</p>`;
  if (s.status === "failed") return `<p class="err">요약에 실패했습니다: ${esc(s.error)}</p>`;
  return `<p class="muted">요약을 만드는 중입니다…</p>`;
}
async function makeSummary(body, box, btn) {
  btn.disabled = true; box.innerHTML = '<p class="muted">요약을 만드는 중입니다…</p>';
  try { const d = await API.post("/summaries", body); let s = d.summary;
    for (let i = 0; i < 40 && s.status === "pending"; i++) { await new Promise(r => setTimeout(r, 1500)); s = await API.get(`/summaries/${s.id}`); }
    box.innerHTML = s.status === "pending" ? '<p class="muted">아직 만드는 중입니다. 잠시 후 다시 열어 주세요.</p>' : sumHtml(s); btn.textContent = "다시 만들기";
  } catch (err) { box.innerHTML = `<p class="err">${esc(err.message)}</p>`; } finally { btn.disabled = false; }
}
function confirmBox(msg) { try { return window.confirm(msg); } catch { return true; } }

/* ---------- 주간 리포트 ---------- */
SCREENS.report = async () => {
  const d = await API.get("/dashboard/overview"); LABELS = d.metric_labels; const sums = await API.get("/summaries?kind=weekly"); const w = d.week, b = d.baseline;
  head("이번 주 AI 요약", `${d.period.start.slice(5, 10).replace("-", "/")} ~ ${d.period.end.slice(5, 10).replace("-", "/")}`, true);
  const rows = KEYS.map(k => { const c = d.compare && d.compare[k]; return `<tr><td>${LABELS[k].name}</td><td class="num">${b.values && b.values[k] ? fmt(k, b.values[k].mean) + unit(k) : "–"}</td><td class="num">${fmt(k, w[k])}${unit(k)}</td><td>${c ? pill(c.level) : "–"}</td></tr>`; }).join("");
  $("#body").innerHTML = `<div class="stack">
    <div class="card"><table class="t"><tr><th>지표</th><th>평소</th><th>이번 주</th><th>비교</th></tr>${rows}</table>${b.status !== "ready" ? '<p class="faint" style="font-size:12.5px;margin-top:8px">평소 기준이 아직 모이는 중이라 비교는 비워 두었습니다.</p>' : ""}</div>
    <div class="card soft"><div class="row"><h3 style="font-size:16px">AI 요약</h3><button class="btn sm dark" id="sumBtn">${sums[0] ? "다시 만들기" : "요약 만들기"}</button></div><div id="sumBox" style="margin-top:10px">${sums[0] ? sumHtml(sums[0]) : '<p class="faint" style="font-size:13.5px">버튼을 누르면 최근 7일을 요약합니다.</p>'}</div></div>
    ${sums.length > 1 ? `<div class="label">이전 요약</div><div class="stack">${sums.slice(1, 4).map(s => `<div class="card flat" style="font-size:13.5px">${sumHtml(s)}</div>`).join("")}</div>` : ""}
    <p class="faint" style="font-size:12px">요약은 참고용입니다. 변화가 이어지면 전문기관 상담을 권합니다.</p></div>`;
  $("#sumBtn").onclick = () => makeSummary({ kind: "weekly" }, $("#sumBox"), $("#sumBtn"));
};

/* ---------- 가족 정보 ---------- */
SCREENS.family = async () => {
  const f = await API.get("/family"); const mems = await API.get("/family/memories"); FAM = f; const p = f.persona || {};
  head("가족 정보", `${f.parent_name}님 · 가족 코드 ${f.code}`);
  const li = (name, val, ph) => `<div class="field"><label for="p_${name}">${ph}</label><input id="p_${name}" value="${esc(Array.isArray(val) ? val.join(", ") : (val || ""))}"></div>`;
  $("#body").innerHTML = `<div class="stack">
    <div class="card"><div class="row"><h3 style="font-size:16px">부모님·보호자</h3></div>
      <form id="famForm" style="margin-top:10px">${li("parent_name", f.parent_name, "부모님 성함")}<div class="grid2">${li("parent_age", f.parent_age, "연세")}${li("region", f.region, "사시는 곳")}</div><div class="grid2">${li("guardian_name", f.guardian_name, "보호자 이름")}${li("guardian_relation", f.guardian_relation, "관계")}</div>${li("keep_audio_days", f.keep_audio_days, "음성 파일 보관 일수")}<button class="btn sm dark" type="submit">저장</button></form></div>
    <div class="card"><h3 style="font-size:16px">${esc(p.display_name || "자녀")} 페르소나 <span class="faint" style="font-size:12px;font-weight:500">다정이가 이렇게 말해요</span></h3>
      <form id="perForm" style="margin-top:10px">${li("display_name", p.display_name, "자녀 이름 (다정이가 쓰는 이름)")}<div class="grid2">${li("calls_parent", p.calls_parent, "부모님을 부르는 말")}${li("formality", p.formality, "말투 (반말/존댓말)")}</div>
        ${li("endings", p.endings, "자주 쓰는 어미 (쉼표로 구분)")}${li("expressions", p.expressions, "자주 쓰는 표현 (쉼표)")}${li("personality", p.personality, "성격 (쉼표)")}${li("habits", p.habits, "대화 습관 (쉼표)")}${li("avoid_topics", p.avoid_topics, "피할 주제 (쉼표)")}
        <div class="field"><label for="p_family_notes">가족 관계 메모</label><textarea id="p_family_notes" rows="3">${esc(p.family_notes || "")}</textarea><span class="hint">예: 남편(작고), 장남 민호(서울), 손녀 서윤(10살)</span></div>
        <button class="btn sm dark" type="submit">저장</button></form></div>
    <div class="card"><div class="row"><h3 style="font-size:16px">가족 이야기 <span class="faint num" style="font-size:13px">${mems.length}</span></h3><button class="btn sm lime" id="addMem">+ 추가</button></div>
      <p class="faint" style="font-size:12.5px;margin-top:4px">다정이는 여기 등록된 이야기만 말합니다. 키워드가 대화와 겹치면 그 이야기를 꺼냅니다.</p>
      <form id="memForm" hidden class="card flat" style="margin-top:10px;padding:12px"><input type="hidden" id="m_id"><div class="field"><label for="m_title">제목</label><input id="m_title" required placeholder="예: 대천 해수욕장 가족여행"></div><div class="field"><label for="m_detail">내용</label><input id="m_detail" placeholder="예: 민호 10살 때. 아빠가 튜브 바람 넣다 쓰러질 뻔함"></div><div class="grid2"><div class="field"><label for="m_keywords">키워드 (쉼표)</label><input id="m_keywords" placeholder="대천, 바다, 여행"></div><div class="field"><label for="m_year">연도</label><input id="m_year" inputmode="numeric" placeholder="1988"></div></div><div style="display:flex;gap:6px"><button class="btn sm dark" type="submit">저장</button><button class="btn sm ghost" type="button" id="memCancel">취소</button></div></form>
      <div class="stack" id="memList" style="margin-top:10px;gap:8px">${mems.map(memCard).join("")}</div></div></div>`;
  const vals = ids => Object.fromEntries(ids.map(k => [k, $("#p_" + k).value.trim()]));
  const list = s => s.split(",").map(x => x.trim()).filter(Boolean);
  $("#famForm").onsubmit = async e => { e.preventDefault(); const v = vals(["parent_name", "parent_age", "region", "guardian_name", "guardian_relation", "keep_audio_days"]);
    await API.put("/family", { parent_name: v.parent_name, parent_age: +v.parent_age || null, region: v.region || null, guardian_name: v.guardian_name, guardian_relation: v.guardian_relation, keep_audio_days: +v.keep_audio_days || 30 }); API.toast("저장되었습니다"); };
  $("#perForm").onsubmit = async e => { e.preventDefault(); const v = vals(["display_name", "calls_parent", "formality", "endings", "expressions", "personality", "habits", "avoid_topics", "family_notes"]);
    await API.put("/family/persona", { display_name: v.display_name, calls_parent: v.calls_parent, formality: v.formality, endings: list(v.endings), expressions: list(v.expressions), personality: list(v.personality), habits: list(v.habits), avoid_topics: list(v.avoid_topics), family_notes: v.family_notes }); API.toast("페르소나가 저장되었습니다"); };
  const openMem = m => { $("#memForm").hidden = false; $("#m_id").value = m ? m.id : ""; $("#m_title").value = m ? m.title : ""; $("#m_detail").value = m ? m.detail : ""; $("#m_keywords").value = m ? m.keywords.join(", ") : ""; $("#m_year").value = m && m.year ? m.year : ""; $("#m_title").focus(); };
  $("#addMem").onclick = () => openMem(null); $("#memCancel").onclick = () => ($("#memForm").hidden = true);
  $("#memForm").onsubmit = async e => { e.preventDefault(); const body = { title: $("#m_title").value.trim(), detail: $("#m_detail").value.trim(), keywords: list($("#m_keywords").value), year: +$("#m_year").value || null }; const id = $("#m_id").value;
    if (id) await API.put(`/family/memories/${id}`, body); else await API.post("/family/memories", body); API.toast("저장되었습니다"); route(); };
  $("#memList").onclick = async e => { const b = e.target.closest("button"); if (!b) return; const id = +b.dataset.id; const m = mems.find(x => x.id === id);
    if (b.dataset.act === "edit") openMem(m); else if (b.dataset.act === "del" && confirmBox(`'${m.title}' 기록을 지울까요?`)) { await API.del(`/family/memories/${id}`); route(); } };
};
function memCard(m) { return `<div class="card flat" style="padding:12px"><div class="row"><b>${esc(m.title)}${m.year ? ` <span class="faint num" style="font-weight:400;font-size:12px">${m.year}</span>` : ""}</b><span><button class="btn sm ghost" data-act="edit" data-id="${m.id}">수정</button><button class="btn sm ghost" data-act="del" data-id="${m.id}">삭제</button></span></div><p class="muted" style="font-size:13.5px">${esc(m.detail)}</p><div class="chips" style="margin-top:6px">${m.keywords.map(k => `<span class="chip" style="font-size:11.5px;padding:1px 8px">${esc(k)}</span>`).join("")}</div></div>`; }

/* ---------- 설정 ---------- */
SCREENS.more = async () => {
  const jobs = await API.get("/jobs"); const failed = jobs.filter(j => j.status === "failed");
  head("설정", FAM ? `${FAM.guardian_name} · ${FAM.code}` : "");
  $("#body").innerHTML = `<div class="stack">
    <div class="card"><h3 style="font-size:16px">태블릿 연결</h3><p class="muted" style="font-size:14px;margin-top:6px">부모님 태블릿 브라우저(Chrome)에서 <b>${location.origin}/tablet.html</b>을 열고 가족 코드 <b>${FAM ? FAM.code : ""}</b>와 태블릿 비밀번호를 넣으세요. 홈 화면에 추가하면 앱처럼 쓸 수 있어요.</p></div>
    <div class="card"><div class="row"><h3 style="font-size:16px">처리 작업</h3><span class="faint" style="font-size:12.5px">최근 ${jobs.length}건 · 실패 ${failed.length}건</span></div>
      <p class="faint" style="font-size:12.5px;margin-top:4px">대화 분석과 AI 요약은 뒤에서 처리됩니다. 실패한 작업은 다시 시도할 수 있습니다.</p>
      <div class="stack" style="margin-top:10px;gap:6px">${(failed.length ? failed : jobs.slice(0, 5)).map(j => `<div class="card flat" style="padding:10px 12px;font-size:13px"><div class="row"><span><b>${j.kind === "analyze" ? "대화 분석" : "AI 요약"}</b> #${j.ref_id} · <span class="${j.status === "failed" ? "err" : "muted"}">${j.status}</span> · 시도 ${j.attempts}회</span>${j.status === "failed" ? `<button class="btn sm" data-retry="${j.id}">다시 시도</button>` : ""}</div>${j.error ? `<div class="faint" style="font-size:11.5px;margin-top:4px;white-space:pre-wrap">${esc(j.error.split("\n")[0])}</div>` : ""}</div>`).join("") || '<p class="faint">작업이 없어요.</p>'}</div></div>
    <div class="card"><h3 style="font-size:16px">개인정보</h3><p class="muted" style="font-size:14px;margin-top:6px">대화 기록은 ‘대화 기록 › 대화 상세 › 휴지통’에서 삭제할 수 있습니다. 음성 파일 보관 일수는 가족 정보에서 바꿀 수 있습니다. <a href="/privacy.html">처리방침</a></p></div>
    <button class="btn block" id="logout">로그아웃</button>
    <p class="faint" style="font-size:12px;text-align:center">다정이 MVP · 인하우스앤파트너스</p></div>`;
  $("#body").onclick = async e => { const b = e.target.closest("[data-retry]"); if (b) { await API.post(`/jobs/${b.dataset.retry}/retry`); API.toast("다시 시도합니다"); route(); } };
  $("#logout").onclick = async () => { await API.logout(); location.reload(); };
};
