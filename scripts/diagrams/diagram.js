/* 간단한 다이어그램 렌더러: 노드를 절대 좌표로 놓고 SVG 화살표로 잇는다. 각 diagram HTML 에서 DIAGRAM 전역을 정의하면 그린다.
   DIAGRAM = { title, subtitle, width, height, groups:[{x,y,w,h,label,tone}], nodes:[{id,x,y,w,h,title,lines[],tone}], edges:[{from,to,label,side,dash}] } */
(function () {
  const d = window.DIAGRAM;
  const root = document.getElementById('canvas');
  root.style.width = d.width + 'px'; root.style.height = d.height + 'px';
  document.getElementById('title').textContent = d.title;
  document.getElementById('subtitle').textContent = d.subtitle || '';
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('width', d.width); svg.setAttribute('height', d.height); svg.classList.add('edges');
  svg.innerHTML = `<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#17191B"/></marker>
    <marker id="crow" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse"><path d="M0 6L11 1M0 6L11 11M0 6L11 6" fill="none" stroke="#17191B" stroke-width="1.4"/></marker>
    <marker id="one" viewBox="0 0 12 12" refX="11" refY="6" markerWidth="10" markerHeight="10" orient="auto-start-reverse"><path d="M6 1V11" fill="none" stroke="#17191B" stroke-width="1.6"/></marker></defs>`;
  root.appendChild(svg);
  (d.groups || []).forEach(g => { const el = document.createElement('div'); el.className = 'group ' + (g.tone || ''); Object.assign(el.style, { left: g.x + 'px', top: g.y + 'px', width: g.w + 'px', height: g.h + 'px' }); el.innerHTML = `<span>${g.label}</span>`; root.appendChild(el); });
  const pos = {};
  d.nodes.forEach(n => {
    const el = document.createElement('div'); el.className = 'node ' + (n.tone || ''); el.id = n.id;
    Object.assign(el.style, { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px', height: n.h ? n.h + 'px' : 'auto' });
    el.innerHTML = `<div class="t">${n.title}</div>` + (n.lines || []).map(l => `<div class="l">${l}</div>`).join('');
    root.appendChild(el); pos[n.id] = el;
  });
  const rect = id => { const r = pos[id].getBoundingClientRect(), c = root.getBoundingClientRect(); return { x: r.left - c.left, y: r.top - c.top, w: r.width, h: r.height }; };
  const anchor = (r, side) => side === 'top' ? [r.x + r.w / 2, r.y] : side === 'bottom' ? [r.x + r.w / 2, r.y + r.h] : side === 'left' ? [r.x, r.y + r.h / 2] : [r.x + r.w, r.y + r.h / 2];
  const auto = (a, b) => { const dx = (b.x + b.w / 2) - (a.x + a.w / 2), dy = (b.y + b.h / 2) - (a.y + a.h / 2); return Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? ['right', 'left'] : ['left', 'right']) : (dy > 0 ? ['bottom', 'top'] : ['top', 'bottom']); };
  (d.edges || []).forEach(e => {
    const a = rect(e.from), b = rect(e.to); const [sa, sb] = e.sides || auto(a, b);
    const [x1, y1] = anchor(a, sa), [x2, y2] = anchor(b, sb);
    let path;
    if (sa === 'right' || sa === 'left') { const mx = (x1 + x2) / 2; path = `M${x1} ${y1} C${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`; }
    else { const my = (y1 + y2) / 2; path = `M${x1} ${y1} C${x1} ${my}, ${x2} ${my}, ${x2} ${y2}`; }
    const p = document.createElementNS('http://www.w3.org/2000/svg', 'path'); p.setAttribute('d', path); p.setAttribute('fill', 'none'); p.setAttribute('stroke', '#17191B'); p.setAttribute('stroke-width', e.bold ? 2.4 : 1.6);
    if (e.dash) p.setAttribute('stroke-dasharray', '6 5');
    p.setAttribute('marker-end', e.end === 'crow' ? 'url(#crow)' : e.end === 'none' ? '' : 'url(#arr)'); if (e.start) p.setAttribute('marker-start', `url(#${e.start})`);
    svg.appendChild(p);
    if (e.label) { const t = document.createElement('div'); t.className = 'elabel'; t.textContent = e.label; const lx = (x1 + x2) / 2 + (e.dx || 0), ly = (y1 + y2) / 2 + (e.dy || 0); Object.assign(t.style, { left: lx + 'px', top: ly + 'px' }); root.appendChild(t); }
  });
  (d.notes || []).forEach(n => { const el = document.createElement('div'); el.className = 'noteb'; Object.assign(el.style, { left: n.x + 'px', top: n.y + 'px', width: n.w + 'px' }); el.innerHTML = n.html; root.appendChild(el); });
})();
