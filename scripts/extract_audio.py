#!/usr/bin/env python3
"""One-time: decode embedded-audio base64 from index.html into audio/*.mp3 + manifest.json."""

import base64
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
AUDIO_DIR = os.path.join(ROOT, "audio")
MANIFEST = os.path.join(AUDIO_DIR, "manifest.json")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "x"


def read_block(html, block_id):
    m = re.search(r'<script id="%s"[^>]*>(.*?)</script>' % block_id, html, re.S)
    return m.group(1) if m else None


def main():
    if not os.path.exists(HTML):
        sys.exit(f"Not found: {HTML}")

    html = open(HTML, encoding="utf-8").read()
    raw = read_block(html, "embedded-audio")
    if not raw:
        sys.exit("No embedded-audio block in index.html")

    data = json.loads(raw)
    voices = data.get("voices", [])
    clips = data.get("clips", {})
    if not voices or not clips:
        sys.exit("embedded-audio is empty")

    manifest = {"voices": voices, "clips": {v["id"]: {} for v in voices}}
    total = sum(len(clips.get(v["id"], {})) for v in voices)
    done = 0

    print(f"Extracting {total} clips...")
    for v in voices:
        vid = v["id"]
        vdir = os.path.join(AUDIO_DIR, vid)
        os.makedirs(vdir, exist_ok=True)
        for key, uri in clips.get(vid, {}).items():
            if not uri.startswith("data:audio/mpeg;base64,"):
                sys.exit(f"Unexpected URI for {vid}/{key!r}")
            b64 = uri.split(",", 1)[1]
            mp3 = base64.b64decode(b64)
            fname = slug(key) + ".mp3"
            fpath = os.path.join(vdir, fname)
            open(fpath, "wb").write(mp3)
            manifest["clips"][vid][key] = f"audio/{vid}/{fname}"
            done += 1
            if done % 50 == 0 or done == total:
                print(f"  {done}/{total}")

    open(MANIFEST, "w", encoding="utf-8").write(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Wrote {MANIFEST}")

    new_html = re.sub(
        r'\n?<!-- ============ EMBEDDED PREMIUM AUDIO.*?-->.*?<script id="embedded-audio"[^>]*>.*?</script>\n?',
        "\n",
        html,
        count=1,
        flags=re.S,
    )
    if new_html == html:
        sys.exit("Could not remove embedded-audio block")

    open(HTML, "w", encoding="utf-8").write(new_html)
    mb = os.path.getsize(HTML) / 1_048_576
    print(f"Stripped blob from index.html ({mb:.2f} MB)")


if __name__ == "__main__":
    main()
