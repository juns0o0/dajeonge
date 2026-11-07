/**
 * 다정이 랜딩 — 신청 저장 백엔드 (Google Apps Script) v1
 *
 * GitHub Pages(정적)에 올린 랜딩은 서버가 없어, 신청(POST /api/applications 대체)을 구글 시트에 쌓는다.
 * 열람은 applicants.html 이 doGet(action=list&key=ADMIN_KEY) 로 읽는다. 키 없이는 목록을 내주지 않는다.
 *
 * 시트(자동 생성):
 *  - applications : 신청 1건 = 1행 (서버 DB의 applications 테이블과 같은 열 이름)
 *  - log          : 요청 결과 기록 (new / invalid:* / honeypot / busy) — 연락처는 가려서
 *
 * 배포: 확장 프로그램 > Apps Script > 배포 > 새 배포 > 웹 앱 (실행: 나 / 액세스: 모든 사용자)
 * 코드 수정 후: 배포 > 배포 관리 > 연필 > 버전 "새 버전" > 배포 (URL은 그대로)
 */
var ADMIN_KEY = "CHANGE-ME"; // ← 열람 키. 긴 임의 문자열로 바꾼다. 공개 사이트 코드에는 넣지 않는다.

var COLS = ["id", "created_at", "kind", "name", "org_name", "phone", "email", "message", "agreed", "status", "note", "user_agent", "referrer"];
var LOG_COLS = ["at", "result", "name", "contact_masked", "kind"];
var KINDS = ["home", "org"];
var GLOBAL_PER_MIN = 120;

function sheet_(name, cols) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(name);
  if (!sh) { sh = ss.insertSheet(name); sh.appendRow(cols); sh.setFrozenRows(1); sh.getRange(1, 1, sh.getMaxRows(), cols.length).setNumberFormat("@"); return sh; }
  var head = sh.getRange(1, 1, 1, Math.max(sh.getLastColumn(), 1)).getValues()[0];
  if (head.join("|") !== cols.join("|")) sh.getRange(1, 1, 1, cols.length).setValues([cols]);
  return sh;
}
function nowSeoul_() { return Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd'T'HH:mm:ssXXX"); }
function mask_(s) { s = String(s || ""); if (!s) return ""; return s.slice(0, 3) + "***" + s.slice(-2); }
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function log_(result, v) {
  try { sheet_("log", LOG_COLS).appendRow([nowSeoul_(), result, (v && v.name) || "", mask_((v && (v.phone || v.email)) || ""), (v && v.kind) || ""]); } catch (e) {}
}

// ---- 검증 (서버 /api/applications 와 같은 규칙) ----
function validate_(b) {
  var kind = String(b.kind || "").trim();
  if (KINDS.indexOf(kind) < 0) return { error: "kind", detail: "신청 구분이 올바르지 않습니다." };
  var name = String(b.name || "").trim();
  if (!name || name.length > 50) return { error: "name", detail: "이름을 입력해 주세요." };
  var phone = String(b.phone || "").trim().slice(0, 30);
  var email = b.email == null ? "" : String(b.email).trim().toLowerCase().slice(0, 100);
  if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) return { error: "email", detail: "이메일 형식을 확인해 주세요." };
  if (!phone && !email) return { error: "contact", detail: "연락받을 수단을 입력해 주세요." };
  if (b.agreed !== true) return { error: "agreed", detail: "개인정보 수집·이용에 동의해 주세요." };
  return {
    kind: kind, name: name, org_name: kind === "org" ? String(b.org_name || "").trim().slice(0, 100) : "",
    phone: phone, email: email, message: String(b.message || "").trim().slice(0, 1000), agreed: true,
    user_agent: String(b.userAgent || "").slice(0, 300), referrer: String(b.referrer || "").slice(0, 300)
  };
}

// ---- 저장 ----
function doPost(e) {
  var body = {};
  try { body = JSON.parse((e && e.postData && e.postData.contents) || "{}"); } catch (err) { return json_({ ok: false, error: "json", detail: "요청 형식이 올바르지 않습니다." }); }
  if (body.website) { log_("honeypot", body); return json_({ ok: true }); } // 봇에게는 조용히 성공처럼

  var cache = CacheService.getScriptCache();
  var minuteKey = "rate:" + Math.floor(Date.now() / 60000);
  var cnt = parseInt(cache.get(minuteKey) || "0", 10) + 1;
  cache.put(minuteKey, String(cnt), 120);
  if (cnt > GLOBAL_PER_MIN) { log_("busy", body); return json_({ ok: false, error: "busy", detail: "잠시 후 다시 시도해 주세요." }); }

  var v = validate_(body);
  if (v.error) { log_("invalid:" + v.error, body); return json_({ ok: false, error: v.error, detail: v.detail }); }

  var lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    var sh = sheet_("applications", COLS);
    var now = nowSeoul_();
    var row = [Utilities.getUuid(), now, v.kind, v.name, v.org_name, v.phone, v.email, v.message, "TRUE", "new", "", v.user_agent, v.referrer];
    var r = sh.getLastRow() + 1;
    sh.getRange(r, 1, 1, COLS.length).setNumberFormat("@").setValues([row]);
    log_("new", v);
    return json_({ ok: true, id: row[0] });
  } catch (err) {
    log_("error:" + String(err).slice(0, 80), v);
    return json_({ ok: false, error: "server", detail: "신청을 저장하지 못했어요. 잠시 후 다시 시도해 주세요." });
  } finally {
    lock.releaseLock();
  }
}

// ---- 열람 (applicants.html) ----
function authed_(p) { return ADMIN_KEY && ADMIN_KEY !== "CHANGE-ME" && p.key === ADMIN_KEY; }
function doGet(e) {
  var p = (e && e.parameter) || {};
  if (p.action === "list") {
    if (!authed_(p)) return json_({ ok: false, error: "key" });
    var sh = sheet_("applications", COLS);
    var data = sh.getDataRange().getValues();
    var head = data[0] || COLS, rows = [];
    for (var i = 1; i < data.length; i++) {
      var o = {};
      head.forEach(function (h, k) { var val = data[i][k]; o[h] = val instanceof Date ? Utilities.formatDate(val, "Asia/Seoul", "yyyy-MM-dd'T'HH:mm:ssXXX") : val; });
      if (o.id) rows.push(o);
    }
    rows.reverse(); // 최신이 위
    return json_({ ok: true, rows: rows, sheetUrl: SpreadsheetApp.getActiveSpreadsheet().getUrl(), time: nowSeoul_() });
  }
  if (p.action === "status" || p.action === "note") {
    if (!authed_(p)) return json_({ ok: false, error: "key" });
    if (!p.id) return json_({ ok: false, error: "id" });
    var col = p.action === "status" ? COLS.indexOf("status") + 1 : COLS.indexOf("note") + 1;
    var value = p.action === "status" ? (["new", "contacted", "done"].indexOf(p.value) >= 0 ? p.value : "new") : String(p.value || "").slice(0, 500);
    var lock = LockService.getScriptLock(); lock.waitLock(20000);
    try {
      var s = sheet_("applications", COLS), d = s.getDataRange().getValues(), hit = 0;
      for (var r = 1; r < d.length; r++) if (String(d[r][0]) === String(p.id)) { s.getRange(r + 1, col).setNumberFormat("@").setValue(value); hit++; }
      return json_({ ok: hit > 0, updated: hit });
    } finally { lock.releaseLock(); }
  }
  if (p.action === "delete") {
    if (!authed_(p)) return json_({ ok: false, error: "key" });
    if (!p.id) return json_({ ok: false, error: "id" });
    var lock2 = LockService.getScriptLock(); lock2.waitLock(20000);
    try {
      var s2 = sheet_("applications", COLS), d2 = s2.getDataRange().getValues(), del = 0;
      for (var r2 = d2.length - 1; r2 >= 1; r2--) if (String(d2[r2][0]) === String(p.id)) { s2.deleteRow(r2 + 1); del++; }
      return json_({ ok: true, deleted: del });
    } finally { lock2.releaseLock(); }
  }
  return json_({ ok: true, service: "dajeong-landing", version: 1, time: nowSeoul_(), ready: ADMIN_KEY !== "CHANGE-ME" });
}
