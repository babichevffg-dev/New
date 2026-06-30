import re

def fix():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Correct labels for the Map tab
    labels = {
        "ru": "Карта", "en": "Map", "zh": "地图", "es": "Mapa",
        "fr": "Carte", "tr": "Harita", "ar": "الخريطة"
    }

    # We'll search for each language block and specifically replace the "map" key's value.
    # The pattern matches "lang: {" then some content until the end of the object.
    # We use a greedy approach for the block but stop at the next lang.

    langs = ["es", "fr", "tr", "ar", "ru", "en", "zh"]

    for lang in langs:
        # Match from "lang: {" to "}," or "}"
        # Using a lookahead to stop at the next language or end of TRANSLATIONS
        pattern = rf'({lang}:|"{lang}":)\s*\{{(.*?)\n\s+}}'

        match = re.search(pattern, content, re.DOTALL)
        if match:
            block_content = match.group(2)
            # Replace only the "map" key's value in this specific block
            new_block_content = re.sub(r'"map":\s*"[^"]*"', f'"map": "{labels[lang]}"', block_content)

            # Reconstruct the block
            new_full_block = f'{match.group(1)} {{{new_block_content}\n  }}'
            content = content.replace(match.group(0), new_full_block)

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Fixed translations labels with v2.")

if __name__ == "__main__":
    fix()
