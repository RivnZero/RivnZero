"""Design system for the RivnZero profile SVGs.

Bento tiles on a transparent canvas, so every widget sits on GitHub's own page
colour. Tiles are filled and borderless, content sits in nested inner cards,
labels are small pill tags. Geist throughout. Colour is rare: cyan accent
(also Go's colour) and amber from the leopard avatar.
"""
from __future__ import annotations

import base64
import io
import re
from functools import lru_cache
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
FONTS = ROOT / "assets" / "fonts"
ICONS = ROOT / "assets" / "icons"
OUT = ROOT / "assets"

# Layout tokens. GAP matches the gutter GitHub leaves between images placed side by side
# or stacked with <br> (one space, about 9px at full width), so grids inside one SVG and grids
# made of several images line up.
W = 880
GAP = 10
R_TILE = 24
R_INNER = 14
PAD = 24

THEMES = {
    "dark": {
        "tile": "#171717", "inner": "#222222", "line": "#2c2c2c",
        "fg": "#f2f2f2", "text2": "#a8a8a8", "text3": "#858585",
        "accent": "#2ccfd2", "on_accent": "#06292a", "warm": "#eaa23f",
        "dots": ["#f2f2f2", "#b4b4b4", "#7a7a7a", "#4a4a4a"],
        "dot_warm": ["#f0b250", "#9a6420"], "dot_accent": "#2ccfd2",
    },
    "light": {
        "tile": "#f4f4f5", "inner": "#ffffff", "line": "#e2e2e5",
        "fg": "#0b0b0b", "text2": "#52525b", "text3": "#68686f",
        "accent": "#0a7d82", "on_accent": "#ffffff", "warm": "#9a5c06",
        "dots": ["#0b0b0b", "#3d3d3d", "#767676", "#b0b0b0"],
        "dot_warm": ["#b06c0e", "#dca35a"], "dot_accent": "#0a7d82",
    },
}

FONT_FILES = {
    "display": "Geist-Medium.woff2",
    "sans": "Geist-Regular.woff2",
    "mono": "GeistMono-Regular.woff2",
}

EASE = "cubic-bezier(.22,1,.36,1)"

BASE_CSS = f"""
.d{{font-family:'GDisplay',Geist,Inter,system-ui,sans-serif;font-weight:500;}}
.s{{font-family:'GSans',Geist,Inter,system-ui,sans-serif;}}
.m{{font-family:'GMono','Geist Mono',ui-monospace,monospace;}}
.rise{{animation:rise 720ms {EASE} both;}}
@keyframes rise{{0%{{opacity:0;transform:translateY(14px);}}}}
.word{{animation:word 900ms {EASE} both;}}
@keyframes word{{0%{{opacity:0;transform:translateY(.32em);filter:blur(10px);}}}}
.fadein{{animation:fadein 1100ms {EASE} both;}}
@keyframes fadein{{0%{{opacity:0;}}}}
.grow{{transform-box:fill-box;transform-origin:left;animation:grow 1200ms {EASE} both;}}
@keyframes grow{{0%{{transform:scaleX(0);}}}}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important;}}}}
"""


@lru_cache(maxsize=None)
def _font(key: str) -> TTFont:
    return TTFont(FONTS / FONT_FILES[key])


def measure(key: str, text: str, size: float, tracking: float = 0.0) -> float:
    f = _font(key)
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = sum(hmtx[cmap.get(ord(ch), cmap[ord("?")])][0] for ch in text) * size / upm
    return w + tracking * len(text)


def wrap(key: str, text: str, size: float, width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if measure(key, trial, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


FAMILY = {"display": "GDisplay", "sans": "GSans", "mono": "GMono"}


def font_faces(used: dict[str, str]) -> str:
    """@font-face rules, each font subset to only the characters used."""
    rules = []
    for key, text in used.items():
        if not text:
            continue
        opts = subset.Options()
        opts.flavor = "woff2"
        opts.layout_features = ["kern", "liga", "calt"]
        opts.name_IDs = []
        opts.notdef_outline = False
        font = TTFont(FONTS / FONT_FILES[key])
        sub = subset.Subsetter(options=opts)
        sub.populate(text="".join(sorted(set(text + " "))))
        sub.subset(font)
        buf = io.BytesIO()
        font.flavor = "woff2"
        font.save(buf)
        b64 = base64.b64encode(buf.getvalue()).decode()
        rules.append(f"@font-face{{font-family:'{FAMILY[key]}';src:url(data:font/woff2;base64,{b64}) format('woff2');}}")
    return "\n".join(rules)


def style(used: dict[str, str], extra: str = "") -> str:
    return f"<style>\n{font_faces(used)}\n{BASE_CSS}\n{extra}\n</style>"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def svg(w: float, h: float, label: str, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:g} {h:g}" width="{w:g}" height="{h:g}" '
            f'role="img" aria-label="{esc(label)}">\n{body}\n</svg>\n')


def words(text: str, x: float, y: float, size: float, fill: str, tracking: float,
          delay0: float = 0.0, step: float = 0.07, cls: str = "d") -> tuple[str, float]:
    """Each word as its own <text> so it can blur in on its own."""
    out, cx = [], x
    space = measure("display", " ", size) * 1.0
    for i, w in enumerate(text.split(" ")):
        out.append(f'<text x="{cx:.1f}" y="{y:.1f}" class="{cls} word" style="animation-delay:{delay0 + i * step:.2f}s" '
                   f'font-size="{size}" letter-spacing="{tracking:.2f}" fill="{fill}">{esc(w)}</text>')
        cx += measure("display", w, size, tracking) + space
    return "".join(out), cx


def tile(c: dict, x: float, y: float, w: float, h: float, delay: float = 0.0, inner: str = "") -> str:
    """A bento tile: filled, borderless, large radius. `inner` is drawn on top."""
    return (f'<g class="rise" style="animation-delay:{delay:.2f}s">'
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{R_TILE}" fill="{c["tile"]}"/>'
            f'{inner}</g>')


def tag(c: dict, x: float, y: float, text: str, dot: str | None = None) -> tuple[str, float]:
    """Small pill label for the top-left of a tile. Returns (svg, width). Uses the 'sans' font."""
    fs, h = 12, 24
    tx = x + (22 if dot else 11)
    w = (tx - x) + measure("sans", text, fs) + 11
    d = f'<circle cx="{x + 12}" cy="{y + h / 2}" r="3" fill="{dot}"/>' if dot else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{c["inner"]}"/>{d}'
            f'<text x="{tx:.1f}" y="{y + 16.2:.1f}" class="s" font-size="{fs}" fill="{c["text2"]}">{esc(text)}</text>', w)


@lru_cache(maxsize=None)
def icon_path(slug: str) -> str:
    """The single path of a Simple Icons glyph (24x24, CC0) from assets/icons."""
    return re.search(r'<path d="([^"]+)"', (ICONS / f"{slug}.svg").read_text(encoding="utf-8")).group(1)


def icon(slug: str, x: float, y: float, size: float, fill: str) -> str:
    return f'<path transform="translate({x:.1f} {y:.1f}) scale({size / 24:g})" d="{icon_path(slug)}" fill="{fill}"/>'


def write(name: str, content: str, out: Path = OUT) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / name).write_text(content, encoding="utf-8")
