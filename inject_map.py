import re

def inject():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Inject CSS into <style>
    new_css = """
/* Playoff Map Styles */
.map-outer-container {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  -webkit-overflow-scrolling: touch;
  display: flex;
  justify-content: center;
  padding: 20px 0;
  background: transparent;
}
.map-wrapper {
  position: relative;
  width: 1000px;
  height: 1000px;
  flex-shrink: 0;
}
#radialMap {
  width: 1000px;
  height: 1000px;
  display: block;
}
.map-center-img {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 220px;
  height: 220px;
  border-radius: 50%;
  object-fit: contain;
  filter: drop-shadow(0 0 25px rgba(0,255,0,0.5));
  pointer-events: none;
  z-index: 5;
}
.map-node { cursor: pointer; transition: all 0.3s; }
.map-node:hover { filter: brightness(1.4); transform: scale(1.05); transform-origin: center; }
.map-link { fill: none; stroke-width: 3; opacity: 0.3; transition: all 0.4s; stroke: rgba(255,255,255,0.2); }
.map-link.active { stroke-width: 5; opacity: 0.9; stroke: #2ecc71; filter: drop-shadow(0 0 10px #2ecc71); }
.map-link.final-path { stroke: #f1c40f; stroke-width: 7; filter: drop-shadow(0 0 15px #f1c40f); opacity: 1; }

.map-tooltip {
  position: fixed;
  padding: 12px;
  background: rgba(10, 25, 49, 0.95);
  backdrop-filter: blur(15px);
  color: #fff;
  border-radius: 12px;
  font-size: 14px;
  pointer-events: none;
  z-index: 100000;
  display: none;
  border: 1px solid rgba(0, 212, 255, 0.3);
  box-shadow: 0 15px 35px rgba(0,0,0,0.7);
  min-width: 200px;
}
.map-tooltip b { color: #f1c40f; display: block; margin-bottom: 8px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 5px; font-size: 16px; }
.map-tooltip-team { display: flex; align-items: center; gap: 10px; margin-bottom: 5px; font-weight: bold; }

@media (max-width: 900px) {
  .map-outer-container { padding: 0; justify-content: flex-start; }
  .map-wrapper { transform: scale(0.6); transform-origin: top left; height: 600px; width: 600px; }
}
/* END Playoff Map Styles */
"""
    style_end = content.find('</style>')
    if style_end != -1:
        content = content[:style_end] + new_css + content[style_end:]

    # 2. Inject JS functions before </body>
    new_js = """
<script>
let mapLastTap = 0;

function viewMatchEvents(matchId) {
  const m = [...GROUP_MATCHES, ...KO].find(x => x.id === matchId);
  if (!m) return;
  const sc = getScore(matchId), events = sc.events || [], hId = resolveSlot(m.h), aId = resolveSlot(m.a), T = TRANSLATIONS[currentLang];
  let h = `<div style="text-align:center; margin-bottom:20px;"><div style="display:flex; justify-content:center; align-items:center; gap:15px; font-size:1.2rem; font-weight:bold;">${teamLabel(hId)} <span>${sc.h ?? '-'} : ${sc.a ?? '-'}</span> ${teamLabel(aId)}</div><div style="color:var(--muted); font-size:0.9rem; margin-top:5px;">${tCity(m.v)} | ${formatKickoff(m.t)}</div></div>`;
  if (events.length === 0) { h += `<div style="text-align:center; padding:20px; color:var(--muted);">${T.info_unavailable}</div>`; }
  else {
    h += '<div class="events-list-simple" style="max-height:300px; overflow-y:auto; padding-right:10px;">';
    events.sort((a, b) => (parseInt(a.minute) || 0) - (parseInt(b.minute) || 0)).forEach(ev => {
      const isHome = ev.side === 'h', icon = { goal: '⚽', yellow: '🟨', red: '🟥' }[ev.type] || '', tId = isHome ? hId : aId, pName = getPlayerTranslatedName(ev.playerName, tId);
      h += `<div style="display:flex; justify-content:${isHome ? 'flex-start' : 'flex-end'}; margin-bottom:8px; align-items:center; gap:10px;">${isHome ? `<span style="font-weight:bold; color:var(--primary);">${ev.minute}'</span>` : ''}<span style="background:rgba(255,255,255,0.05); padding:4px 10px; border-radius:12px; border:1px solid rgba(255,255,255,0.1);">${isHome ? icon + ' ' + pName : pName + ' ' + icon}</span>${!isHome ? `<span style="font-weight:bold; color:var(--primary);">${ev.minute}'</span>` : ''}</div>`;
    });
    h += '</div>';
  }
  const modal = document.getElementById('eventsModal'), contentM = modal.querySelector('.events-modal-content');
  contentM.innerHTML = `<div class="modal-header"><h3>${T.match_events}</h3><button class="modal-close" onclick="closeEventsModal()">✕</button></div><div style="padding:20px;">${h}</div>`;
  modal.classList.add('show');
}

function renderMap() {
  const container = document.getElementById('panel8');
  if (!container) return;

  container.innerHTML = `
    <div class="map-outer-container">
      <div class="map-wrapper">
        <img src="https://img.freepik.com/premium-vector/gold-trophy-cup-with-garland-victory-champion-winner-concept-hand-drawn-vector-illustration_501069-1383.jpg" class="map-center-img">
        <svg id="radialMap" viewBox="0 0 1000 1000"></svg>
      </div>
    </div>
    <div id="mapTooltip" class="map-tooltip"></div>
  `;

  const svg = document.getElementById('radialMap');
  const centerX = 500, centerY = 500;

  const rings = [
    { id: 'r32', count: 32, radius: 440, matches: [33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64] },
    { id: 'r16', count: 16, radius: 360, matches: [65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80] },
    { id: 'qf',  count: 8,  radius: 280, matches: [81,82,83,84,85,86,87,88] },
    { id: 'sf',  count: 4,  radius: 200, matches: [89,90,91,92] },
    { id: 'f',   count: 2,  radius: 120, matches: [103, 104] }
  ];

  rings.forEach((ring, rIdx) => {
    if (rIdx === rings.length - 1) return;
    const nextRing = rings[rIdx+1];
    for(let i=0; i<ring.count; i++) {
      const angle = (i / ring.count) * Math.PI * 2 - Math.PI/2;
      const nextAngle = (Math.floor(i/2) / nextRing.count) * Math.PI * 2 - Math.PI/2;

      const x1 = centerX + Math.cos(angle) * ring.radius;
      const y1 = centerY + Math.sin(angle) * ring.radius;
      const x2 = centerX + Math.cos(nextAngle) * nextRing.radius;
      const y2 = centerY + Math.sin(nextAngle) * nextRing.radius;

      const path = document.createElementNS("http://www.w3.org/2000/svg", "line");
      path.setAttribute("x1", x1); path.setAttribute("y1", y1);
      path.setAttribute("x2", x2); path.setAttribute("y2", y2);
      path.setAttribute("class", "map-link");

      const mid = ring.matches[i];
      const winId = getWinner('M'+mid);
      if (winId) path.classList.add('active');
      if (mid === 101 || mid === 102) path.classList.add('final-path');
      svg.appendChild(path);
    }
  });

  rings.forEach((ring, rIdx) => {
    for(let i=0; i<ring.count; i++) {
      const matchId = ring.matches[i];
      if (matchId === 104) continue;

      const angle = (i / ring.count) * Math.PI * 2 - Math.PI/2;
      const x = centerX + Math.cos(angle) * ring.radius;
      const y = centerY + Math.sin(angle) * ring.radius;

      const m = KO.find(km => km.id === 'M' + matchId) || { h: '?', a: '?', id: 'M'+matchId };
      const winner = getWinner('M'+matchId);

      const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
      g.setAttribute("class", "map-node");
      g.onclick = (e) => handleMapNodeClick('M'+matchId, e);
      g.onmouseenter = (e) => showMapTooltip('M'+matchId, e);
      g.onmouseleave = () => { document.getElementById('mapTooltip').style.display='none'; };

      const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
      circle.setAttribute("cx", x); circle.setAttribute("cy", y);
      circle.setAttribute("r", rIdx === 4 ? 22 : 18);
      circle.setAttribute("fill", winner ? (TEAMS[winner]?.colors?.[0] || '#2ecc71') : 'rgba(16, 33, 61, 0.9)');
      circle.setAttribute("stroke", winner ? '#fff' : 'rgba(255,255,255,0.3)');
      circle.setAttribute("stroke-width", "2");
      g.appendChild(circle);

      if (winner) {
          const flagW = 22, flagH = 15;
          const img = document.createElementNS("http://www.w3.org/2000/svg", "image");
          img.setAttributeNS("http://www.w3.org/1999/xlink", "href", TEAMS[winner].f);
          img.setAttribute("x", x - flagW/2);
          img.setAttribute("y", y - flagH/2);
          img.setAttribute("width", flagW);
          img.setAttribute("height", flagH);
          g.appendChild(img);
      } else {
          const txt = document.createElementNS("http://www.w3.org/2000/svg", "text");
          txt.setAttribute("x", x); txt.setAttribute("y", y + 4);
          txt.setAttribute("text-anchor", "middle");
          txt.setAttribute("fill", "rgba(255,255,255,0.6)");
          txt.setAttribute("font-size", "10px");
          txt.textContent = 'M' + matchId;
          g.appendChild(txt);
      }
      svg.appendChild(g);
    }
  });
}

function showMapTooltip(mid, e) {
  const m = KO.find(x => x.id === mid);
  if (!m) return;
  const tt = document.getElementById('mapTooltip');
  const hId = resolveSlot(m.h), aId = resolveSlot(m.a);

  let html = `<b>Match ${mid} - ${m.s || ''}</b>`;
  if (hId) {
      const n = TEAMS[hId].n[currentLang] || TEAMS[hId].n.en;
      html += `<div class="map-tooltip-team">${flagImg(hId, 20)} ${n}</div>`;
  }
  if (aId) {
      const n = TEAMS[aId].n[currentLang] || TEAMS[aId].n.en;
      html += `<div class="map-tooltip-team">${flagImg(aId, 20)} ${n}</div>`;
  }

  const sc = scores[mid];
  if (sc) html += `<div style="color:#f1c40f; font-size:18px; margin:5px 0;">${sc.h}:${sc.a}</div>`;
  else html += `<div style="margin:5px 0; opacity:0.6;">vs</div>`;

  html += `<div style="font-size:11px; opacity:0.7;">${tCity(m.v)}<br>${m.d} ${m.t}</div>`;

  tt.innerHTML = html;
  tt.style.display = 'block';

  const move = (ev) => {
    tt.style.left = (ev.clientX + 15) + 'px';
    tt.style.top = (ev.clientY + 15) + 'px';
  };
  move(e);
  e.target.onmousemove = move;
}

function handleMapNodeClick(mid, e) {
  const now = Date.now();
  if (now - mapLastTap < 300) {
    const m = KO.find(x => x.id === mid);
    const win = getWinner(mid) || resolveSlot(m.h) || resolveSlot(m.a);
    if (win) goToTeam(win);
    e.preventDefault();
  } else {
    viewMatchEvents(mid);
  }
  mapLastTap = now;
}
</script>
"""
    body_end = content.find('</body>')
    if body_end != -1:
        content = content[:body_end] + new_js + content[body_end:]

    # 3. Ensure renderMap() is in renderAll()
    if 'renderMap();' not in content:
        content = content.replace('renderStadiums();', 'renderStadiums();renderMap();')

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Injected Map logic.")

if __name__ == "__main__":
    inject()
