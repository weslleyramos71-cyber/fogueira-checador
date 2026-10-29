"""Paso 5 — render del reel según plan.json.
Uso:
  python scripts/render.py CARPETA_PROYECTO --preview 1,5.5,12      (capturas -> preview.png, rápido)
  python scripts/render.py CARPETA_PROYECTO                         (video final -> final.mp4)
Ver PLAN.md para todas las opciones del plan."""
import sys, os, json, math, re, argparse, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import cv2

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KIT, "scripts"))
import fx

ap = argparse.ArgumentParser(); ap.add_argument("proj"); ap.add_argument("--preview", default=None); ap.add_argument("--out", default=None)
ARGS = ap.parse_args(); PROJ = ARGS.proj
INFO = json.load(open(f"{PROJ}/info.json")); PLAN = json.load(open(f"{PROJ}/plan.json"))
CAPS = json.load(open(f"{PROJ}/captions.json")) if os.path.exists(f"{PROJ}/captions.json") else []
SW, SH = INFO["width"], INFO["height"]; fx.SW, fx.SH = SW, SH
W, H, FPS, UP = 1080, 1920, 30, 2

T = lambda c: tuple(int(x) for x in c)
LAY = PLAN.get("layout", {})
ACC = T(LAY.get("accent", [255, 106, 26])); BLUE = (52, 120, 255); GREEN = (46, 190, 90)
BG = T(LAY.get("background", [16, 14, 13])); CARD = (28, 26, 24); LINE = (52, 48, 44)
CREAM = (246, 240, 232); MUTED = (150, 142, 134)

def font(name, s, v=None):
    f = ImageFont.truetype(f"{KIT}/fonts/{name}", int(s))
    if v:
        try: f.set_variation_by_name(v)
        except Exception: pass
    return f
ANTON = lambda s: font("Anton-Regular.ttf", s)
MONT = lambda s, v="ExtraBold": font("Montserrat-VF.ttf", s, v)
INT = lambda s, w="SemiBold": font("Inter-VF.ttf", s, w)

# ---------------- easing ----------------
def bez(p1x, p1y, p2x, p2y):
    def f(x):
        if x <= 0: return 0.0
        if x >= 1: return 1.0
        lo, hi = 0.0, 1.0
        for _ in range(30):
            m = (lo + hi) / 2
            if 3 * (1 - m) ** 2 * m * p1x + 3 * (1 - m) * m ** 2 * p2x + m ** 3 < x: lo = m
            else: hi = m
        m = (lo + hi) / 2
        return 3 * (1 - m) ** 2 * m * p1y + 3 * (1 - m) * m ** 2 * p2y + m ** 3
    return f
easeOut = bez(0.16, 1, 0.3, 1); easeIn = bez(0.6, 0, 0.9, 0.35); easeInOut = bez(0.65, 0, 0.35, 1)
def prog(t, a, b, e=easeOut): return e(min(1, max(0, (t - a) / (b - a)))) if b > a else float(t >= b)
_sp = {}
def spring(t, d=10, k=220, m=0.7):
    if t <= 0: return 0.0
    if (d, k, m) not in _sp:
        x = v = 0.0; arr = []
        for _ in range(2400):
            a = (-k * (x - 1) - d * v) / m; v += a / 600; x += v / 600; arr.append(x)
        _sp[(d, k, m)] = arr
    return _sp[(d, k, m)][min(2399, int(t * 600))]
def window(t, a, b, fin=0.35, fout=0.25): return prog(t, a, a + fin) * (1 - prog(t, b - fout, b, easeIn))
def lerp(a, b, k): return a + (b - a) * k

# ---------------- sprites ----------------
_cache = {}
def text(s, f, col, track=0, stroke=0, scol=(0, 0, 0)):
    key = (s, id(f), col, track, stroke)
    if key in _cache: return _cache[key]
    w = int(sum(f.getlength(c) for c in s) + track * max(0, len(s) - 1)) + 2 * stroke + 8
    bb = f.getbbox("ÁgjÑ|")
    im = Image.new("RGBA", (max(1, w), bb[3] + 2 * stroke + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 4 + stroke
    if track:
        for c in s: d.text((x, 4 + stroke), c, font=f, fill=col, stroke_width=stroke, stroke_fill=scol); x += f.getlength(c) + track
    else: d.text((x, 4 + stroke), s, font=f, fill=col, stroke_width=stroke, stroke_fill=scol)
    im = im.crop(im.getbbox()) if im.getbbox() else im
    _cache[key] = im; return im

def shadow(spr, r=14, a=0.6, off=6):
    pad = r * 2; out = Image.new("RGBA", (spr.width + 2 * pad, spr.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(spr.split()[3], (pad, pad + off))
    s = Image.new("RGBA", out.size, (0, 0, 0, 0)); s.putalpha(m.filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * a)))
    out.alpha_composite(s); out.alpha_composite(spr, (pad, pad)); return out

def place(L, spr, cx, cy, a=1.0, sc=1.0, rot=0):
    if a <= 0.004 or sc <= 0.01: return
    s = spr
    if abs(sc - 1) > 0.003: s = s.resize((max(1, int(s.width * sc)), max(1, int(s.height * sc))), Image.BICUBIC)
    if rot: s = s.rotate(rot, Image.BICUBIC, expand=True)
    if a < 1: s = s.copy(); s.putalpha(s.split()[3].point(lambda v: int(v * a)))
    L.alpha_composite(s, (int(cx - s.width / 2), int(cy - s.height / 2)))

def two_tone(a, b, size, ca=CREAM, cb=ACC):
    fa = ANTON(size); s1 = text(a, fa, ca) if a else None; s2 = text(b, fa, cb) if b else None
    gap = int(size * 0.18) if (a and b) else 0
    w = (s1.width if s1 else 0) + gap + (s2.width if s2 else 0); h = max(x.height for x in (s1, s2) if x)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if s1: im.alpha_composite(s1, (0, h - s1.height))
    if s2: im.alpha_composite(s2, (w - s2.width, h - s2.height))
    if im.width > W - 80:  # never wider than the frame
        k = (W - 80) / im.width; im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    return im

def big_word(L, t, t0, t1, a, b, cy, size=150, ca=CREAM, cb=ACC):
    if not (t0 - 0.05 <= t < t1 + 0.3): return
    spr = two_tone(a, b, size, ca, cb)
    pin = prog(t, t0, t0 + 0.45); pout = prog(t, t1, t1 + 0.25, easeIn)
    clip = Image.new("RGBA", (spr.width + 20, spr.height + 20), (0, 0, 0, 0))
    clip.alpha_composite(spr, (10, 10 + int((1 - pin) * spr.height * 0.9 + pout * spr.height * 0.9)))
    place(L, shadow(clip, 18, 0.5), W / 2, cy)

def rrect(w, h, r, fill, outline=None, width=2):
    im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=fill, outline=outline, width=width * 2)
    return im.resize((w, h), Image.LANCZOS)

def chip(s, fg=CREAM, bg=(40, 37, 34, 255), size=30, padx=26, h=62, icon=None):
    ts = text(s, INT(size, "SemiBold"), fg); iw = (icon.width + 14) if icon else 0
    im = rrect(ts.width + 2 * padx + iw, h, h // 2, bg)
    if icon: im.alpha_composite(icon, (padx, (h - icon.height) // 2))
    im.alpha_composite(ts, (padx + iw, (h - ts.height) // 2)); return im

def label(s, col=MUTED): return text(s, INT(24, "SemiBold"), col, track=5)

def check_icon(sz, col=ACC, fg=(255, 255, 255)):
    S = sz * 3; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S - 1, S - 1), fill=col)
    d.line([(S * .28, S * .52), (S * .44, S * .67), (S * .73, S * .35)], fill=fg, width=int(S * .09), joint="curve")
    return im.resize((sz, sz), Image.LANCZOS)

def ui_card(w, h): return shadow(rrect(w, h, 30, CARD + (255,), LINE + (255,), 2), 20, 0.55, 8)
def swatch(col, sz=150):
    S = sz * 2; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S - 1, S - 1), fill=CREAM + (255,)); d.ellipse((8, 8, S - 9, S - 9), fill=T(col) + (255,))
    return im.resize((sz, sz), Image.LANCZOS)
def arrow(w, col=ACC):
    im = Image.new("RGBA", (w, 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.line([(0, 20), (w - 14, 20)], fill=col, width=6); d.polygon([(w - 20, 6), (w, 20), (w - 20, 34)], fill=col); return im
def logo_face(spec, size=320):
    if spec == "claude": return fx.claude_logo(size)
    if spec == "chatgpt": return fx.chatgpt_logo(size)
    p = spec if os.path.isabs(spec) else os.path.join(PROJ, spec)
    return Image.open(p).convert("RGBA").resize((size, size), Image.LANCZOS)

# ---------------- canvas ----------------
def make_canvas():
    y, x = np.mgrid[0:H, 0:W]; arr = np.zeros((H, W, 3), np.float32) + BG
    for (cx, cy, rx, ry, a) in [(850, 1250, 520, 380, 34), (160, 1650, 420, 300, 26), (900, 350, 380, 260, 14)]:
        arr += np.exp(-(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2))[..., None] * np.array([255, 196, 160]) * a / 255
    arr += np.random.default_rng(3).normal(0, 2.0, arr.shape)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
CANVAS = make_canvas()

# ---------------- captions ----------------
CAP_F = MONT(64, "ExtraBold")
def cap_sprite(s):
    key = ("cap", s)
    if key in _cache: return _cache[key]
    segs = []
    for p in [p for p in re.split(r"(\*[^*]+\*|#[^#]+#|%[^%]+%)", s) if p]:
        segs.append((p.strip("*#%"), {"*": ACC, "#": BLUE, "%": GREEN}.get(p[0], CREAM)))
    w = int(sum(CAP_F.getlength(x) for x, _ in segs)) + 30
    im = Image.new("RGBA", (w, 100), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 12
    for s_, col in segs: d.text((x, 10), s_, font=CAP_F, fill=col, stroke_width=6, stroke_fill=(12, 10, 10)); x += CAP_F.getlength(s_)
    im = im.crop(im.getbbox())
    if im.width > W - 80: k = (W - 80) / im.width; im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    im = shadow(im, 10, 0.7, 4); _cache[key] = im; return im

# ---------------- effects ----------------
EFF = PLAN.get("effects", {})
BGX = EFF.get("background"); CHAIR = EFF.get("chair"); RECOLOR = EFF.get("recolor", []); LOGOS = EFF.get("hand_logos", [])
ROOM = None
if BGX:
    if BGX.get("image"):
        p = BGX["image"] if os.path.isabs(BGX["image"]) else os.path.join(PROJ, BGX["image"])
        im = Image.open(p).convert("RGB"); s = max(SW / im.width, SH / im.height)
        im = im.resize((math.ceil(im.width * s), math.ceil(im.height * s)), Image.LANCZOS)
        im = im.crop(((im.width - SW) // 2, (im.height - SH) // 2, (im.width - SW) // 2 + SW, (im.height - SH) // 2 + SH))
        ROOM = np.asarray(im.filter(ImageFilter.GaussianBlur(BGX.get("blur", 3))), np.float32)
    else:
        ROOM = fx.gamer_room()
CHAIR_IMG = fx.gamer_chair() if CHAIR else None
LOGO_FACES = {l["logo"]: logo_face(l["logo"]) for l in LOGOS}
HANDS = json.load(open(f"{PROJ}/hands.json")) if LOGOS else []
SR = cv2.dnn_superres.DnnSuperResImpl_create(); SR.readModel(f"{KIT}/models/FSRCNN_x2.pb"); SR.setModel("fsrcnn", 2)

def wipe(shape, t, t0, dur, axis=0):
    k = prog(t, t0, t0 + dur, easeInOut); pos = np.linspace(0, 1, shape[axis]); m = np.clip((k * 1.2 - pos) / 0.2, 0, 1)
    return m[:, None] if axis == 0 else m[None, :]

def hand_anchor(n):
    best = None
    for h in (HANDS[n] if n < len(HANDS) else []):
        P = np.array(h["pts"]) * [SW, SH]; palm = P[[0, 5, 9, 13, 17]].mean(0)
        span = max(np.ptp(P[:, 0]), np.ptp(P[:, 1])); top = P[:, 1].min()
        if best is None or top < best[2]: best = (palm, span, top)
    return best
_anc = {}
def smooth_anchor(n, n0):
    for k in range(n0, n + 1):
        if k in _anc: continue
        prev = _anc.get(k - 1) if k > n0 else None; a = hand_anchor(k)
        if a is None: _anc[k] = prev; continue
        x, y = a[0][0], a[2] - a[1] * 0.35; s = max(SW * 0.19, min(SW * 0.4, a[1] * 1.05))
        _anc[k] = (x, y, s) if prev is None else tuple(p * 0.7 + q * 0.3 for p, q in zip(prev, (x, y, s)))
    return _anc.get(n)

def composite_source(fr, masks, t, n):
    fr = fx.grade_person(fr.astype(np.float32)); al = masks[..., 0].astype(np.float32); a01 = al / 255
    for rc in RECOLOR:
        if t >= rc["start"]:
            ch = 1 if rc.get("part", "clothes") == "clothes" else 2
            m = masks[..., ch] / 255.0 * a01 * wipe(fr.shape, t, rc["start"], 0.7, 0)
            fr = fx.recolor2(fr, m, T(rc["color"]))
    out = fr
    if BGX and t >= BGX["start"]:
        k = wipe(fr.shape, t, BGX["start"], 0.8, 1)[..., None] if t < BGX["start"] + 0.8 else 1.0
        p = fx.relight2(fr, al, ROOM); base = ROOM.copy()
        if CHAIR and t >= CHAIR["start"]:
            ca = CHAIR_IMG[..., 3:4] / 255 * prog(t, CHAIR["start"], CHAIR["start"] + 0.45)
            base = base * (1 - ca) + CHAIR_IMG[..., :3] * ca
        new = base * (1 - a01[..., None]) + p * a01[..., None]
        out = fr * (1 - k) + new * k
        if t < BGX["start"] + 0.8:
            kk = prog(t, BGX["start"], BGX["start"] + 0.8, easeInOut) * 1.2
            xs = np.linspace(0, 1, SW)[None, :]
            out = np.clip(out + np.exp(-((xs - kk + 0.1) / 0.03) ** 2)[..., None] * np.array([255, 150, 70]) * 0.9, 0, 255)
    up = SR.upsample(np.ascontiguousarray(np.clip(out, 0, 255).astype(np.uint8)[..., ::-1]))[..., ::-1]
    up = cv2.addWeighted(up, 1.45, cv2.GaussianBlur(up, (0, 0), 1.6), -0.45, 0)
    img = Image.fromarray(np.ascontiguousarray(up)).convert("RGBA")
    for lg in LOGOS:
        a, b = lg["start"], lg["end"]
        if a <= t < b + 0.3:
            anc = smooth_anchor(n, int(a * FPS))
            if anc is None: continue
            x, y, s = anc[0] * UP, anc[1] * UP, anc[2] * UP
            sc = spring(t - a, 9, 200, 0.75) * (1 - prog(t, b, b + 0.3, easeIn))
            if sc < 0.03: continue
            spr = fx.spin_frame(LOGO_FACES[lg["logo"]], (t - a) * 2 * math.pi * 0.55, max(8, int(s * sc)))
            spr = fx.glow_sprite(spr, 30, T(lg.get("glow", [255, 160, 100])), 0.75)
            sh = Image.new("RGBA", (int(s * 0.9), int(s * 0.25)), (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse((0, 0, sh.width - 1, sh.height - 1), fill=(0, 0, 0, int(90 * sc)))
            img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)), (int(x - sh.width / 2), int(y + s * 0.55)))
            img.alpha_composite(spr, (int(x - spr.width / 2), int(y - spr.height / 2 + math.sin((t - a) * 4) * 12)))
    return img

# ---------------- panel elements (see PLAN.md) ----------------
def el_big(L, t, e):
    big_word(L, t, e["start"], e["end"], e.get("a", ""), e.get("b", ""), e.get("y", 400), e.get("size", 150),
             T(e.get("color_a", CREAM)), T(e.get("color_b", ACC)))

def el_chips(L, t, e):
    items = e["items"]; n = len(items)
    for i, (s, ts) in enumerate(items):
        if ts <= t < e["end"] + 0.3:
            a = spring(t - ts); o = 1 - prog(t, e["end"], e["end"] + 0.3, easeIn)
            x = W / 2 + (i - (n - 1) / 2) * min(440, (W - 160) / max(1, n))
            place(L, shadow(chip(s, size=36, h=84)), x, e.get("y", 470), min(1, a) * o, 0.6 + 0.4 * a)

def el_check(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.3): return
    a = spring(t - e["start"], 9, 230, 0.7); o = 1 - prog(t, e["end"] - 0.2, e["end"] + 0.1, easeIn)
    place(L, shadow(check_icon(220)), W / 2, 290, min(1, a * 1.5) * o, 0.4 + 0.6 * a)
    if e.get("a") or e.get("b"): big_word(L, t, e["start"] + 0.9, e["end"], e.get("a", ""), e.get("b", ""), 560, 110)

def el_swatch(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.2): return
    o = window(t, e["start"], e["end"]); at = e.get("at", (e["start"] + e["end"]) / 2)
    if e.get("label"): place(L, label(e["label"].upper()), W / 2, 150, o)
    place(L, shadow(swatch(e.get("from", [14, 14, 16]))), 330, 330, o)
    place(L, arrow(140), W / 2, 330, prog(t, at - 0.3, at + 0.2) * o)
    a = spring(t - at); place(L, shadow(swatch(e["to"])), 750, 330, min(1, a) * o, 0.5 + 0.5 * a)
    if e.get("word"): big_word(L, t, at + 0.3, e["end"], "", e["word"], 560, 150, CREAM, T(e["to"]))

def waveform(w, h, t, ck):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im); rng = np.random.default_rng(1); n = 46; bw = w / n
    base = np.abs(np.sin(np.linspace(0, 7, n))) * 0.6 + 0.25; noise = rng.uniform(0.3, 1.0, n)
    for i in range(n):
        v = (noise[i] * (1 - ck) + base[i] * ck) * (0.75 + 0.25 * math.sin(t * 9 + i * 0.7)); hh = max(6, v * h * 0.9)
        col = tuple(int(MUTED[c] * (1 - ck) + ACC[c] * ck) for c in range(3))
        d.rounded_rectangle((i * bw + 2, h / 2 - hh / 2, i * bw + bw - 3, h / 2 + hh / 2), 4, fill=col + (255,))
    return im

def toggle(k):
    w, h = 120, 64
    im = rrect(w, h, h // 2, tuple(int(LINE[c] * (1 - k) + ACC[c] * k) for c in range(3)) + (255,))
    im.alpha_composite(rrect(52, 52, 26, (255, 255, 255, 255)), (int(6 + (w - 64) * k), 6)); return im

def el_audio(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.2): return
    o = window(t, e["start"], e["end"]); card = ui_card(920, 560).copy(); d = ImageDraw.Draw(card)
    d.text((50, 40), e.get("title", "AUDIO").upper(), font=INT(24, "SemiBold"), fill=MUTED)
    ck = prog(t, e.get("clean_at", e["start"] + 2), e.get("clean_at", e["start"] + 2) + 0.8)
    card.alpha_composite(waveform(820, 150, t, ck), (50, 90))
    for i, (s, ts) in enumerate(e.get("tags", [])):
        if t >= ts:
            c_ = chip(s, size=28, h=56, bg=(48, 45, 42, 255)); x0 = 50 + i * 300; card.alpha_composite(c_, (x0, 270))
            if t >= ts + 0.35:
                sk = prog(t, ts + 0.35, ts + 0.7); d.line([(x0 + 10, 298), (x0 + 10 + (c_.width - 20) * sk, 298)], fill=ACC, width=5)
    if ck > 0.5: card.alpha_composite(check_icon(48), (650, 274)); d.text((710, 280), e.get("clean_word", "OK"), font=INT(30, "Bold"), fill=CREAM)
    if e.get("toggle"):
        d.line([(50, 365), (870, 365)], fill=LINE, width=2); d.text((50, 420), e["toggle"], font=INT(36, "Bold"), fill=CREAM)
        card.alpha_composite(toggle(prog(t, e.get("toggle_at", e["end"] - 1), e.get("toggle_at", e["end"] - 1) + 0.4, easeInOut)), (750, 412))
    place(L, card, W / 2, 380 + 30 * (1 - o), o)

def el_checklist(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.3): return
    o = 1 - prog(t, e["end"] - 0.3, e["end"], easeIn)
    if e.get("title"): place(L, label(e["title"].upper()), W / 2, 110, prog(t, e["start"], e["start"] + 0.4) * o)
    for i, s in enumerate(e["items"]):
        a = prog(t, e["start"] + 0.3 + i * 0.14, e["start"] + 0.7 + i * 0.14)
        place(L, chip(s, icon=check_icon(40), size=32, h=80), 300 + (i % 2) * 480, 230 + (i // 2) * 120 + 20 * (1 - a), a * o)

def el_chat(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.2): return
    o = window(t, e["start"], e["end"]); card = ui_card(900, 380).copy(); d = ImageDraw.Draw(card)
    d.text((60, 58), e.get("assistant", "IA"), font=INT(32, "Bold"), fill=CREAM); d.ellipse((800, 72, 814, 86), fill=(70, 200, 120))
    bub = e["user"][: int(max(0, (t - e["start"] - 0.4) * 22))]
    if bub:
        f = INT(30, "Medium"); ub = rrect(int(f.getlength(bub)) + 60, 76, 24, (48, 45, 42, 255))
        ImageDraw.Draw(ub).text((30, 20), bub, font=f, fill=CREAM); card.alpha_composite(ub, (860 - ub.width, 140))
    ra = e.get("reply_at", e["start"] + 3.4)
    if ra - 0.9 <= t < ra:
        for i in range(3):
            yy = 270 - 8 * max(0, math.sin(t * 8 - i)); d.ellipse((70 + i * 30, yy, 88 + i * 30, yy + 18), fill=MUTED)
    if t >= ra:
        k = prog(t, ra, ra + 0.4); f = INT(30, "Bold")
        rb = rrect(int(f.getlength(e["reply"])) + 60, 80, 24, ACC + (int(255 * k),))
        ImageDraw.Draw(rb).text((30, 20), e["reply"], font=f, fill=(255, 255, 255, int(255 * k))); card.alpha_composite(rb, (60, 250))
    place(L, card, W / 2, 300 + 30 * (1 - o), o)

def el_before_after(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.2): return
    o = window(t, e["start"], e["end"])
    def tile(top, name, col, k):
        c = ui_card(420, 400).copy(); d = ImageDraw.Draw(c)
        d.text((40, 36), top, font=INT(24, "SemiBold"), fill=col)
        d.rounded_rectangle((80, 105, 340, 265), 22, outline=col, width=4)
        f = INT(32, "Bold"); d.text((210 - f.getlength(name) / 2, 290), name, font=f, fill=CREAM); return c
    place(L, tile(e.get("before_label", "ANTES"), e.get("before", ""), MUTED, 1), 300 - 40 * (1 - o), 340, o)
    at = e.get("after_at", (e["start"] + e["end"]) / 2)
    if t >= at:
        k = prog(t, at, at + 0.5) * o; place(L, arrow(90), W / 2, 340, k)
        place(L, tile(e.get("after_label", "DESPUÉS"), e.get("after", ""), ACC, k), 780 + 40 * (1 - k), 340, k)

def el_follow(L, t, e):
    if not (e["start"] - 0.1 <= t < e["end"] + 0.2): return
    o = window(t, e["start"], e["end"]); card = ui_card(900, 260).copy(); d = ImageDraw.Draw(card)
    d.ellipse((50, 60, 190, 200), fill=(60, 56, 52))
    d.text((220, 80), e.get("handle", "@tu_pagina"), font=INT(40, "Bold"), fill=CREAM)
    if e.get("bio"): d.text((220, 140), e["bio"], font=INT(28, "Medium"), fill=MUTED)
    tap = e.get("tap_at", e["start"] + 1.5); tapped = t >= tap
    btn = chip(e.get("done", "✓") if tapped else e.get("button", "Seguir"), fg=(255, 255, 255) if not tapped else CREAM,
               bg=ACC + (255,) if not tapped else (48, 45, 42, 255), size=34, h=84, padx=34)
    pulse = 1 + 0.05 * math.sin(t * 8) if not tapped else 1
    b = btn.resize((int(btn.width * pulse), int(btn.height * pulse))); card.alpha_composite(b, (int(860 - b.width), int(130 - b.height / 2)))
    if tap <= t < tap + 0.6:
        r = 20 + 140 * prog(t, tap, tap + 0.6); a = int(200 * (1 - prog(t, tap, tap + 0.6)))
        d.ellipse((760 - r, 130 - r, 760 + r, 130 + r), outline=(255, 255, 255, a), width=5)
    place(L, card, W / 2, 260 + 30 * (1 - o), o)

def el_label(L, t, e):
    place(L, label(e["text"].upper(), ACC), e.get("x", 220), e.get("y", 52), window(t, e["start"], e["end"], 0.3, 0.3))

ELEMENTS = {"big": el_big, "chips": el_chips, "check": el_check, "swatch": el_swatch, "audio": el_audio,
            "checklist": el_checklist, "chat": el_chat, "before_after": el_before_after, "follow": el_follow, "label": el_label}
PANEL = PLAN.get("panel", []); OVERLAY = PLAN.get("full_overlay", [])

# ---------------- layout ----------------
FULL = [tuple(x) for x in LAY.get("punch_in", [])]
CARD_R = (60, 770, 1020, 1860)
def fullness(t): return max([prog(t, a, a + 0.4, easeInOut) * (1 - prog(t, b - 0.4, b, easeInOut)) for a, b in FULL] + [0])
_rm = {}
def round_mask(w, h, r):
    if (w, h, r) not in _rm:
        m = Image.new("L", (w * 2, h * 2), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w * 2 - 1, h * 2 - 1), r * 2, fill=255)
        _rm[(w, h, r)] = m.resize((w, h), Image.LANCZOS)
    return _rm[(w, h, r)]
FOCUS_Y = LAY.get("focus_y", 0.42)  # vertical centre of the card crop, as a fraction of the source height

def frame(t, n, fr, masks):
    src = composite_source(fr, masks, t, n); k = fullness(t)
    x0, y0, x1, y1 = [lerp(a, b, k) for a, b in zip(CARD_R, (0, 0, W, H))]
    cw, ch = int(x1 - x0), int(y1 - y0); ca = cw / ch
    SWu, SHu = SW * UP, SH * UP; sh_ = min(SHu, SWu / ca); sw_ = sh_ * ca
    cy = lerp(FOCUS_Y * SHu, SHu / 2, k); top = max(0, min(SHu - sh_, cy - sh_ / 2)); left = (SWu - sw_) / 2
    vid = src.convert("RGB").resize((cw, ch), Image.LANCZOS, box=(left, top, left + sw_, top + sh_)).convert("RGBA")
    L = CANVAS.copy()
    if k < 0.999:
        P = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for e in PANEL: ELEMENTS[e["type"]](P, t, e)
        if k > 0: P.putalpha(P.split()[3].point(lambda v: int(v * (1 - k))))
        L.alpha_composite(P)
    vid.putalpha(round_mask(cw, ch, max(1, int(lerp(36, 0, k)))))
    if k < 0.999:
        sh = Image.new("RGBA", (cw + 80, ch + 80), (0, 0, 0, 0)); m = Image.new("L", sh.size, 0); m.paste(vid.split()[3], (40, 50))
        sh.putalpha(m.filter(ImageFilter.GaussianBlur(24)).point(lambda v: int(v * 0.6))); L.alpha_composite(sh, (int(x0) - 40, int(y0) - 40))
    L.alpha_composite(vid, (int(x0), int(y0)))
    if k > 0 and OVERLAY:
        O = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for e in OVERLAY: ELEMENTS[e["type"]](O, t, e)
        O.putalpha(O.split()[3].point(lambda v: int(v * k))); L.alpha_composite(O)
    for i, (c0, s) in enumerate(CAPS):
        c1 = min(CAPS[i + 1][0] if i + 1 < len(CAPS) else c0 + 1.2, c0 + 1.3)
        if c0 <= t < c1:
            a = spring(t - c0, 12, 300, 0.6)
            place(L, cap_sprite(s), W / 2, lerp(y1 - 230, 1520, k), min(1, a * 2), 0.82 + 0.18 * min(1, a))
    return L.convert("RGB")

# ---------------- run ----------------
def readers():
    v = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", f"{PROJ}/norm.mp4", "-vf", "hqdn3d=1.5:1.5:5:5", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    m = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", f"{PROJ}/masks.mkv", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    return v, m

def main():
    dec, mdec = readers(); fsz = SW * SH * 3
    if ARGS.preview:
        want = sorted(int(round(float(x) * FPS)) for x in ARGS.preview.split(",")); got = []; n = 0
        while want and n <= want[-1]:
            b = dec.stdout.read(fsz); mb = mdec.stdout.read(fsz)
            if len(b) < fsz: break
            if n in want:
                got.append(frame(n / FPS, n, np.frombuffer(b, np.uint8).reshape(SH, SW, 3), np.frombuffer(mb, np.uint8).reshape(SH, SW, 3)).resize((540, 960)))
            n += 1
        dec.kill(); mdec.kill()
        cols = min(4, len(got)); rows = math.ceil(len(got) / cols)
        sheet = Image.new("RGB", (540 * cols, 960 * rows), (0, 0, 0))
        for i, g in enumerate(got): sheet.paste(g, ((i % cols) * 540, (i // cols) * 960))
        out = ARGS.out or f"{PROJ}/preview.png"; sheet.save(out); print("OK  vista previa ->", out); return
    out = ARGS.out or f"{PROJ}/final.mp4"
    af = "highpass=f=80,afftdn=nr=14:nf=-40,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,loudnorm=I=-14:TP=-1:LRA=9" if EFF.get("audio_clean", True) else "loudnorm=I=-14:TP=-1:LRA=9"
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-i", f"{PROJ}/audio_orig.wav", "-map", "0:v", "-map", "1:a", "-af", af + ",aresample=48000",
        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "film", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "192k", "-shortest", out], stdin=subprocess.PIPE)
    total = int(INFO["duration"] * FPS); n = 0
    while True:
        b = dec.stdout.read(fsz); mb = mdec.stdout.read(fsz)
        if len(b) < fsz or len(mb) < fsz: break
        enc.stdin.write(frame(n / FPS, n, np.frombuffer(b, np.uint8).reshape(SH, SW, 3), np.frombuffer(mb, np.uint8).reshape(SH, SW, 3)).tobytes()); n += 1
        if n % 150 == 0: print(f"   {n}/{total} cuadros", flush=True)
    enc.stdin.close(); enc.wait(); print("OK  video final ->", out)

main()
