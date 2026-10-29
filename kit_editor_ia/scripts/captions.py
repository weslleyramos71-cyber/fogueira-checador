"""Paso 3 — arma los subtítulos (1 a 3 palabras por bloque) a partir de words.json.
Uso: python scripts/captions.py CARPETA_PROYECTO [--fix "Cloud=Claude" --fix "chat GBT=ChatGPT"] [--drop "eh,ah,hum"]
Escribe captions.json: [[inicio, "texto"], ...]. Se puede editar a mano:
  *palabra*  -> color de acento      #palabra# -> azul      %palabra% -> verde
"""
import sys, json, re, argparse

ap = argparse.ArgumentParser()
ap.add_argument("proj"); ap.add_argument("--fix", action="append", default=[]); ap.add_argument("--drop", default="")
args = ap.parse_args()
words = json.load(open(f"{args.proj}/words.json"))
drop = {x.strip().lower() for x in args.drop.split(",") if x.strip()}

# fixes may span several words ("chat GBT=ChatGPT"): apply on the joined text keeping the first word's time
toks = [[t, w] for t, w in words if w.lower().strip(",.!?") not in drop]
for fx in args.fix:
    a, b = fx.split("=", 1); aw = a.split()
    i = 0
    while i <= len(toks) - len(aw):
        seg = [re.sub(r"[,.!?;:]+$", "", toks[i + k][1]) for k in range(len(aw))]
        if [s.lower() for s in seg] == [x.lower() for x in aw]:
            tail = re.search(r"[,.!?;:]+$", toks[i + len(aw) - 1][1])
            toks[i][1] = b + (tail.group(0) if tail else ""); del toks[i + 1: i + len(aw)]
        i += 1
# collapse immediate stutters ("cadeira, cadeira" -> "cadeira")
clean = []
for t, w in toks:
    if clean and re.sub(r"\W", "", clean[-1][1]).lower() == re.sub(r"\W", "", w).lower(): continue
    clean.append([t, w])

caps, cur = [], []
# words that should never end a caption (they belong with the next word)
SMALL = {"a", "o", "e", "de", "da", "do", "em", "no", "na", "que", "y", "el", "la", "los", "las", "en", "un", "una", "con", "com",
         "por", "pra", "para", "se", "me", "te", "mi", "tu", "su", "minha", "meu", "seu", "sua", "esse", "essa", "este", "esta", "eu", "yo"}
bare = lambda w: re.sub(r"[^\w]", "", w).lower()
for i, (t, w) in enumerate(clean):
    if cur:
        prev_t, prev_w = cur[-1]
        text = " ".join(x for _, x in cur + [(t, w)])
        hard = prev_w[-1:] in ".!?" or t - prev_t > 0.9          # sentence end or real pause: always cut
        soft = len(cur) >= 3 or len(text) > 20 or prev_w[-1:] in ",;:"
        if hard or (soft and bare(prev_w) not in SMALL):
            caps.append([cur[0][0], " ".join(x for _, x in cur)]); cur = []
    cur.append((t, w))
if cur: caps.append([cur[0][0], " ".join(x for _, x in cur)])
# a lone short word after a pause joins the next caption when that keeps it short
merged = []
for c in caps:
    if merged and len(merged[-1][1].split()) == 1 and not merged[-1][1].endswith((".", "!", "?")) and len(merged[-1][1] + c[1]) < 22:
        merged[-1] = [merged[-1][0], merged[-1][1] + " " + c[1]]
    else: merged.append(c)
caps = merged
json.dump(caps, open(f"{args.proj}/captions.json", "w"), ensure_ascii=False, indent=1)
for t, s in caps: print(f"{t:6.2f}  {s}")
print(f"\nOK  {len(caps)} subtítulos -> {args.proj}/captions.json")
