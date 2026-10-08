import re
from pathlib import Path

M3U = Path("playlist.m3u")
JS = Path("playlist.js")

text = M3U.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")

blocks = re.split(r"(?=^#EXTINF:)", text, flags=re.MULTILINE)
source = {}

for block in blocks:
    if not block.startswith("#EXTINF:"):
        continue

    lines = block.splitlines()
    extinf = lines[0]
    name = extinf.rsplit(",", 1)[-1].strip()

    group = re.search(r'group-title="([^"]*)"', extinf, re.IGNORECASE)
    group_name = group.group(1).strip() if group else ""

    if "Sự Kiện TV360" not in group_name and "Sự Kiện FPT PLAY" not in group_name:
        continue

    urls = [
        line.strip()
        for line in lines[1:]
        if line.strip() and not line.startswith("#")
    ]
    if not urls:
        continue

    logo = re.search(r'tvg-logo="([^"]*)"', extinf, re.IGNORECASE)

    source[name] = {
        "url": urls[-1],
        "logo": logo.group(1) if logo else "",
    }

# Web playlist intentionally contains only THVL1 and TV360+10
target_names = {"THVL1", "TV360+10"}

for name in target_names:
    if name not in source:
        print(f"Source channel not found: {name}")

def update_array(js_text, array_name, allowed_names):
    pattern = re.compile(
        rf'("{re.escape(array_name)}"\s*:\s*\[)(.*?)(\n\s*\])',
        re.DOTALL,
    )
    match = pattern.search(js_text)
    if not match:
        raise RuntimeError(f"Could not locate {array_name} array in playlist.js.")

    body = match.group(2)

    entry_re = re.compile(
        r'\s*\{\s*"name":\s*"([^"]*)",\s*"short":\s*"([^"]*)",'
        r'\s*"logo":\s*"([^"]*)",\s*"url":\s*"([^"]*)"\s*\},?'
    )

    entries = [
        {
            "name": m.group(1),
            "short": m.group(2),
            "logo": m.group(3),
            "url": m.group(4),
        }
        for m in entry_re.finditer(body)
    ]

    for entry in entries:
        name = entry["name"]
        if name not in allowed_names or name not in source:
            continue

        entry["url"] = source[name]["url"]

        # Keep the existing web logo; only fill it from VMT if missing.
        if not entry["logo"]:
            entry["logo"] = source[name]["logo"]

    def render(e):
        return (
            f'    {{ "name": "{e["name"]}", "short": "{e["short"]}", '
            f'"logo": "{e["logo"]}", "url": "{e["url"]}" }}'
        )

    new_body = ",\n".join(render(e) for e in entries)
    return js_text[:match.start(2)] + "\n" + new_body + js_text[match.end(2):]

js = update_array(js, "FPT", {"THVL1"})
js = update_array(js, "TV360", {"TV360+10"})

JS.write_text(js, encoding="utf-8")

print("Synced THVL1 and TV360+10 from VMT.")
