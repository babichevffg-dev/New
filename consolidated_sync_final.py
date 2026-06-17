import json
import re
import os
import difflib

def clean_text(text):
    if not isinstance(text, str): return ""

    # meta keywords to remove the entire sentence
    meta_keywords = [
        "ошибочно указан", "ошибочно указана", "ошибочно отнесен", "erroneously listed",
        "mistakenly listed", "erroneous surname", "erroneous name", "в файле указан",
        "в реальности", "in reality", "en réalité", "en realidad", "事实上",
        "according to FIFA", "согласно ФИФА", "FIFA registries", "реестрам ФИФА",
        "Listed in the file as", "В файле ошибочно", "В файле указана", "The file contains",
        "В файле указана ошибочная фамилия", "The file contains an erroneous surname",
        "El archivo contiene un apellido erróneo", "Le fichier contient un nom de famille erroné",
        "文件中包含错误的姓氏"
    ]

    # Split into sentences using lookbehind for period/bang/question followed by space
    sentences = re.split(r'(?<=[.!?])\s+', text)
    filtered_sentences = []
    for s in sentences:
        if not any(kw.lower() in s.lower() for kw in meta_keywords):
            filtered_sentences.append(s.strip())

    new_text = " ".join(filtered_sentences)

    # patterns to remove fragments
    patterns_to_remove = [
        r"(Этот игрок|Данный игрок|В файле|Игрок).*?(ошибочно|указан|отнесен).*?(сборной|команде|как).*?(\.\s*|$)",
        r"(This player|The player).*?(erroneously|mistakenly|listed|under).*?(team|file).*?(\.\s*|$)",
        r"(En realidad|In reality|В реальности|事实上).*?(él|he|он|他).*?(\.\s*|$)",
        r"(Согласно|According to|Selon|Según|根据).*?(реестрам|registries|registres|registros|登记).*?(\.\s*|$)",
        r"(In the file an|The file contains an|В файле).*?erroneous.*?(surname|name|фамилия).*?(\.\s*|$)",
        r"Listed in the file as.*?(\.\s*|$)",
        r"Erroneously listed as.*?(\.\s*|$)",
        r"В файле ошибочно указан как тренер Ирака.*?(\.\s*|$)",
        r"тренер Ирака.*?(\.\s*|$)",
        r"coach of Iraq.*?(\.\s*|$)"
    ]

    for pattern in patterns_to_remove:
        new_text = re.sub(pattern, "", new_text, flags=re.IGNORECASE | re.DOTALL)

    new_text = new_text.strip().strip('"').strip()
    new_text = re.sub(r'\s+', ' ', new_text)
    new_text = re.sub(r'^[\.,\s]+', '', new_text)
    new_text = re.sub(r'[\.,\s]+$', '.', new_text)

    return new_text

def extract_langs(text):
    res = {}
    for lang in ["ru", "en", "es", "fr", "zh"]:
        m = re.search(fr'"{lang}":\s*("(.*?)"|([^"\s,][^,}}]*))', text, re.DOTALL)
        if m:
            val = m.group(2) if m.group(2) is not None else m.group(3)
            res[lang] = clean_text(val)
    return res

def process_file(filepath):
    if not os.path.exists(filepath): return []
    content = open(filepath, "r", encoding="utf-8").read()
    extracted = []

    team_blocks = re.findall(r'"([A-Z]{3})":\s*\{(.*?)\n\s*\}', content, re.DOTALL)
    for tid, block in team_blocks:
        objs = re.findall(r'\{[^{}]*"name":\s*\{[^{}]*\}.*?"story":\s*\{[^{}]*\}[^{}]*\}', block, re.DOTALL)
        for obj in objs:
            n_part = re.search(r'"name":\s*(\{[^{}]*\})', obj, re.DOTALL)
            s_part = re.search(r'"story":\s*(\{[^{}]*\})', obj, re.DOTALL)
            pos_m = re.search(r'"pos":\s*"([^"]+)"', obj)
            if n_part and s_part:
                names = extract_langs(n_part.group(1))
                stories = extract_langs(s_part.group(1))
                pos = pos_m.group(1).lower() if pos_m else "player"
                if names.get("en"):
                    extracted.append({"name": names["en"], "pos": pos, "team": tid, "story": stories})

    global_objs = re.findall(r'\{[^{}]*"name":\s*\{[^{}]*\}.*?"story":\s*\{[^{}]*\}[^{}]*\}', content, re.DOTALL)
    for obj in global_objs:
        n_part = re.search(r'"name":\s*(\{[^{}]*\})', obj, re.DOTALL)
        s_part = re.search(r'"story":\s*(\{[^{}]*\})', obj, re.DOTALL)
        pos_m = re.search(r'"pos":\s*"([^"]+)"', obj)
        if n_part and s_part:
            names = extract_langs(n_part.group(1))
            stories = extract_langs(s_part.group(1))
            pos = pos_m.group(1).lower() if pos_m else "player"
            if names.get("en"):
                if not any(e["name"] == names["en"] and e["pos"] == pos and e["story"] == stories for e in extracted):
                    extracted.append({"name": names["en"], "pos": pos, "team": None, "story": stories})
    return extracted

source_files = ["Точное описание .txt", "Точное описание финал.txt", "Суперфинал.txt"]
all_source = []
for f in source_files: all_source.extend(process_file(f))

def normalize(s):
    if not s: return ""
    return " ".join(s.lower().replace("-", " ").replace(".", " ").split())

def update_squads(squads):
    updated = 0
    for tid, tdata in squads.items():
        personnel = []
        if "players" in tdata:
            for p in tdata["players"]: personnel.append((p, "player"))
        if "coaches" in tdata:
            for c in tdata["coaches"]: personnel.append((c, "coach"))

        for p, p_type in personnel:
            name_en = normalize(p["name"]["en"])
            p_pos = p.get("pos", "").lower().strip()
            best_match = None
            for s in all_source:
                if s["team"] == tid and normalize(s["name"]) == name_en and s["pos"] == p_pos:
                    best_match = s["story"]
                    break
            if not best_match:
                for s in all_source:
                    if s["team"] == tid and normalize(s["name"]) == name_en:
                        best_match = s["story"]
                        break
            if not best_match:
                for s in all_source:
                    if normalize(s["name"]) == name_en and s["pos"] == p_pos:
                        best_match = s["story"]
                        break
            if not best_match:
                for s in all_source:
                    if difflib.SequenceMatcher(None, normalize(s["name"]), name_en).ratio() > 0.9:
                        best_match = s["story"]
                        break

            if best_match:
                if best_match.get("en") and best_match["en"].lower() != p["name"]["en"].lower():
                    p["story"] = best_match
                    p["isPrecise"] = True
                    updated += 1
                else:
                    p["story"] = {l: "" for l in ["ru", "en", "es", "fr", "zh"]}
                    p["isPrecise"] = False
    return updated

results = json.load(open("results.json", "r", encoding="utf-8"))
cnt = update_squads(results["squads"])
json.dump(results, open("results.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

html = open("index.html", "r", encoding="utf-8").read()
m = re.search(r'let SQUADS = (\{.*?\});', html, re.DOTALL)
if m:
    data = json.loads(m.group(1))
    update_squads(data)
    new_json = json.dumps(data, ensure_ascii=False, indent=2)
    html = html.replace(m.group(1), new_json)
    open("index.html", "w", encoding="utf-8").write(html)
