/* API 호출 공통. 토큰은 localStorage 에 두고 Authorization 헤더로 보낸다. */
window.API = (function () {
  const BASE = (window.DAJEONG_API_BASE || "") + "/api";
  const KEY = "dajeong.auth";
  function auth() { try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch { return null; } }
  function setAuth(a) { try { a ? localStorage.setItem(KEY, JSON.stringify(a)) : localStorage.removeItem(KEY); } catch {} }
  async function req(method, path, body, opts = {}) {
    const headers = { ...(opts.headers || {}) };
    const a = auth(); if (a && a.token) headers["Authorization"] = "Bearer " + a.token;
    let payload = body;
    if (body && !(body instanceof FormData)) { headers["Content-Type"] = "application/json"; payload = JSON.stringify(body); }
    const r = await fetch(BASE + path, { method, headers, body: payload });
    let data = null; try { data = await r.json(); } catch {}
    if (r.status === 401) { setAuth(null); if (opts.onUnauthorized) opts.onUnauthorized(); }
    if (!r.ok) { const e = new Error((data && (data.detail || data.message)) || ("요청 실패 (" + r.status + ")")); e.status = r.status; e.data = data; throw e; }
    return data;
  }
  return {
    auth, setAuth,
    get: (p, o) => req("GET", p, null, o), post: (p, b, o) => req("POST", p, b, o), put: (p, b, o) => req("PUT", p, b, o), del: (p, o) => req("DELETE", p, null, o),
    async login(code, password, role) { const d = await req("POST", "/auth/login", { code, password, role }); setAuth({ token: d.token, role, family: d.family }); return d; },
    async logout() { try { await req("POST", "/auth/logout"); } catch {} setAuth(null); },
    fmtDate(iso, opt) { const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : iso + "Z"); return d.toLocaleString("ko-KR", opt || { month: "numeric", day: "numeric", hour: "numeric", minute: "2-digit" }); },
    toast(msg) { let t = document.getElementById("toast"); if (!t) { t = document.createElement("div"); t.id = "toast"; t.className = "toast"; document.body.appendChild(t); } t.textContent = msg; t.hidden = false; clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, 2600); },
    esc: s => String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])),
  };
})();
