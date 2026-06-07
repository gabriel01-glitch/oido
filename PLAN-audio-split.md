# PLAN: Audio Split → Export/Import → Netlify

**Status:** Diff preview — NOT applied yet. Say **"apply the plan"** to execute.

---

## TTS source (confirmed from original script)

Found: `C:\Users\gabri\Downloads\files (4)\generate_audio.py`

| Setting | Value |
|---------|-------|
| Model | **`tts-1-hd`** |
| Format | **`mp3`** |
| Speed | **`0.95`** |
| Voices in production file | **nova** (f), **onyx** (m) only |
| Clip key | **spoken text** (`key == text`) |
| API | `POST https://api.openai.com/v1/audio/speech` |

Old script does **not** synth curriculum `exEn` — only `speakAs||word` for pairs.

---

## Clip inventory (analyzed from current `index.html`)

| Metric | nova | onyx |
|--------|------|------|
| Total clips | 541 | 541 |
| Word-like keys | 334 | 334 |
| Phrase-like keys | 207 | 207 |
| Decoded size | 8.81 MB | 8.96 MB |

**Combined:** 1,082 clips, ~17.8 MB decoded, 23.9 MB inline HTML.

### exEn sentence diff (126 curriculum sentences)

| Status | Count |
|--------|-------|
| Already in clips | **1** (`"She is my best friend."` — WOTD overlap) |
| **Missing — need generation** | **125** |

`generate_audio.py` will add only missing keys (skip existing cache/files).

---

## Implementation order

1. **Phase A** — Extract audio + lazy-load (GitHub URL unchanged)
2. **Phase B** — JSON export/import (file primary, URL fallback)
3. **Phase C** — Netlify config + generate 125 missing sentence clips
4. **Phase D** — Migration banner when Netlify URL is live

---

## New file tree

```
oido/
├── index.html                 # ~200 KB (no base64 blob)
├── audio/
│   ├── manifest.json          # keys → paths
│   ├── nova/*.mp3             # 541 files
│   └── onyx/*.mp3             # 541 files (+ 125 new per voice later)
├── scripts/
│   ├── extract_audio.py       # one-time decode from current HTML
│   └── generate_audio.py      # from Downloads/files (4), adapted for external mp3
├── netlify.toml
├── .gitignore                 # .env, audio_cache/
└── AGENTS.md
```

---

## Phase A — `speak()` diff (TTS fallback preserved)

**Remove** 24 MB `#embedded-audio` blob.

**Add** manifest fetch + URL playback:

```diff
- const EMB  = JSON.parse(document.getElementById('embedded-audio').textContent);
+ let AUDIO_MANIFEST = null;
+ const clipUrlCache = {};  // "nova:ship" → blob URL or path

+ async function loadAudioManifest(){
+   if(AUDIO_MANIFEST) return AUDIO_MANIFEST;
+   try{
+     const r = await fetch('audio/manifest.json');
+     AUDIO_MANIFEST = r.ok ? await r.json() : {voices:[],clips:{}};
+   }catch(e){ AUDIO_MANIFEST = {voices:[],clips:{}}; }
+   return AUDIO_MANIFEST;
+ }
+ function clipPath(voiceId, key){
+   const m = AUDIO_MANIFEST;
+   return (m && m.clips && m.clips[voiceId] && m.clips[voiceId][key]) || null;
+ }

  function speak(text, key, cardEl, onDone){
    stopAll();
    const v = curVoice();
    const onStart = ()=>{ if(cardEl) cardEl.classList.add('playing'); };
    const onEnd   = ()=>{ if(cardEl) cardEl.classList.remove('playing'); if(onDone) onDone(); };

-   if(v && v.kind==='premium' && EMB.clips[v.key] && EMB.clips[v.key][key]){
+   const path = (v && v.kind==='premium') ? clipPath(v.key, key) : null;
+   if(path){
      try{
-       currentAudio = new Audio(EMB.clips[v.key][key]);
+       currentAudio = new Audio(path);
        currentAudio.onplay = onStart;
        currentAudio.onended = onEnd;
-       currentAudio.onerror = ()=>{ deviceSpeak(text,onStart,onEnd); };
-       currentAudio.play().catch(()=>{ deviceSpeak(text,onStart,onEnd); });
+       currentAudio.onerror = ()=>{ deviceSpeak(text,onStart,onEnd); };  // never silent
+       currentAudio.play().catch(()=>{ deviceSpeak(text,onStart,onEnd); });
        return;
      }catch(e){ /* fall through to device TTS */ }
    }
    deviceSpeak(text,onStart,onEnd);  // unchanged fallback
  }

+ // kick off manifest load early (non-blocking)
+ loadAudioManifest();
```

**Invariant:** every `onerror` / `play().catch()` path calls `deviceSpeak` — student never gets silence.

---

## Phase B — Export/import diff

**Primary:** downloadable `oido-progreso.json`  
**Fallback:** `?backup=` URL only if payload < 1,800 chars (WhatsApp-safe)

```diff
+ const OIDO_LS_KEYS = ['oido_voice','oido_scores','oido_contrasts','oido_streak','oido_wlevel','oido_saved'];

+ function exportProgress(){
+   const data = {v:1, exported:Date.now(), keys:{}};
+   OIDO_LS_KEYS.forEach(k=>{ const v=localStorage.getItem(k); if(v!=null) data.keys[k]=v; });
+   const json = JSON.stringify(data);
+   const blob = new Blob([json], {type:'application/json'});
+   const a = document.createElement('a');
+   a.href = URL.createObjectURL(blob);
+   a.download = 'oido-progreso.json';
+   a.click();
+   if(json.length < 1800 && navigator.clipboard){
+     const link = location.origin+location.pathname+'?backup='+encodeURIComponent(btoa(json));
+     navigator.clipboard.writeText(link).catch(()=>{});
+     toast('Archivo descargado. Enlace corto copiado también.');
+   } else {
+     toast('Archivo descargado ✓ — guárdalo para importar después.');
+   }
+ }

+ function importProgress(data){
+   if(!data || !data.keys) return false;
+   Object.entries(data.keys).forEach(([k,v])=>localStorage.setItem(k,v));
+   return true;
+ }

+ // hidden file input + button in Mis palabras header
+ <input type="file" id="importFile" accept=".json,application/json" hidden>
+ <button id="exportProgressBtn">⬇ Exportar progreso</button>
+ <button id="importProgressBtn">⬆ Importar progreso</button>
```

---

## Phase C — `netlify.toml`

```toml
[build]
  publish = "."

[[headers]]
  for = "/audio/*"
  [headers.values]
    Cache-Control = "public, max-age=31536000, immutable"
```

---

## Phase D — `generate_audio.py` changes (from original)

- Output to `audio/{voice}/{slug}.mp3` + update `manifest.json`
- MODEL=`tts-1-hd`, speed=`0.95`, voices=`nova`,`onyx`
- Collect clips from curriculum words **and** `exEn` (new)
- **Diff step:** skip keys already in manifest / cache
- Only synthesize **125 missing** sentence keys (+ any new words)

---

## Test checklist

- [ ] `index.html` < 1 MB after extract
- [ ] Word + phrase clips play from `/audio/`
- [ ] Airplane mode / 404 mp3 → device TTS speaks (not silence)
- [ ] Export JSON → import on clean browser restores words + scores
- [ ] Long progress → file only, no truncated WhatsApp URL
- [ ] Netlify serves mp3 with cache headers
- [ ] GitHub Pages still works at same URL during transition