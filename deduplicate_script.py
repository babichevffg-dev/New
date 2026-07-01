import re

def deduplicate():
    with open('index.html', 'r', encoding='utf-8') as f:
        content = f.read()

    # Remove all occurrences of let mapLastTap = 0;
    content = re.sub(r'let mapLastTap\s*=\s*0;?', '', content)

    # Inject it once at the top of the main script block
    # Main script block starts at line 989 approximately
    content = content.replace('let activeTab=0;', 'let activeTab=0;\nlet mapLastTap = 0;')

    # Find all function renderMap() { ... } and keep only the last one
    # This is tricky in a huge file.
    # Let's find all function headers and their positions

    def get_function_blocks(name, text):
        blocks = []
        for m in re.finditer(rf'function {name}\s*\(.*?\)\s*\{{', text):
            start = m.start()
            # find matching brace
            count = 1
            curr = text.find('{', start) + 1
            while count > 0 and curr < len(text):
                if text[curr] == '{': count += 1
                elif text[curr] == '}': count -= 1
                curr += 1
            blocks.append((start, curr))
        return blocks

    for func in ['renderMap', 'drawBracketLines', 'showMapTooltip', 'handleMapNodeClick']:
        blocks = get_function_blocks(func, content)
        if len(blocks) > 1:
            print(f"Found {len(blocks)} copies of {func}. Removing all but last.")
            # Remove all but the last one, from back to front to keep indices valid
            for i in range(len(blocks) - 2, -1, -1):
                s, e = blocks[i]
                content = content[:s] + content[e:]

    # Also check for viewMatchEvents duplicate
    blocks = get_function_blocks('viewMatchEvents', content)
    if len(blocks) > 1:
        for i in range(len(blocks) - 2, -1, -1):
            s, e = blocks[i]
            content = content[:s] + content[e:]

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Deduplication complete.")

if __name__ == "__main__":
    deduplicate()
