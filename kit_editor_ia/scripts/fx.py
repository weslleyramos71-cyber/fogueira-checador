"""Visual effects for the 'edited by Claude' demo: gamer room, gamer chair, recolors, 3D spinning logos, relight."""
import math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SW, SH = 576, 1024  # source resolution

def _blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))).astype(np.float32)

def gamer_room(seed=4):
    """Dark modern gamer room: acoustic wall panels, RGB LED strips, neon hexagons, shelf lights, bokeh. Slight DOF blur."""
    rng = random.Random(seed)
    W, H = SW * 2, SH * 2
    im = Image.new("RGB", (W, H), (14, 12, 22)); d = ImageDraw.Draw(im)
    # wall gradient
    y = np.linspace(0, 1, H)[:, None, None]
    base = np.array([18, 16, 30]) * (1 - y) + np.array([8, 8, 14]) * y
    arr = np.repeat(base, W, 1).astype(np.float32)
    im = Image.fromarray(arr.astype(np.uint8)); d = ImageDraw.Draw(im)
    # vertical acoustic slats
    for x in range(0, W, 46):
        d.rectangle((x, 0, x + 34, H), fill=(22, 20, 34))
        d.line((x + 34, 0, x + 34, H), fill=(10, 9, 16), width=3)
    glow = Image.new("RGB", (W, H), (0, 0, 0)); g = ImageDraw.Draw(glow)
    # ceiling RGB strip
    for i in range(W):
        t = i / W
        col = (int(150 + 100 * t), int(60 + 40 * (1 - t)), 255) if t < 0.5 else (int(80 * (1 - t)), int(200 * t), 255)
        g.line((i, 70, i, 86), fill=col)
    # neon hexagon panels (right) and LED ring (left)
    def hexa(cx, cy, r, col, w=7):
        pts = [(cx + r * math.cos(math.pi / 3 * k + math.pi / 6), cy + r * math.sin(math.pi / 3 * k + math.pi / 6)) for k in range(7)]
        g.line(pts, fill=col, width=w, joint="curve")
    for (cx, cy) in [(930, 520), (1040, 585), (930, 650), (1040, 715), (1150, 650)]:
        hexa(cx, cy, 66, (60, 200, 255))
    hexa(1040, 455, 66, (190, 80, 255))
    g.ellipse((60, 380, 300, 620), outline=(255, 70, 160), width=8)
    # shelf with glowing items (left)
    d.rectangle((40, 820, 360, 836), fill=(40, 36, 58))
    for k in range(5):
        x = 60 + k * 60; h = rng.randint(40, 90)
        d.rectangle((x, 820 - h, x + 36, 820), fill=(30, 28, 46))
        g.rectangle((x + 4, 820 - h + 4, x + 32, 820 - h + 10), fill=rng.choice([(255, 90, 180), (80, 220, 255), (190, 90, 255)]))
    # vertical LED bars at the far edges
    g.rectangle((8, 120, 18, 1500), fill=(140, 70, 255)); g.rectangle((W - 18, 120, W - 8, 1500), fill=(60, 200, 255))
    # desk monitor glow low behind
    g.rectangle((380, 1150, 780, 1170), fill=(80, 140, 255))
    ga = np.asarray(glow).astype(np.float32)
    light = _blur(ga, 26) * 1.4 + _blur(ga, 6) * 0.9 + ga * 0.9
    out = np.asarray(im).astype(np.float32) + light
    # bokeh dots
    lay = Image.new("RGB", (W, H), (0, 0, 0)); bd = ImageDraw.Draw(lay)
    for _ in range(40):
        r = rng.uniform(6, 22); x = rng.uniform(0, W); yy = rng.uniform(100, 1400)
        bd.ellipse((x - r, yy - r, x + r, yy + r), fill=rng.choice([(90, 40, 140), (30, 90, 130), (120, 30, 80)]))
    out += _blur(np.asarray(lay).astype(np.float32), 5)
    # floor fade
    fy = np.clip((np.linspace(0, 1, H) - 0.72) / 0.28, 0, 1)[:, None, None]
    out = out * (1 - 0.55 * fy)
    img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(5))
    return np.asarray(img.resize((SW, SH), Image.LANCZOS)).astype(np.float32)

def gamer_chair():
    """Backrest of a gamer chair (RGBA, source resolution), meant to sit behind the shoulders."""
    W, H = SW * 2, SH * 2
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx = W * 0.5; top = H * 0.115
    # wings + main backrest
    body = [(cx - 250, top + 120), (cx - 330, top + 420), (cx - 300, top + 760), (cx - 360, H), (cx + 360, H),
            (cx + 300, top + 760), (cx + 330, top + 420), (cx + 250, top + 120), (cx + 170, top), (cx - 170, top)]
    d.polygon(body, fill=(22, 22, 26, 255))
    # red side panels
    for s in (-1, 1):
        d.polygon([(cx + s * 250, top + 120), (cx + s * 330, top + 420), (cx + s * 300, top + 760), (cx + s * 360, H),
                   (cx + s * 290, H), (cx + s * 240, top + 760), (cx + s * 262, top + 420), (cx + s * 200, top + 110)], fill=(196, 28, 40, 255))
    # headrest opening slots
    for s in (-1, 1):
        d.rounded_rectangle((cx + s * 95 - 28, top + 60, cx + s * 95 + 28, top + 160), 26, fill=(0, 0, 0, 0))
    # stitching
    for s in (-1, 1):
        d.line([(cx + s * 175, top + 30), (cx + s * 240, top + 420), (cx + s * 215, top + 760), (cx + s * 260, H)], fill=(70, 70, 80, 255), width=4)
    arr = np.asarray(im).astype(np.float32)
    # leather shading: darker toward the edges, soft highlight on the upper middle
    yy, xx = np.mgrid[0:H, 0:W]
    shade = 1 - 0.45 * np.clip(np.abs(xx - cx) / 360, 0, 1) ** 2 + 0.25 * np.exp(-(((xx - cx) / 200) ** 2 + ((yy - top - 260) / 300) ** 2))
    arr[..., :3] *= shade[..., None]
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))
    return np.asarray(img.resize((SW, SH), Image.LANCZOS)).astype(np.float32)

def recolor(fr, mask, target, keep_bright=True):
    """Re-dye dark fabric to `target` keeping its texture; spare bright prints and saturated jewellery."""
    f = fr / 255.0
    L = f @ np.array([0.299, 0.587, 0.114])
    sat = f.max(2) - f.min(2)
    m = mask.copy()
    if keep_bright:
        m *= np.clip((0.55 - L) / 0.2, 0, 1)        # prints / logos stay
        m *= np.clip((0.28 - sat) / 0.12, 0, 1)     # gold chain / skin stay
    t = np.array(target, np.float32) / 255
    dyed = np.clip(t[None, None, :] * (0.30 + 2.6 * L[..., None]) + 0.10 * L[..., None], 0, 1)
    return (f * (1 - m[..., None]) + dyed * m[..., None]) * 255

def relight(person, alpha, bg):
    """Match the subject to the dark RGB room: cooler grade, slight darkening, coloured rim light from the background."""
    p = person.astype(np.float32)
    p = p * np.array([0.86, 0.88, 0.98]) * 0.92
    a = alpha / 255.0
    edge = np.clip(_blur(alpha, 3) / 255.0 - _blur(alpha, 10) / 255.0, 0, 1) * 0 + np.clip(a - _blur(alpha, 8) / 255.0, 0, 1)
    rim = _blur(bg, 20) * 2.2
    p = p + rim * edge[..., None] * 1.6
    # light wrap
    wrap = np.clip(1 - _blur(alpha, 6) / 255.0, 0, 1) * a
    p = p * (1 - 0.35 * wrap[..., None]) + _blur(bg, 12) * 0.35 * wrap[..., None]
    return np.clip(p, 0, 255)

# ---------- 3D spinning logos ----------
def claude_logo(S=256):
    """Claude spark: coral rays of uneven length radiating from the centre."""
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    c = S / 2; n = 12
    lens = [0.46, 0.38, 0.44, 0.36, 0.47, 0.40, 0.45, 0.37, 0.46, 0.39, 0.43, 0.38]
    for k in range(n):
        a = k * 2 * math.pi / n + 0.12
        L = lens[k] * S; w = S * 0.055
        tip = (c + L * math.cos(a), c + L * math.sin(a))
        p1 = (c + w * math.cos(a + math.pi / 2), c + w * math.sin(a + math.pi / 2))
        p2 = (c + w * math.cos(a - math.pi / 2), c + w * math.sin(a - math.pi / 2))
        d.polygon([p1, tip, p2], fill=(217, 119, 87, 255))
        d.ellipse((tip[0] - w * 0.6, tip[1] - w * 0.6, tip[0] + w * 0.6, tip[1] + w * 0.6), fill=(217, 119, 87, 255))
    d.ellipse((c - S * 0.09, c - S * 0.09, c + S * 0.09, c + S * 0.09), fill=(217, 119, 87, 255))
    return im

def chatgpt_logo(S=256):
    """ChatGPT-style badge: green disc with a white hexagonal knot."""
    ss = 4; B = S * ss
    im = Image.new("RGBA", (B, B), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, B - 1, B - 1), fill=(16, 163, 127, 255))
    c = B / 2; R = B * 0.24; w = B * 0.055
    for k in range(6):
        a = k * math.pi / 3
        # each petal: a rounded capsule tangent to the inner hexagon
        x0 = c + R * 0.55 * math.cos(a); y0 = c + R * 0.55 * math.sin(a)
        dx, dy = math.cos(a + math.pi / 2), math.sin(a + math.pi / 2)
        p = [(x0 - dx * R * 0.95, y0 - dy * R * 0.95), (x0 + dx * R * 0.6, y0 + dy * R * 0.6)]
        d.line(p, fill=(255, 255, 255, 255), width=int(w))
        for q in p: d.ellipse((q[0] - w / 2, q[1] - w / 2, q[0] + w / 2, q[1] + w / 2), fill=(255, 255, 255, 255))
    return im.resize((S, S), Image.LANCZOS)

def spin_frame(face, ang, size, thick=0.10):
    """Render a coin-like 3D spin of `face` at rotation `ang` (radians) into an RGBA sprite of width ~size."""
    f = face.resize((size, size), Image.LANCZOS)
    c = math.cos(ang); s = math.sin(ang)
    w = max(2, int(abs(c) * size))
    front = f.resize((w, size), Image.LANCZOS)
    if c < 0: front = front.transpose(Image.FLIP_LEFT_RIGHT)
    fa = np.asarray(front).astype(np.float32)
    # shading: facing the light when c > 0
    fa[..., :3] *= (0.55 + 0.45 * abs(c))
    W = size + int(size * thick) + 8; out = Image.new("RGBA", (W, size + 8), (0, 0, 0, 0))
    # edge thickness: dark copies shifted sideways
    depth = int(abs(s) * size * thick)
    edge = Image.fromarray(fa.astype(np.uint8)); ea = np.asarray(edge).astype(np.float32); ea[..., :3] *= 0.45
    edge = Image.fromarray(ea.astype(np.uint8))
    x0 = (W - w) // 2
    for k in range(depth, 0, -1):
        out.alpha_composite(edge, (x0 + int(k * np.sign(s)), 4))
    fr_ = Image.fromarray(fa.astype(np.uint8))
    # specular sweep
    spec = np.zeros((size, w), np.float32)
    xs = np.linspace(-1, 1, w)[None, :]
    spec[:] = np.exp(-((xs - (s * 0.8)) / 0.18) ** 2) * 120
    fa2 = np.asarray(fr_).astype(np.float32); fa2[..., :3] += spec[..., None] * (fa2[..., 3:4] / 255)
    out.alpha_composite(Image.fromarray(np.clip(fa2, 0, 255).astype(np.uint8)), (x0, 4))
    return out

def glow_sprite(spr, r, col, a=0.8):
    pad = r * 2
    out = Image.new("RGBA", (spr.width + 2 * pad, spr.height + 2 * pad), (0, 0, 0, 0))
    m = Image.new("L", out.size, 0); m.paste(spr.split()[3], (pad, pad))
    g = Image.new("RGBA", out.size, col + (0,)); g.putalpha(m.filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * a)))
    out.alpha_composite(g); out.alpha_composite(spr, (pad, pad))
    return out

# ---------- v2: better colour ----------
def grade_person(fr):
    """Neutralise the warm wall cast, gentle S-curve and vibrance that protects skin."""
    f = fr / 255.0
    f = f * np.array([0.97, 1.0, 1.05])                      # white balance: less yellow
    f = np.clip(f, 0, 1)
    f = f + 0.07 * np.sin(2 * np.pi * (f - 0.5)) * -0.5 * 2 * (f * (1 - f)) * 4  # soft S-curve
    f = np.clip(0.5 + (f - 0.5) * 1.07, 0, 1)
    l = f.mean(2, keepdims=True); sat = f.max(2, keepdims=True) - f.min(2, keepdims=True)
    f = l + (f - l) * (1 + 0.22 * (1 - np.clip(sat * 3, 0, 1)))
    return np.clip(f, 0, 1) * 255

def recolor2(fr, mask, target):
    """Dye fabric keeping folds: remap the fabric's own (denoised) luminance onto a dark->light ramp of the target hue."""
    f = fr / 255.0
    L = f @ np.array([0.299, 0.587, 0.114])
    Ls = _blur(L * 255, 1.4) / 255                       # tame JPEG blocks before stretching
    sat = f.max(2) - f.min(2)
    m = mask * np.clip((0.62 - L) / 0.14, 0, 1) * np.clip((0.24 - sat) / 0.10, 0, 1)
    ridge = L - _blur(L * 255, 4) / 255              # thin bright lines (chains) stay untouched
    m = m * np.clip((0.035 - ridge) / 0.025, 0, 1)
    sel = m > 0.5
    if sel.sum() < 50: return fr
    lo, hi = np.percentile(Ls[sel], 2), np.percentile(Ls[sel], 99.5)
    ln = np.clip((Ls - lo) / max(1e-3, hi - lo), 0, 1) ** 0.9
    t = np.array(target, np.float32) / 255
    dark, light = t * 0.34, np.clip(t * 1.35 + 0.05, 0, 1)
    dyed = dark[None, None] * (1 - ln[..., None]) + light[None, None] * ln[..., None]
    m = _blur(m * 255, 1.0) / 255
    return (f * (1 - m[..., None]) + dyed * m[..., None]) * 255

def relight2(person, alpha, bg):
    p = person.astype(np.float32) * np.array([0.97, 0.98, 1.02])
    a = alpha / 255.0
    edge = np.clip(a - _blur(alpha, 8) / 255.0, 0, 1)
    rim = _blur(bg, 20) * 2.0
    p = p + rim * edge[..., None] * 1.5
    wrap = np.clip(1 - _blur(alpha, 6) / 255.0, 0, 1) * a
    p = p * (1 - 0.3 * wrap[..., None]) + _blur(bg, 12) * 0.3 * wrap[..., None]
    return np.clip(p, 0, 255)
