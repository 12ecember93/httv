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

    extinf = block.splitlines()[0]
    name = extinf.rsplit(",", 1)[-1].strip()
    group = re.search(r'group-title="([^"]*)"', extinf, re.IGNORECASE)
    group_name = group.group(1).strip() if group else ""

    if "Sự Kiện TV360" in group_name or "Sự Kiện FPT PLAY" in group_name:
        urls = [
            line.strip()
            for line in block.splitlines()[1:]
            if line.strip() and not line.startswith("#")
        ]
        if not urls:
            continue

        logo = re.search(r'tvg-logo="([^"]*)"', extinf, re.IGNORECASE)
        source[name] = {
            "url": urls[-1],
            "logo": logo.group(1) if logo else "",
            "short": f"FPT{len(source) + 1}" if "FPT" in group_name else name,
        }

# Split only the Others array. Everything else, especially VTV, stays byte-for-byte unchanged.
others_match = re.search(r'("Others"\\s*:\\s*\\[)(.*?)(\\n\\s*\\])', js, re.DOTALL)
if not others_match:
    raise RuntimeError("Could not locate Others array in playlist.js.")

prefix, body, suffix = others_match.groups()

entry_re = re.compile(
    r'\\s*\\{\\s*"name":\\s*"([^"]*)",\\s*"short":\\s*"([^"]*)",'
    r'\\s*"logo":\\s*"([^"]*)",\\s*"url":\\s*"([^"]*)"\\s*\\},?'
)

entries = []
for m in entry_re.finditer(body):
    entries.append({
        "name": m.group(1),
        "short": m.group(2),
        "logo": m.group(3),
        "url": m.group(4),
    })

target = lambda name: name.startswith("TV360+") or name == "TV360 Promo" or name.startswith("Sự Kiện FPT") or name.startswith("Event ") or name.startswith("Sự Kiện ")

result = []
used = set()

for entry in entries:
    name = entry["name"]

    if not target(name):
        result.append(entry)
        continue

    if name in source:
        entry["url"] = source[name]["url"]
        used.add(name)
        result.append(entry)

# Add newly appeared TV360/FPT entries from playlist.m3u.
for name, item in source.items():
    if name in used:
        continue
    result.append({
        "name": name,
        "short": item["short"],
        "logo": item["logo"],
        "url": item["url"],
    })

def render(e):
    return (
        f'    {{ "name": "{e["name"]}", "short": "{e["short"]}", '
        f'"logo": "{e["logo"]}", "url": "{e["url"]}" }}'
    )

new_body = ",\\n".join(render(e) for e in result)
new_js = js[:others_match.start(2)] + "\\n" + new_body + js[others_match.end(2):]
JS.write_text(new_js, encoding="utf-8")

print(f"Synced {len(source)} TV360/FPT entries in playlist.js.")
