"""Builds the static profile SVGs: hero, buttons, section headings, toolbox, more-tile, footer.

Run after editing: python scripts/build_assets.py   (needs fonttools, brotli, pillow)
The live cards (projects, stats) are built daily by scripts/refresh.py.
"""
from __future__ import annotations

import base64
import io

from PIL import Image

from common import (GAP, OUT, PAD, R_INNER, R_TILE, THEMES, W, esc, icon, measure, style, svg, tag, tile,
                    words, write)
from dither import dither, smoothstep

AVATAR = OUT / "avatar.jpg"
HIRO = OUT / "hiro.jpg"
HALF = (W - GAP) / 2


# ------------------------------------------------------------------------ hero

def hero(t: str) -> str:
    c = THEMES[t]
    H = 400
    side = 280
    lw = W - GAP - side
    x0 = 36
    l1, l2 = "I turn ideas into", "real, working software."
    lede = ["Go backends, messenger bots, web apps and automation", "that takes the repetitive work off your hands."]
    cmd = "gh repo list RivnZero --source"
    info = [("Based in", "Shahreza, Iran"), ("Now building", "Private projects")]

    t1, w1 = tag(c, x0, 36, "@RivnZero", c["accent"])
    t2, _ = tag(c, x0 + w1 + 6, 36, "Backend & full-stack")

    size, track = 46, -46 * 0.035
    h1, _ = words(l1, x0 - 2, 156, size, c["fg"], track, 0.15)
    h2, _ = words(l2, x0 - 2, 206, size, c["text3"], track, 0.15 + 2 * 0.07)
    lede_svg = "".join(
        f'<text x="{x0}" y="{252 + i * 23}" class="s rise" style="animation-delay:{0.36 + i * 0.06:.2f}s" '
        f'font-size="15.5" fill="{c["text2"]}">{esc(s)}</text>' for i, s in enumerate(lede))

    # command, as an inner card pinned to the bottom of the tile
    cy, ch = H - 36 - 44, 44
    cw = lw - 2 * x0
    ix = x0 + cw - 34
    cmd_svg = (
        f'<g class="rise" style="animation-delay:.5s">'
        f'<rect x="{x0}" y="{cy}" width="{cw}" height="{ch}" rx="{R_INNER}" fill="{c["inner"]}"/>'
        f'<text x="{x0 + 18}" y="{cy + 27}" class="m" font-size="13" fill="{c["text3"]}">$ '
        f'<tspan fill="{c["fg"]}">{esc(cmd)}</tspan></text>'
        f'<rect x="{ix + 4:.1f}" y="{cy + 17}" width="9" height="10" rx="2" fill="none" stroke="{c["text3"]}" stroke-width="1.2"/>'
        f'<path d="M{ix + 7:.1f} {cy + 15.5}v-.5a1.5 1.5 0 0 1 1.5-1.5h5.5a1.5 1.5 0 0 1 1.5 1.5v6a1.5 1.5 0 0 1-1.5 1.5h-.5" '
        f'fill="none" stroke="{c["text3"]}" stroke-width="1.2"/></g>')

    # avatar tile: the leopard, dithered, fading out toward the bottom where its name tag sits
    ax, ah = lw + GAP, 268
    dots = dither(AVATAR, c, ax - 30, -20, 330, 3, 2, lambda x, y: 1 - 0.85 * smoothstep(150, 262, y))
    name_tag, _ = tag(c, ax + 20, ah - 44, "Rivn")

    # info tile
    iy = ah + GAP
    ih = H - iy
    info_svg = ""
    # two spec rows: label left, value right, a hairline between
    for i, (k, v) in enumerate(info):
        y = iy + ih / 2 + (i - 0.5) * 40 + 5
        info_svg += (f'<text x="{ax + PAD}" y="{y:.1f}" class="s" font-size="13" fill="{c["text3"]}">{esc(k)}</text>'
                     f'<text x="{ax + side - PAD}" y="{y:.1f}" text-anchor="end" class="d" font-size="15" '
                     f'letter-spacing="-.2" fill="{c["fg"]}">{esc(v)}</text>')
    info_svg += f'<path d="M{ax + PAD} {iy + ih / 2:.1f}h{side - 2 * PAD}" stroke="{c["line"]}"/>'

    used = {"display": l1 + l2 + "".join(v for _, v in info),
            "sans": "@RivnZeroBackend & full-stackRivn" + "".join(lede) + "".join(k for k, _ in info),
            "mono": "$ " + cmd}
    body = f"""<defs>{style(used)}
<clipPath id="av"><rect x="{ax}" width="{side}" height="{ah}" rx="{R_TILE}"/></clipPath></defs>
{tile(c, 0, 0, lw, H, 0, t1 + t2)}
{h1}{h2}
{lede_svg}
{cmd_svg}
{tile(c, ax, 0, side, ah, .08)}
<g clip-path="url(#av)" class="fadein" style="animation-delay:.15s">{dots}</g>
<g class="rise" style="animation-delay:.3s">{name_tag}</g>
{tile(c, ax, iy, side, ih, .16, info_svg)}"""
    return svg(W, H, f"RivnZero. {l1} {l2} {' '.join(lede)} Based in Shahreza, Iran. Now building private projects.", body)


# --------------------------------------------------------------------- buttons

ARROW = "M0 0h9M5 -4l4 4l-4 4"
PLANE = "M0 4.4L10.5 0 8 9.5 5 6.6zM5 6.6L10.5 0M5 6.6v3l1.6-1.6"


def button(t: str, label: str, primary: bool, icon_d: str, icon_dy: float) -> str:
    c = THEMES[t]
    h, pad, fs = 44, 20, 14.5
    tw = measure("display", label, fs)
    w = pad * 2 + tw + 20
    bg, fg = (c["fg"], c["tile"]) if primary else (c["tile"], c["fg"])
    stroke = fg if primary else c["accent"]
    body = f"""<defs>{style({'display': label})}</defs>
<rect width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{bg}"/>
<text x="{pad}" y="{h / 2 + 5}" class="d" font-size="{fs}" fill="{fg}">{esc(label)}</text>
<path transform="translate({pad + tw + 10:.1f} {h / 2 + icon_dy})" d="{icon_d}" fill="none" stroke="{stroke}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>"""
    return svg(round(w, 1), h, label, body)


# --------------------------------------------------------------------- headings

HEADINGS = [
    ("projects", "Projects", "Bots, bridges and developer tools, mostly in Go."),
    ("toolbox", "Toolbox", "Languages, frameworks and the infrastructure underneath."),
    ("activity", "Activity", "Refreshed every day by a GitHub Action."),
]


def heading(t: str, idx: int, title: str, lede: str) -> str:
    c = THEMES[t]
    H = 84
    size, track = 28, -28 * 0.03
    ws, _ = words(title, 4, 38, size, c["fg"], track)
    num = f"{idx:02d} / {len(HEADINGS):02d}"
    body = f"""<defs>{style({'display': title, 'sans': lede, 'mono': num})}</defs>
{ws}
<text x="{W - 4}" y="36" text-anchor="end" class="m rise" font-size="12" fill="{c['text3']}">{num}</text>
<text x="4" y="68" class="s rise" style="animation-delay:.15s" font-size="15" fill="{c['text2']}">{esc(lede)}</text>"""
    return svg(W, H, f"{title}. {lede}", body)


# ---------------------------------------------------------------------- toolbox
# Only what RivnZero lists on their profile or uses in their public projects.

FEATURE = ("Languages", [("go", "Go"), ("rust", "Rust"), ("typescript", "TypeScript"), ("javascript", "JavaScript"),
                         ("python", "Python")])
LISTS = [
    ("Data", [("postgresql", "PostgreSQL", ""), ("mysql", "MySQL", ""), ("sqlite", "SQLite", "")]),
    ("Web", [("nodedotjs", "Node.js", ""), ("react", "React", ""), ("nextdotjs", "Next.js", ""),
             ("tailwindcss", "Tailwind CSS", "")]),
    ("Ops", [("docker", "Docker", ""), ("git", "Git", ""), ("githubactions", "GitHub Actions", ""),
             ("linux", "Linux", "")]),
    ("Platforms", [("telegram", "Telegram", "Bot API"), ("discord", "Discord", "Webhooks")]),
]


def icon_list(c: dict, x: float, y: float, h: float, items: list) -> str:
    """Rows of icon chip + name, centred vertically in the space below the tag."""
    step = 44 if any(s for _, _, s in items) else 36
    top = y + 60 + (h - 60 - 16 - len(items) * step) / 2
    out = []
    for i, (slug, name, sub) in enumerate(items):
        ry = top + i * step + step / 2
        out.append(f'<rect x="{x + PAD}" y="{ry - 15:.1f}" width="30" height="30" rx="9" fill="{c["inner"]}"/>'
                   + icon(slug, x + PAD + 7, ry - 8, 16, c["fg"]))
        if sub:
            out.append(f'<text x="{x + PAD + 42}" y="{ry - 2:.1f}" class="s" font-size="14.5" fill="{c["fg"]}">{esc(name)}</text>'
                       f'<text x="{x + PAD + 42}" y="{ry + 14:.1f}" class="s" font-size="12" fill="{c["text3"]}">{esc(sub)}</text>')
        else:
            out.append(f'<text x="{x + PAD + 42}" y="{ry + 5:.1f}" class="s" font-size="14.5" fill="{c["fg"]}">{esc(name)}</text>')
    return "".join(out)


def toolbox(t: str) -> str:
    c = THEMES[t]
    col = (W - 2 * GAP) / 3
    h1, h2 = 196, 224
    parts, n = [], 0

    # row 1: the languages, large, with Go (the primary one) in the accent colour
    fw = 2 * col + GAP
    ftag, _ = tag(c, PAD, PAD, FEATURE[0])
    slot = (fw - 2 * PAD) / len(FEATURE[1])
    feat = ""
    for i, (slug, name) in enumerate(FEATURE[1]):
        cx = PAD + slot * i + slot / 2
        primary = i == 0
        feat += (f'<rect x="{cx - 30:.1f}" y="68" width="60" height="60" rx="18" fill="{c["accent"] if primary else c["inner"]}"/>'
                 + icon(slug, cx - 15, 83, 30, c["on_accent"] if primary else c["fg"])
                 + f'<text x="{cx:.1f}" y="158" text-anchor="middle" class="s" font-size="14.5" fill="{c["fg"]}">{esc(name)}</text>')
    parts.append(tile(c, 0, 0, fw, h1, 0, ftag + feat))

    xs = [fw + GAP, 0, col + GAP, 2 * (col + GAP)]
    ys = [0, h1 + GAP, h1 + GAP, h1 + GAP]
    hs = [h1, h2, h2, h2]
    for (label, items), x, y, h in zip(LISTS, xs, ys, hs):
        n += 1
        tg, _ = tag(c, x + PAD, y + PAD, label)
        parts.append(tile(c, x, y, col, h, n * 0.05, tg + icon_list(c, x, y, h, items)))

    H = h1 + GAP + h2
    names = [n for _, n in FEATURE[1]] + [n for _, its in LISTS for _, n, _ in its]
    sans = "".join(names) + "".join(s for _, its in LISTS for *_, s in its) + FEATURE[0] + "".join(l for l, _ in LISTS)
    body = f"<defs>{style({'sans': sans})}</defs>\n" + "\n".join(parts)
    return svg(W, H, "Toolbox: " + ", ".join(names), body)


# -------------------------------------------------------------- more-repos tile
# Same size as the small project cards from refresh.py, so it completes their grid.

CARD_H = 196


def more_tile(t: str) -> str:
    c = THEMES[t]
    title, lede = "More on GitHub", "Forks, experiments and everything else."
    tg, _ = tag(c, PAD, PAD, "Repositories")
    cx, cy = HALF - PAD - 22, PAD + 22
    arrow = (f'<circle cx="{cx}" cy="{cy}" r="22" fill="{c["inner"]}"/>'
             f'<path d="M{cx - 5} {cy + 5}l10-10M{cx - 3} {cy - 5}h8v8" fill="none" stroke="{c["fg"]}" '
             f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>')
    body = f"""<defs>{style({'display': title, 'sans': lede + 'Repositories'})}</defs>
{tile(c, 0, 0, HALF, CARD_H, 0, tg + arrow +
      f'<text x="{PAD}" y="{CARD_H - 56}" class="d" font-size="21" letter-spacing="-.4" fill="{c["fg"]}">{esc(title)}</text>'
      f'<text x="{PAD}" y="{CARD_H - 30}" class="s" font-size="14" fill="{c["text2"]}">{esc(lede)}</text>')}"""
    return svg(HALF, CARD_H, f"{title}. {lede}", body)


# ----------------------------------------------------------------------- footer

def footer(t: str) -> str:
    c = THEMES[t]
    H = 260
    l1, l2, note = "Not Hiro Hamada.", "Still inventing.", "See you in the next build."
    # Hiro on the left, feathered into the tile: the hero's composition, mirrored
    pw = 380
    im = Image.open(HIRO).convert("RGB")
    im = im.crop((0, 0, im.width, round(im.width * H / pw))).resize((pw * 2, H * 2), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=80, optimize=True, progressive=True)
    photo = base64.b64encode(buf.getvalue()).decode()
    size, track, right = 34, -34 * 0.034, W - 48
    w1, _ = words(l1, right - measure("display", l1, size, track), 118, size, c["fg"], track, 0.2)
    w2, _ = words(l2, right - measure("display", l2, size, track), 160, size, c["text3"], track, 0.2 + 3 * 0.07)
    rule = right - measure("sans", note, 15) - 12 - 22  # a short accent stroke, like a sign-off
    body = f"""<defs>{style({'display': l1 + l2, 'sans': note})}
<clipPath id="f"><rect width="{W}" height="{H}" rx="{R_TILE}"/></clipPath>
<linearGradient id="fade"><stop offset=".45" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<mask id="m"><rect width="{pw}" height="{H}" fill="url(#fade)"/></mask></defs>
{tile(c, 0, 0, W, H)}
<g clip-path="url(#f)"><image class="fadein" mask="url(#m)" width="{pw}" height="{H}" preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{photo}"/></g>
{w1}{w2}
<g class="rise" style="animation-delay:.5s"><path d="M{rule:.1f} 194h22" stroke="{c['accent']}" stroke-width="1.5" stroke-linecap="round"/>
<text x="{right}" y="199" text-anchor="end" class="s" font-size="15" fill="{c['text2']}">{esc(note)}</text></g>"""
    return svg(W, H, f"{l1} {l2} {note}", body)


def main() -> None:
    for t in ("dark", "light"):
        write(f"hero-{t}.svg", hero(t))
        write(f"btn-projects-{t}.svg", button(t, "Browse projects", True, ARROW, 0))
        write(f"btn-telegram-{t}.svg", button(t, "Message on Telegram", False, PLANE, -5))
        for i, (slug, title, lede) in enumerate(HEADINGS, 1):
            write(f"h-{slug}-{t}.svg", heading(t, i, title, lede))
        write(f"toolbox-{t}.svg", toolbox(t))
        write(f"more-{t}.svg", more_tile(t))
        write(f"footer-{t}.svg", footer(t))
    print("built static assets")


if __name__ == "__main__":
    main()
