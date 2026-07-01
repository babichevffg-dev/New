import re

def fix():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # The user says "Map" is empty.
    # 1. Check if panel8 is being rendered in buildUI
    # 2. Check if renderMap is called correctly.

    # buildUI creates panel0 to panel8 (if tabs has 9 elements).
    # tabs=[T.groups, T.tables, T.thirds, T.calendar, T.knockout, T.bracket, T.teams, T.stadiums, T.map] (9 elements)
    # The panels loop:
    # tabs.forEach((t,i)=>{
    #   ...
    #   p.id='panel'+i; panels.appendChild(p);
    # });
    # So panel8 should exist.

    # 3. Simplify and fix renderMap and buildUI once more.

    new_build_ui = """
function buildUI(){
  const T = TRANSLATIONS[currentLang];
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
}
"""

    new_render_all = """
function renderAll(){
  const ae=document.activeElement;
  const fid=ae&&ae.dataset?ae.dataset.id:null;
  const fside=ae&&ae.dataset?ae.dataset.side:null;
  const selStart=ae&&ae.selectionStart!=null?ae.selectionStart:null;
  renderGroups();renderTables();renderThird();renderCalendar();renderKnockout();renderBracket();renderTeams();renderStadiums();
  if(activeTab === 8) renderMap();
  bindInputs();
  if(fid){
    const inp=document.querySelector('input.score-inp[data-id="'+fid+'"][data-side="'+fside+'"]');
    if(inp){inp.focus();if(selStart!=null)try{inp.setSelectionRange(selStart,selStart)}catch(e){}}
  }
}
"""

    # Replace buildUI
    content = re.sub(r'function buildUI\(\)\{.*?\}', new_build_ui, content, flags=re.DOTALL)

    # Replace renderAll
    content = re.sub(r'function renderAll\(\)\{.*?\}', new_render_all, content, flags=re.DOTALL)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed buildUI and renderAll v7.")

if __name__ == "__main__":
    fix()
