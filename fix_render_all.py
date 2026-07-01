import re

def run():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the renderAll function and clean it up
    pattern = r'function renderAll\(\)\{.*?bindInputs\(\);'
    replacement = """function renderAll(){
  const ae=document.activeElement;
  const fid=ae&&ae.dataset?ae.dataset.id:null;
  const fside=ae&&ae.dataset?ae.dataset.side:null;
  const selStart=ae&&ae.selectionStart!=null?ae.selectionStart:null;
  renderGroups();renderTables();renderThird();renderCalendar();renderKnockout();renderBracket();renderTeams();renderStadiums();
  if(activeTab === 8) renderMap();
  bindInputs();"""

    content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Also fix the trailing garbage seen in sed output
    # "}\ncatch(e){}}\n  }\n}\n"
    content = re.sub(r'bindInputs\(\);\s*if\(fid\)\{.*?\}\s*\}\s*catch\(e\)\{\}\}\s*\}\s*\}',
                     'bindInputs();\n  if(fid){\n    const inp=document.querySelector(\'input.score-inp[data-id="\'+fid+\'"][data-side="\'+fside+\'"]\');\n    if(inp){inp.focus();if(selStart!=null)try{inp.setSelectionRange(selStart,selStart)}catch(e){}}\n  }\n}',
                     content, flags=re.DOTALL)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == "__main__":
    run()
