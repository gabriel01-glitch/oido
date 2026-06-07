#!/usr/bin/env python3
import json, os, re, sys, time, urllib.error, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "index.html")
AUDIO_DIR = os.path.join(ROOT, "audio")
MANIFEST = os.path.join(AUDIO_DIR, "manifest.json")
CACHE = os.path.join(ROOT, "audio_cache")
VOICES = {"nova": ("f", "Nova"), "onyx": ("m", "Onyx")}
MODEL, FORMAT = "tts-1-hd", "mp3"
SYNTH_SENTENCES = True

def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_") or "x"

def read_block(html, block_id):
    m = re.search(r'<script id="%s"[^>]*>(.*?)</script>' % block_id, html, re.S)
    return m.group(1) if m else None

def load_manifest():
    return json.load(open(MANIFEST, encoding="utf-8")) if os.path.exists(MANIFEST) else {"voices": [], "clips": {}}

def save_manifest(manifest):
    os.makedirs(AUDIO_DIR, exist_ok=True)
    json.dump(manifest, open(MANIFEST, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

def collect_clips_needed(html):
    curr = json.loads(read_block(html, "curriculum"))
    needed = {}
    def add(text):
        if text: needed[text] = text
    for sec in curr["sections"]:
        for pair in sec["pairs"]:
            for side in ("left", "right"):
                it = pair[side]
                add(it.get("speakAs") or it["word"])
                add(it.get("exEn"))
    add(curr["testPhrase"])
    wotd_raw = read_block(html, "word-of-day")
    if wotd_raw:
        try:
            wotd = json.loads(wotd_raw)
            for level in wotd.get("levels", {}).values():
                for w in level:
                    add(w.get("speakAs") or w.get("word"))
                    if SYNTH_SENTENCES: add(w.get("exEn"))
                    if "verb" in w:
                        for f in w["verb"].get("forms", []):
                            add(f.get("speakAs") or f.get("word"))
        except Exception as e:
            print(f"  warn word-of-day: {e}")
    phrasal_raw = read_block(html, "phrasal-verbs")
    if phrasal_raw:
        try:
            phrasal = json.loads(phrasal_raw)
            for group in phrasal.get("groups", []):
                for v in group.get("verbs", []):
                    add(v.get("verb"))
                    for ok in v.get("ok", []): add(ok)
                    if SYNTH_SENTENCES: add(v.get("exEn"))
        except Exception as e:
            print(f"  warn phrasal: {e}")
    return needed

def existing_keys(manifest):
    out = set()
    for voice_clips in manifest.get("clips", {}).values():
        out.update(voice_clips.keys())
    return out

def tts(api_key, voice, text):
    cdir = os.path.join(CACHE, voice); os.makedirs(cdir, exist_ok=True)
    cpath = os.path.join(cdir, slug(text) + "." + FORMAT)
    if os.path.exists(cpath) and os.path.getsize(cpath) > 0:
        return open(cpath, "rb").read()
    body = json.dumps({"model": MODEL, "voice": voice, "input": text, "response_format": FORMAT, "speed": 0.95}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/audio/speech", data=body,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = r.read()
            open(cpath, "wb").write(data); return data
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors="ignore")
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(2 * (attempt + 1)); continue
            sys.exit(f"OpenAI error {e.code}: {msg}")
        except Exception as e:
            if attempt < 3: time.sleep(2 * (attempt + 1)); continue
            sys.exit(f"Network error: {e}")

def verify():
    manifest = load_manifest()
    voices = manifest.get("voices", [])
    clips = manifest.get("clips", {})
    if not voices:
        print("No voices in manifest"); sys.exit(1)
    print(f"\nManifest: {MANIFEST}")
    for v in voices:
        vid = v["id"]; n = len(clips.get(vid, {})); missing_files = 0
        for key, rel in clips.get(vid, {}).items():
            if not os.path.exists(os.path.join(ROOT, rel.replace("/", os.sep))): missing_files += 1
        print(f"  {v.get('label', vid)} - {n} keys, {missing_files} missing files")
    html = open(HTML, encoding="utf-8").read()
    needed = collect_clips_needed(html); have = existing_keys(manifest)
    missing = sorted(k for k in needed if k not in have)
    print(f"\nCurriculum {len(needed)} keys; manifest {len(have)} unique; missing {len(missing)}")
    for m in missing[:10]: print(f"    {m}")
    if len(missing) > 10: print(f"    ... {len(missing)-10} more")
    print()

if "--verify" in sys.argv:
    verify(); sys.exit(0)

if "--diff" in sys.argv:
    html = open(HTML, encoding="utf-8").read()
    needed = collect_clips_needed(html); manifest = load_manifest(); have = existing_keys(manifest)
    missing = sorted(k for k in needed if k not in have)
    print(f"Missing {len(missing)} keys:")
    for m in missing: print(f"  {m}")
    sys.exit(0)

API_KEY = os.environ.get("OPENAI_API_KEY", "").strip()
if not API_KEY: sys.exit("No OPENAI_API_KEY")

if not os.path.exists(HTML): sys.exit(f"Not found: {HTML}")
html = open(HTML, encoding="utf-8").read()
needed = collect_clips_needed(html); manifest = load_manifest()
if not manifest.get("voices"):
    manifest["voices"] = [{"id": v, "gender": g, "label": lbl} for v, (g, lbl) in VOICES.items()]
for v in VOICES: manifest.setdefault("clips", {}).setdefault(v, {})
have = existing_keys(manifest)
todo = {k: t for k, t in needed.items() if k not in have}
total = len(VOICES) * len(todo); done = 0
print(f"\n{len(todo)} missing x {len(VOICES)} voices = {total} clips\n")
if not todo:
    print("Nothing to synthesize"); verify(); sys.exit(0)
for voice in VOICES:
    vdir = os.path.join(AUDIO_DIR, voice); os.makedirs(vdir, exist_ok=True)
    for key, text in todo.items():
        mp3 = tts(API_KEY, voice, text)
        fname = slug(text) + "." + FORMAT; rel = f"audio/{voice}/{fname}"
        open(os.path.join(ROOT, rel.replace("/", os.sep)), "wb").write(mp3)
        manifest["clips"][voice][key] = rel
        done += 1
        if done % 10 == 0 or done == total: print(f"  {done}/{total}")
save_manifest(manifest); print(f"\nUpdated {MANIFEST}"); verify()
