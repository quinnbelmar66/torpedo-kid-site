"""Builds the A2 recruitment poster as an editable SVG.

Run with a Python that has segno, fonttools, brotli and Pillow-free deps:
    python build_poster.py <out_dir>
Fonts come from the website build (.astro/fonts); the car drawing and logo
mark use the same geometry as src/components/torpedo.
"""
import base64, html, io, os, sys
import segno
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1]
os.makedirs(os.path.join(OUT, 'fonts'), exist_ok=True)

FORM_URL = 'https://docs.google.com/forms/d/e/1FAIpQLSc4p8znoZhYt5e3m5y8SWBUHf52sX_6h8zfO-Xc7dvbm9TyLg/viewform'

C = dict(charcoal='#252724', cream='#F3F0E8', brass='#A58A5C', burgundy='#8C3830',
         stone='#E8E3D8', warm='#D9D5CC', graphite='#494A44', light='#D8D4C9', lbrass='#C5A979')

# ---- fonts -----------------------------------------------------------------
def load_font(pattern, name):
    d = os.path.join(ROOT, '.astro', 'fonts')
    src = next(os.path.join(d, f) for f in os.listdir(d) if f.startswith(pattern) and f.endswith('.woff2'))
    f = TTFont(src)
    f.flavor = None
    path = os.path.join(OUT, 'fonts', name)
    f.save(path)
    return TTFont(path), path

besley, besley_path = load_font('font-besley', 'Besley-Variable.ttf')
familjen, familjen_path = load_font('font-familjen', 'FamiljenGrotesk-Variable.ttf')

# Static instances: print shops and design tools handle these more reliably than
# variable fonts (Chrome writes variable fonts into PDFs as Type 3).
from fontTools.varLib import instancer
WEIGHT_NAMES = {400: 'Regular', 500: 'Medium', 600: 'SemiBold', 700: 'Bold'}
STATIC = []
for var_path, family, file_stem, weights in ((besley_path, 'Besley', 'Besley', (500,)),
                                              (familjen_path, 'Familjen Grotesk', 'FamiljenGrotesk', (400, 500, 600, 700))):
    for w in weights:
        inst = instancer.instantiateVariableFont(TTFont(var_path), {'wght': w}, updateFontNames=False)
        style = WEIGHT_NAMES[w]
        for rec in inst['name'].names:
            if rec.nameID in (1, 16): rec.string = family
            elif rec.nameID in (2, 17): rec.string = style
            elif rec.nameID == 4: rec.string = f'{family} {style}'
            elif rec.nameID == 6: rec.string = f'{file_stem}-{style}'
        inst['OS/2'].usWeightClass = w
        path = os.path.join(OUT, 'fonts', f'{file_stem}-{style}.ttf')
        inst.save(path)
        STATIC.append((path, family, w))
os.remove(besley_path); os.remove(familjen_path)

def advance(font, text, size, tracking=0.0):
    cmap = font.getBestCmap(); hmtx = font['hmtx'].metrics; upm = font['head'].unitsPerEm
    w = sum(hmtx[cmap.get(ord(ch), cmap[ord(' ')])][0] for ch in text) / upm * size
    return w + tracking * size * max(len(text) - 1, 0)

def wrap(font, text, size, width):
    lines, cur = [], ''
    for word in text.split():
        trial = (cur + ' ' + word).strip()
        if advance(font, trial, size) * 1.04 <= width or not cur:
            cur = trial
        else:
            lines.append(cur); cur = word
    lines.append(cur)
    # avoid a lonely last word: if the last line is very short, rebalance
    if len(lines) >= 2 and advance(font, lines[-1], size) < width * 0.3:
        words = ' '.join(lines[-2:]).split()
        best = min(range(1, len(words)), key=lambda k: abs(advance(font, ' '.join(words[:k]), size) - advance(font, ' '.join(words[k:]), size)))
        lines[-2:] = [' '.join(words[:best]), ' '.join(words[best:])]
    return lines

def esc(s):
    return html.escape(s, quote=False)

def text(x, y, s, size, family, weight, fill, anchor='start', spacing=0, extra=''):
    ls = f' letter-spacing="{spacing:.3f}"' if spacing else ''
    fam = "'Besley', Georgia, serif" if family == 'serif' else "'Familjen Grotesk', Arial, sans-serif"
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{fam}" font-size="{size:.2f}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}"{ls}{extra}>{esc(s)}</text>')

def para(x, y, s, size, family, weight, fill, width, lh):
    font = besley if family == 'serif' else familjen
    lines = wrap(font, s, size, width)
    out = [text(x, y + i * lh, l, size, family, weight, fill) for i, l in enumerate(lines)]
    return '\n'.join(out), y + (len(lines) - 1) * lh

# ---- car geometry (same as the website) ------------------------------------
BODY = ('M24 322 C120 262 300 160 520 148 C760 136 1010 222 1140 336 C1172 364 1182 376 1174 385 '
        'C1168 392 1150 393 1126 393 L150 393 C92 393 44 360 24 322 Z')
UNDER = ('M24 322 C44 360 92 393 150 393 L1126 393 C1150 393 1168 392 1174 385 C1178 380 1177 375 1170 366 '
         'C900 352 340 352 24 322 Z')
REAR_X, FRONT_X, WHEEL_Y, WHEEL_R = 300, 924, 318, 112

def wheel(x):
    bolts = ''.join(f'<circle r="3.5" cx="80" transform="rotate({a})" fill="#77756e"/>' for a in range(0, 360, 60))
    return (f'<g transform="translate({x} {WHEEL_Y}) rotate(-18)">'
            f'<circle r="{WHEEL_R - 1}" fill="#171816" stroke="#69665d" stroke-width="2"/>'
            f'<circle r="92" fill="{C["stone"]}"/>'
            f'<path d="M0 0 L92 0 A92 92 0 0 1 46 79.7 Z" fill="{C["warm"]}"/>'
            f'<path d="M0 0 L-92 0 A92 92 0 0 1 -46 -79.7 Z" fill="{C["cream"]}"/>'
            f'{bolts}<circle r="13" fill="{C["brass"]}"/><circle r="5" fill="{C["charcoal"]}"/></g>')

def car(x, ground_y, width):
    s = width / 1200
    return f'''<g id="car-999" transform="translate({x:.3f} {ground_y - 430 * s:.3f}) scale({s:.5f})">
  <path d="M474 176 C474 138 490 124 522 124 C552 124 566 140 566 176 Z" fill="{C['burgundy']}"/>
  <path d="M492 94 C490 62 512 48 534 50 C558 52 568 68 566 86 L573 99 L565 102 L564 116 C560 130 540 134 524 130 L500 130 Z" fill="#d9c9ab"/>
  <path d="M489 102 C480 62 506 42 534 45 C552 46 564 54 567 70 C548 64 536 68 526 70 C518 80 516 92 510 104 C504 112 494 112 489 102 Z" fill="#171816"/>
  <path d="M542 106 C552 100 566 101 572 110 C562 114 550 114 542 106 Z" fill="#171816"/>
  <path d="{BODY}" fill="{C['cream']}"/>
  <path d="{UNDER}" fill="{C['warm']}"/>
  <path d="M450 156 C490 148 550 146 596 149" fill="none" stroke="{C['graphite']}" stroke-width="10" stroke-linecap="round"/>
  <path d="M690 152 C712 220 712 300 700 364 M430 157 C410 220 408 300 416 360" fill="none" stroke="#c9c4b8" stroke-width="3"/>
  <text x="566" y="322" text-anchor="middle" font-family="'Besley', Georgia, serif" font-size="112" font-weight="500" fill="{C['charcoal']}">999</text>
  {wheel(REAR_X)}{wheel(FRONT_X)}
</g>'''

def mark(x, y, width, fg, bg):
    s = width / 1200
    holes = ''.join(
        f'<circle cx="{cx}" cy="318" r="112" fill="{bg}"/><circle cx="{cx}" cy="318" r="88" fill="{fg}"/>'
        f'<circle cx="{cx}" cy="318" r="22" fill="{bg}"/>' for cx in (REAR_X, FRONT_X))
    return f'<g id="logo-mark" transform="translate({x:.3f} {y - 110 * s:.3f}) scale({s:.5f})"><path d="{BODY}" fill="{fg}"/>{holes}</g>'

# ---- QR code -----------------------------------------------------------------
qr = segno.make(FORM_URL, error='m', micro=False)
matrix = [list(r) for r in qr.matrix]
n = len(matrix)
QUIET = 4

def qr_group(x, y, size):
    total = n + 2 * QUIET
    m = size / total
    runs = []
    for r, row in enumerate(matrix):
        c = 0
        while c < n:
            if row[c]:
                start = c
                while c < n and row[c]:
                    c += 1
                runs.append(f'M{QUIET + start} {QUIET + r}h{c - start}v1h-{c - start}z')
            else:
                c += 1
    return (f'<g id="qr-application-form" transform="translate({x:.3f} {y:.3f})">'
            f'<rect width="{size:.3f}" height="{size:.3f}" fill="#FFFFFF"/>'
            f'<path transform="scale({m:.5f})" d="{"".join(runs)}" fill="{C["charcoal"]}" shape-rendering="crispEdges"/></g>'), m

# ---- layout (mm, trim coordinates; 3 mm bleed added around) -------------------
# Simple recruitment layout: one promise, three plain answers, one action.
W, H, BLEED, M = 420, 594, 3, 30
GROUND = 262            # charcoal / cream line, the car stands on it
BAND = 470              # cream / burgundy line
parts = []

parts.append(f'<rect x="{-BLEED}" y="{-BLEED}" width="{W + 2 * BLEED}" height="{GROUND + BLEED}" fill="{C["charcoal"]}"/>')
parts.append(f'<rect x="{-BLEED}" y="{GROUND}" width="{W + 2 * BLEED}" height="{BAND - GROUND}" fill="{C["cream"]}"/>')
parts.append(f'<rect x="{-BLEED}" y="{BAND}" width="{W + 2 * BLEED}" height="{H - BAND + BLEED}" fill="{C["burgundy"]}"/>')

# header: logo mark + wordmark, project line
parts.append(mark(M, 33.9 - 320 * 26 / 1200, 26, C['cream'], C['charcoal']))
parts.append(text(M + 31, 33.6, 'TorpedoKid', 8.4, 'sans', 600, C['cream']))

# the promise
parts.append(text(M - 1.6, 92, 'Build an', 44, 'serif', 500, C['cream'], spacing=-0.9))
parts.append(text(M - 1.6, 138, 'electric car.', 44, 'serif', 500, C['cream'], spacing=-0.9))
sub = 'Join the Fontys team recreating the 1902 Torpedo Kid.'
block, _ = para(M, 164, sub, 9, 'sans', 400, C['light'], 216, 12.6)
parts.append(block)

# the car, smaller, standing on the dividing line
CAR_W = 232
CAR_X = W - M - CAR_W + 5
parts.append(car(CAR_X, GROUND, CAR_W))

# three plain answers; the roles are the team's subsystems from the 2026-27 report
ROLES = [['Chassis', 'Suspension', 'Steering', 'Brakes and pedals'],
         ['Drive shafts', 'Battery and electronics', 'Wiring and CAN', 'Cooling']]
rows = [
    ('What you’ll do', 'Design, build, and test to get the car driving for the first time.'),
    ('Roles', ROLES),
    ('What you get', 'Hands-on experience on an electric car, working with industry partners. A project that stands out on your CV.'),
]
HEAD_X, BODY_X, BODY_W = M, 160, W - M - 160
HEAD_SIZE, BODY_SIZE, BODY_LH = 15.5, 11, 14.6
COL2_X = BODY_X + 106
assert BODY_X + max(advance(familjen, r, BODY_SIZE) for r in ROLES[0]) + 8 < COL2_X, 'role column 1 too wide'
assert COL2_X + max(advance(familjen, r, BODY_SIZE) for r in ROLES[1]) <= W - M, 'role column 2 too wide'
heights = [(len(v[0]) if isinstance(v, list) else len(wrap(familjen, v, BODY_SIZE, BODY_W))) * BODY_LH for _, v in rows]
top, bottom = GROUND + 24, BAND - 22          # space for the rows, baseline to last descender
gap = (bottom - top - sum(heights)) / (len(rows) - 1)
y = top + BODY_SIZE
for (k, v), h in zip(rows, heights):
    parts.append(text(HEAD_X, y + 1.5, k, HEAD_SIZE, 'serif', 500, C['burgundy'], spacing=-0.3))
    if isinstance(v, list):
        for cx, col in ((BODY_X, v[0]), (COL2_X, v[1])):
            for i, role in enumerate(col):
                parts.append(text(cx, y + i * BODY_LH, role, BODY_SIZE, 'sans', 500, C['charcoal']))
    else:
        block, last = para(BODY_X, y, v, BODY_SIZE, 'sans', 500, C['charcoal'], BODY_W, BODY_LH)
        parts.append(block)
    y += h + gap

# call to action and QR code
QR_SIZE = 100
qx, qy = W - M - QR_SIZE, BAND + 12
qr_svg, module = qr_group(qx, qy, QR_SIZE)
parts.append(qr_svg)

parts.append(text(M - 1.2, BAND + 41, 'JOIN THE TEAM', 27, 'sans', 700, C['cream'], spacing=0.6))
parts.append(text(M, BAND + 62, 'Scan the code to apply.', 12, 'sans', 500, C['cream']))
fy = qy + QR_SIZE
parts.append(text(M, fy, 'torpedokid.nl', 6.4, 'sans', 600, C['cream']))
parts.append(text(M + advance(familjen, 'torpedokid.nl', 6.4) + 10, fy, 'Instagram  @torpedokid_fontys', 6.4, 'sans', 400, C['cream']))

# ---- assemble ------------------------------------------------------------------
def face(path, family, weights):
    data = base64.b64encode(open(path, 'rb').read()).decode()
    return (f"@font-face{{font-family:'{family}';src:url(data:font/ttf;base64,{data}) format('truetype');"
            f"font-weight:{weights};font-style:normal;}}")

svg = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{W + 2 * BLEED}mm" height="{H + 2 * BLEED}mm"
     viewBox="{-BLEED} {-BLEED} {W + 2 * BLEED} {H + 2 * BLEED}">
<title>Torpedo Kid recruitment poster, A2</title>
<desc>A2 portrait, 420 x 594 mm trim with 3 mm bleed on every side. Units are millimetres.
Fonts: Besley Medium and Familjen Grotesk Regular, Medium, SemiBold and Bold (SIL Open Font License), embedded and supplied in fonts/.
QR code: {FORM_URL}</desc>
<defs><style>{''.join(face(p, fam, w) for p, fam, w in STATIC)}</style></defs>
{chr(10).join(parts)}
</svg>'''
open(os.path.join(OUT, 'torpedo-kid-poster-A2.svg'), 'w', encoding='utf-8').write(svg)
print(f'QR version {qr.version}, error level {qr.error}, {n} modules, module {module:.2f} mm, panel {QR_SIZE} mm')
