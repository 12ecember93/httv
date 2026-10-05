import re
import urllib.request
from pathlib import Path

SOURCE = "https://raw.githubusercontent.com/vuminhthanh12/vuminhthanh12/refs/heads/main/vmttv"
OUTPUT = Path("playlist.m3u")

req = urllib.request.Request(
    SOURCE,
    headers={"User-Agent": "Mozilla/5.0"}
)
with urllib.request.urlopen(req, timeout=60) as r:
    text = r.read().decode("utf-8-sig", errors="replace")

lines = text.splitlines()
blocks = []
current = None

for line in lines:
    if line.startswith("#EXTINF:"):
        if current:
            blocks.append(current)
        current = [line]
    elif current is not None:
        current.append(line)

if current:
    blocks.append(current)

wanted = re.compile(
    r"^(VTV(?:[1-9]|10)|HTV(?:3|7|9)|THVL1(?:\s*-.*)?|Vietnam Today|On Sports(?: \+)?(?: 50fps)?)$",
    re.IGNORECASE
)
fpt_group = re.compile(r'Sự Kiện FPT PLAY', re.IGNORECASE)
tv360_group = re.compile(r'Sự Kiện TV360', re.IGNORECASE)
onsports = re.compile(r'^On Sports(?: 50fps)?$', re.IGNORECASE)

selected = []

for block in blocks:
    extinf = block[0]

    # Channel name is the text after the final comma in #EXTINF.
    name = extinf.rsplit(",", 1)[-1].strip()
    group = re.search(r'group-title="([^"]*)"', extinf, re.IGNORECASE)
    group_name = group.group(1).strip() if group else ""

    keep = (
        bool(wanted.fullmatch(name))
        or bool(fpt_group.search(group_name))
        or bool(tv360_group.search(group_name))
        or bool(onsports.fullmatch(name))
    )

    if keep:
        selected.append(block)

if not selected:
    raise RuntimeError("No channels matched. Refusing to overwrite playlist.m3u.")

header = "#EXTM3U url-tvg=\"https://lichphatsong.io.vn/epg.xml\"\n"
output = header + "\n".join("\n".join(block) for block in selected) + "\n"
OUTPUT.write_text(output, encoding="utf-8")

print(f"Selected {len(selected)} channels/entries.")
for block in selected:
    print(" -", block[0].rsplit(",", 1)[-1].strip())
