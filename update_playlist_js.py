import re
from pathlib import Path

M3U = Path("playlist.m3u")
JS = Path("playlist.js")

text = M3U.read_text(encoding="utf-8")
js = JS.read_text(encoding="utf-8")

blocks = re.split(r"(?=^#EXTINF:)", text, flags=re.MULTILINE)
source = {}
fpt_index = 0

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

        if "Sự Kiện FPT PLAY" in group_name:
            fpt_index += 1
            short = f"FPT{fpt_index}"
        else:
            short = name

        source[name] = {
            "url": urls[-1],
            "logo": logo.group(1) if logo else "",
            "short": short,
        }

# Only rebuild Others. VTV and every non-TV360/FPT entry remain unchanged.
others_match = re.search(r'("Others"\s*:\s*\[)(.*?)(\n\s*\])', js, re.DOTALL)
if not others_match:
    raise RuntimeError("Could not locate Others array in playlist.js.")

body = others_match.group(2)

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

def is_target(name):
    return (
        name.startswith("TV360+")
        or name == "TV360 Promo"
        or name.startswith("Sự Kiện FPT")
        or name.startswith("Event ")
        or name.startswith("Sự Kiện ")
    )

result = []
used = set()

for entry in entries:
    name = entry["name"]

    if not is_target(name):
        result.append(entry)
        continue

    if name in source:
        entry["url"] = source[name]["url"]
        used.add(name)
        result.append(entry)
    # Old TV360/FPT entries that disappeared from playlist.m3u are removed.

for name, item in source.items():
    if name not in used:
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

new_body = ",\n".join(render(e) for e in result)
new_js = js[:others_match.start(2)] + "\n" + new_body + js[others_match.end(2):]
JS.write_text(new_js, encoding="utf-8")

print(f"Synced {len(source)} TV360/FPT entries in playlist.js.")
