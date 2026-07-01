import re

def fix():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Labels to update (Карта/Map)
    labels = {
        "ru": "Карта", "en": "Map", "zh": "地图", "es": "Mapa",
        "fr": "Carte", "tr": "Harita", "ar": "الخريطة"
    }

    for lang, label in labels.items():
        # Using a more robust pattern to find the language block and then "map"
        block_pattern = rf'({lang}:|"{lang}":)\s*\{{(.*?)\n\s+}}'
        match = re.search(block_pattern, content, re.DOTALL)
        if match:
            block_content = match.group(2)
            # Find and replace "map" value within this block
            new_block_content = re.sub(r'"map":\s*"[^"]*"', f'"map": "{label}"', block_content)

            # Reconstruct the block
            new_full_block = f'{match.group(1)} {{{new_block_content}\n  }}'
            content = content.replace(match.group(0), new_full_block)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed labels successfully.")

if __name__ == "__main__":
    fix()
