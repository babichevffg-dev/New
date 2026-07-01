import re

def run():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # The buildUI function is clearly double-defined or corrupted
    # because I see duplicate loops and mismatched braces.

    # 1. Clean up buildUI
    new_build_ui = """
function buildUI(){
  const T = TRANSLATIONS[currentLang] || TRANSLATIONS.ru;
  document.getElementById('txt-title').textContent = T.title;
  document.getElementById('txt-subtitle').textContent = T.subtitle;
  document.getElementById('txt-design').textContent = T.design;
  document.getElementById('btnSave').innerHTML = T.save;
  document.getElementById('btnExport').textContent = T.export;
  document.getElementById('btnImport').textContent = T.import;
  document.getElementById('btnReset').textContent = T.reset;
  document.getElementById('adminTrigger').textContent = T.admin_mode;

  const evTitle = document.getElementById('eventsModalTitle');
  if (evTitle) evTitle.textContent = T.match_events || 'Match Events';

  const tabs=[T.groups, T.tables, T.thirds, T.calendar, T.knockout, T.bracket, T.teams, T.stadiums, T.map];
  const tabEl=document.getElementById('tabs');
  const panels=document.getElementById('panels');
  tabEl.innerHTML=''; panels.innerHTML='';

  tabs.forEach((t,i)=>{
    const b=document.createElement('button');
    b.className='tab' + (i === activeTab ? ' active' : '');
    b.textContent=t; b.dataset.tab=i;
    b.onclick=()=>{
      activeTab=i;
      document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
      b.classList.add('active');
      const p=document.getElementById('panel'+i);
      if(p) {
        p.classList.add('active');
        if(i===8) { renderMap(); setTimeout(drawBracketLines, 100); }
      }
    };
    tabEl.appendChild(b);

    const p=document.createElement('div');
    p.className='panel' + (i === activeTab ? ' active' : '');
    p.id='panel'+i;
    panels.appendChild(p);
  });
  if(activeTab === 8) { renderMap(); setTimeout(drawBracketLines, 200); }
}
"""
    # Replace the corrupted block
    # Match from first function buildUI to renderGroups
    pattern = r'function buildUI\(\)\{.*?function renderGroups\(\)\{'
    content = re.sub(pattern, new_build_ui + '\n\nfunction renderGroups(){', content, flags=re.DOTALL)

    # 2. Fix Russian "map" key if Arabic leaked in
    content = re.sub(r'ru:\s*\{\s*"map_hint":\s*"[^"]*",\s*"map":\s*"[^"]*"',
                     'ru: {\n    "map_hint": "Двойной клик — переход к команде",\n    "map": "Карта"', content)

    # 3. Clean all occurrences of map functions to ensure no duplicates
    def remove_func(name, text):
        pattern = rf'function {name}\s*\(.*?\)\s*\{{(?:[^{{}}]*|\{{(?:[^{{}}]*|\{{[^{{}}]*\}})*\}})*\}}'
        return re.sub(pattern, '', text, flags=re.DOTALL)

    for fn in ['renderMap', 'drawBracketLines', 'showMapTooltip', 'handleMapNodeClick']:
        content = remove_func(fn, content)

    # 4. Correct unified map functions
    map_js = """
let mapLastTap = 0;
function renderMap() {
  const container = document.getElementById('panel8');
  if (!container) return;
  const T = TRANSLATIONS[currentLang] || {};
  container.innerHTML = `
    <div class="map-outer-container">
      <div class="map-hint-text">${T.map_hint || ''}</div>
      <div class="bracket-wrapper" id="bracketWrapper">
        <svg class="bracket-svg-layer" id="bracketSvg"></svg>
        <div class="bracket-column" id="col-L1"></div>
        <div class="bracket-column" id="col-L2"></div>
        <div class="bracket-column" id="col-L3"></div>
        <div class="bracket-column" id="col-L4"></div>
        <div class="bracket-center">
            <div class="bracket-logo-box"><img src="https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/2026_FIFA_World_Cup_logo.svg/1200px-2026_FIFA_World_Cup_logo.svg.png" style="height:120px"></div>
            <h1 class="bracket-title-neon">ПЛЕЙ-ОФФ</h1>
            <h2 class="bracket-subtitle-neon">ЧМ 2026</h2>
            <div id="node-M101-box" style="margin-bottom: 20px;"></div>
            <img src="https://img.freepik.com/premium-vector/gold-trophy-cup-with-garland-victory-champion-winner-concept-hand-drawn-vector-illustration_501069-1383.jpg" class="bracket-trophy-main">
            <div id="node-M104-box" style="margin-top: 30px;"></div>
            <div id="node-M102-box" style="margin-top: 30px;"></div>
        </div>
        <div class="bracket-column" id="col-R4"></div>
        <div class="bracket-column" id="col-R3"></div>
        <div class="bracket-column" id="col-R2"></div>
        <div class="bracket-column" id="col-R1"></div>
      </div>
    </div>
    <div id="mapTooltip" class="map-tooltip"></div>
  `;
  const createNode = (id, teamId, mIdNum, targetId, isFinal=false) => {
    const target = document.getElementById(targetId);
    if (!target) return;
    const mId = 'M' + mIdNum;
    const winnerId = getWinner(mId);
    const effectiveTeamId = teamId || winnerId;
    const node = document.createElement('div');
    node.className = 'bracket-node' + (effectiveTeamId && TEAMS[effectiveTeamId] ? '' : ' empty') + (isFinal ? ' final-node' : '');
    node.id = 'node-' + id;
    node.onclick = () => (effectiveTeamId && TEAMS[effectiveTeamId]) ? goToTeam(effectiveTeamId) : openMatchEvents(mId);
    node.onmouseenter = (e) => {
        const tt = document.getElementById('mapTooltip');
        if(!tt) return;
        if (effectiveTeamId && TEAMS[effectiveTeamId]) {
            const t = TEAMS[effectiveTeamId];
            const name = typeof t.n === 'object' ? (t.n[currentLang] || t.n.en) : t.n;
            tt.innerHTML = `<div class="map-tooltip-team">${flagImg(effectiveTeamId)} ${name}</div>`;
        } else {
            const m = KO.find(x => x.id === mId);
            const hId = m ? resolveSlot(m.h) : null, aId = m ? resolveSlot(m.a) : null;
            const hN = (hId && TEAMS[hId]) ? (TEAMS[hId].n[currentLang] || TEAMS[hId].n.en) : slotLabel(m ? m.h : '?');
            const aN = (aId && TEAMS[aId]) ? (TEAMS[aId].n[currentLang] || TEAMS[aId].n.en) : slotLabel(m ? m.a : '?');
            tt.innerHTML = `<b>Match ${mId}</b><br>${hN} vs ${aN}`;
        }
        tt.style.display = 'block';
    };
    node.onmousemove = (e) => {
        const tt = document.getElementById('mapTooltip');
        if(tt) { tt.style.left = (e.clientX + 15) + 'px'; tt.style.top = (e.clientY + 15) + 'px'; }
    };
    node.onmouseleave = () => { const tt = document.getElementById('mapTooltip'); if(tt) tt.style.display='none'; };
    if (effectiveTeamId && TEAMS[effectiveTeamId]) {
        const t = TEAMS[effectiveTeamId];
        node.innerHTML = `<img src="${t.f}" class="bracket-flag"><span class="bracket-name">${t.n[currentLang] || t.n.en}</span>`;
        if(!isFinal) {
            const sc = scores[mId];
            if(sc && sc.h !== undefined && sc.h !== null) node.innerHTML += `<span class="bracket-score">${sc.h}:${sc.a}</span>`;
        }
    } else {
        node.innerHTML = `<span class="bracket-name" style="opacity:0.3;margin:auto">Match ${mIdNum}</span>`;
    }
    target.appendChild(node);
  };
  const leftR32 = [74, 77, 73, 75, 79, 80, 76, 78], rightR32 = [81, 82, 85, 87, 86, 88, 83, 84];
  leftR32.forEach(m => {
    const obj = KO.find(x => x.id === 'M'+m) || {h:'?', a:'?'};
    createNode('M'+m+'-H', resolveSlot(obj.h), m, 'col-L1');
    createNode('M'+m+'-A', resolveSlot(obj.a), m, 'col-L1');
    createNode('W'+m, getWinner('M'+m), m, 'col-L2');
  });
  rightR32.forEach(m => {
    const obj = KO.find(x => x.id === 'M'+m) || {h:'?', a:'?'};
    createNode('M'+m+'-H', resolveSlot(obj.h), m, 'col-R1');
    createNode('M'+m+'-A', resolveSlot(obj.a), m, 'col-R1');
    createNode('W'+m, getWinner('M'+m), m, 'col-R2');
  });
  [89, 90, 92, 91].forEach(m => createNode('W'+m, getWinner('M'+m), m, 'col-L3'));
  [94, 96, 95, 93].forEach(m => createNode('W'+m, getWinner('M'+m), m, 'col-R3'));
  [97, 99].forEach(m => createNode('W'+m, getWinner('M'+m), m, 'col-L4'));
  [98, 100].forEach(m => createNode('W'+m, getWinner('M'+m), m, 'col-R4'));
  createNode('W101', getWinner('M101'), 101, 'node-M101-box');
  createNode('W102', getWinner('M102'), 102, 'node-M102-box');
  createNode('W104', getWinner('M104'), 104, 'node-M104-box', true);
  setTimeout(drawBracketLines, 100);
}

function drawBracketLines() {
    const svg = document.getElementById('bracketSvg');
    if(!svg) return;
    svg.innerHTML = '';
    const wrapper = document.getElementById('bracketWrapper');
    if(!wrapper) return;
    const wRect = wrapper.getBoundingClientRect();
    const connect = (id1, id2, side) => {
        const el1 = document.getElementById('node-' + id1), el2 = document.getElementById('node-' + id2);
        if(!el1 || !el2) return;
        const r1 = el1.getBoundingClientRect(), r2 = el2.getBoundingClientRect();
        let x1, x2;
        if (side === 'left') { x1 = r1.right; x2 = r2.left; }
        else if (side === 'right') { x1 = r1.left; x2 = r2.right; }
        else { x1 = (r1.left + r1.right)/2; x2 = (r2.left + r2.right)/2; }
        x1 -= wRect.left; x2 -= wRect.left;
        const y1 = (r1.top + r1.bottom) / 2 - wRect.top, y2 = (r2.top + r2.bottom) / 2 - wRect.top;
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        const midX = (x1 + x2) / 2;
        path.setAttribute("d", `M ${x1} ${y1} L ${midX} ${y1} L ${midX} ${y2} L ${x2} ${y2}`);
        path.setAttribute("class", "bracket-line");
        if (!el1.classList.contains('empty') && !el2.classList.contains('empty')) path.classList.add('active');
        svg.appendChild(path);
    };
    const leftR32 = [74, 77, 73, 75, 79, 80, 76, 78], rightR32 = [81, 82, 85, 87, 86, 88, 83, 84];
    leftR32.forEach(m => { connect('M'+m+'-H', 'W'+m, 'left'); connect('M'+m+'-A', 'W'+m, 'left'); });
    rightR32.forEach(m => { connect('M'+m+'-H', 'W'+m, 'right'); connect('M'+m+'-A', 'W'+m, 'right'); });
    [['W74','W89'],['W77','W89'],['W73','W90'],['W75','W90'],['W79','W92'],['W80','W92'],['W76','W91'],['W78','W91']].forEach(p=>connect(p[0],p[1],'left'));
    [['W81','W94'],['W82','W94'],['W85','W96'],['W87','W96'],['W86','W95'],['W88','W95'],['W83','W93'],['W84','W93']].forEach(p=>connect(p[0],p[1],'right'));
    [['W89','W97'],['W90','W97'],['W92','W99'],['W91','W99']].forEach(p=>connect(p[0],p[1],'left'));
    [['W94','W98'],['W96','W98'],['W95','W100'],['W93','W100']].forEach(p=>connect(p[0],p[1],'right'));
    connect('W97','W101','left'); connect('W98','W101','right');
    connect('W99','W102','left'); connect('W100','W102','right');
    connect('W101','W104','center'); connect('W102','W104','center');
}
"""
    # 5. Inject at the end of the script tag
    script_end = content.rfind('</script>')
    content = content[:script_end] + map_js + "\n" + content[script_end:]

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Surgical cleanup and fix applied.")

if __name__ == "__main__":
    run()
