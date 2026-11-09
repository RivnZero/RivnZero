"""Builds the live profile cards from GitHub data. Run daily by .github/workflows/profile.yml.

Writes to $DIST (default ./dist):
  card-<repo>-<theme>.svg   project cards with live star counts (the first one is the wide feature card)
  stats-<theme>.svg         stars, contributions, followers, projects, languages
Env: GITHUB_TOKEN, GH_USER (default RivnZero)
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import GAP, PAD, R_INNER, THEMES, W, esc, icon, measure, style, svg, tag, tile, wrap, write  # noqa: E402

USER = os.environ.get("GH_USER", "RivnZero")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
DIST = Path(os.environ.get("DIST", Path(__file__).resolve().parent.parent / "dist"))

HALF = (W - GAP) / 2
CARD_H = 196  # matches more_tile() in build_assets.py

# (repo, display name, language tag, description, meta). The first is drawn as the wide feature card.
PROJECTS = [
    ("telegram-bale-bridge", "Telegram–Bale Bridge", "Go",
     "Forwards text, photos, videos, voice, GIFs and albums between a Telegram chat and a Bale chat, "
     "both ways, with retries, ordered delivery and SQLite-backed deduplication.", "Go 1.26 · SQLite · Docker"),
    ("statisfy", "Statisfy", "Go",
     "One command for usage, quotas, limits and costs across Codex, Gemini, Copilot and other AI coding tools.",
     "Go · CLI"),
    ("dhook", "dhook", "Go",
     "A zero-dependency Discord webhook client for Go, with multi-URL routing, rate-limit handling and queues.",
     "Go · Library"),
    ("FREE-MYKET-DOWNLOADER", "Myket Downloader", "Python",
     "Saves Myket.ir videos as MP4 by resolving their HLS streams and handing them to FFmpeg.",
     "Python · JavaScript"),
]

# Markup isn't a language you write apps in. Forks are already excluded in collect().
LANG_SKIP = {"MDX", "HTML", "CSS", "SCSS", "Makefile", "Dockerfile", "Shell", "PowerShell", "Batchfile", "Nix", "Inno Setup"}

STAR = "M7 1.2l1.75 3.55 3.92.57-2.84 2.76.67 3.9L7 10.13 3.5 11.98l.67-3.9L1.33 5.32l3.92-.57z"


def api(url: str, body: dict | None = None):
    req = urllib.request.Request(
        url if url.startswith("http") else f"https://api.github.com{url}",
        data=json.dumps(body).encode() if body else None,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-refresh",
                 **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def collect() -> dict:
    user = api(f"/users/{USER}")
    repos, page = [], 1
    while True:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        repos += batch
        if len(batch) < 100:
            break
        page += 1
    own = [r for r in repos if not r["fork"] and not r["archived"] and r["name"].lower() != USER.lower()]
    langs: dict[str, int] = {}
    for r in own:
        for k, v in api(f"/repos/{USER}/{r['name']}/languages").items():
            if k not in LANG_SKIP:
                langs[k] = langs.get(k, 0) + v
    contrib = None
    if TOKEN:
        q = {"query": f'{{user(login:"{USER}"){{contributionsCollection{{contributionCalendar{{totalContributions}}}}}}}}'}
        try:
            contrib = api("https://api.github.com/graphql", q)["data"]["user"]["contributionsCollection"][
                "contributionCalendar"]["totalContributions"]
        except Exception as e:  # optional metric: the tile shows "—" instead of failing the whole refresh
            print(f"contributions unavailable: {e}", file=sys.stderr)
    return {"stars": {r["name"]: r["stargazers_count"] for r in own},
            "total_stars": sum(r["stargazers_count"] for r in own),
            "followers": user["followers"], "repos": len(own), "contrib": contrib, "langs": langs}


def fmt(n: int | None) -> str:
    if n is None:
        return "—"
    return f"{n / 1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def stars_svg(c: dict, n: int, right: float, y: float) -> tuple[str, str]:
    label = fmt(n)
    tw = measure("sans", label, 13)
    x = right - tw
    return (f'<path transform="translate({x - 19:.1f} {y - 11.5})" d="{STAR}" fill="none" stroke="{c["text3"]}" '
            f'stroke-width="1.2" stroke-linejoin="round"/>'
            f'<text x="{right}" y="{y}" text-anchor="end" class="s" font-size="13" fill="{c["text2"]}">{label}</text>', label)


def fit(desc: str, size: float, width: float, max_lines: int) -> list[str]:
    """Wrap a description, refusing to silently drop text that doesn't fit the card."""
    lines = wrap("sans", desc, size, width)
    assert len(lines) <= max_lines, f"description needs {len(lines)} lines, card has {max_lines}: {desc}"
    return lines


def lang_dot(c: dict, lang: str) -> str:
    return c["accent"] if lang == "Go" else c["warm"]


def card(t: str, name: str, lang: str, desc: str, meta: str, n: int) -> str:
    c = THEMES[t]
    lines = fit(desc, 14, HALF - 2 * PAD, 2)
    tg, _ = tag(c, PAD, PAD, lang, lang_dot(c, lang))
    st, label = stars_svg(c, n, HALF - PAD, PAD + 17)
    inner = (tg + st
             + f'<text x="{PAD}" y="96" class="d" font-size="21" letter-spacing="-.4" fill="{c["fg"]}">{esc(name)}</text>'
             + "".join(f'<text x="{PAD}" y="{122 + i * 20}" class="s" font-size="14" fill="{c["text2"]}">{esc(s)}</text>'
                       for i, s in enumerate(lines))
             + f'<text x="{PAD}" y="{CARD_H - PAD}" class="m" font-size="11.5" fill="{c["text3"]}">{esc(meta)}</text>')
    used = {"display": name, "sans": lang + desc + label, "mono": meta}
    return svg(HALF, CARD_H, f"{name}: {desc} {label} stars", f"<defs>{style(used)}</defs>\n{tile(c, 0, 0, HALF, CARD_H, 0, inner)}")


def bridge_card(t: str, name: str, lang: str, desc: str, meta: str, n: int) -> str:
    """The wide feature card: text on the left, a small live diagram of the bridge on the right."""
    c = THEMES[t]
    H = 264
    dw = 352
    dx, dy, dh = W - PAD - dw, PAD, H - 2 * PAD
    tw = dx - 2 * PAD - 16
    lines = fit(desc, 15, tw, 3)
    t1, w1 = tag(c, PAD, PAD, "Featured", c["accent"])
    t2, _ = tag(c, PAD + w1 + 6, PAD, lang)
    st, label = stars_svg(c, n, dx - 24, PAD + 17)
    left = (t1 + t2 + st
            + f'<text x="{PAD}" y="112" class="d" font-size="28" letter-spacing="-.8" fill="{c["fg"]}">{esc(name)}</text>'
            + "".join(f'<text x="{PAD}" y="{144 + i * 22}" class="s" font-size="15" fill="{c["text2"]}">{esc(s)}</text>'
                      for i, s in enumerate(lines))
            + f'<text x="{PAD}" y="{H - PAD - 2}" class="m" font-size="12" fill="{c["text3"]}">{esc(meta)}</text>')

    # diagram: Telegram ⇄ Bale, with messages flowing both ways
    nw, nh = 116, 46
    ax, bx = dx + 22, dx + dw - 22 - nw
    ny = dy + 46
    mid = ny + nh / 2

    def node(x: float, label: str, ic: str | None) -> str:
        mark = (icon(ic, x + 16, mid - 8, 16, c["fg"]) if ic else
                f'<circle cx="{x + 24}" cy="{mid}" r="7" fill="none" stroke="{c["fg"]}" stroke-width="1.5"/>')
        return (f'<rect x="{x}" y="{ny}" width="{nw}" height="{nh}" rx="{nh / 2}" fill="{c["tile"]}"/>{mark}'
                f'<text x="{x + 42}" y="{mid + 5}" class="s" font-size="14" fill="{c["fg"]}">{label}</text>')

    l0, l1 = ax + nw + 10, bx - 10
    flows = (f'<path class="flow" d="M{l0} {mid - 7}H{l1}" stroke="{c["accent"]}"/>'
             f'<path d="M{l1 - 5} {mid - 11}l5 4-5 4" fill="none" stroke="{c["accent"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<path class="flow back" d="M{l1} {mid + 7}H{l0}" stroke="{c["text3"]}"/>'
             f'<path d="M{l0 + 5} {mid + 3}l-5 4 5 4" fill="none" stroke="{c["text3"]}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>')
    chips_txt = ["retries", "ordered", "SQLite dedup"]
    widths = [measure("mono", s, 11.5) + 22 for s in chips_txt]
    cx = dx + (dw - sum(widths) - 6 * (len(widths) - 1)) / 2
    chips = ""
    for s, cw in zip(chips_txt, widths):
        chips += (f'<rect x="{cx:.1f}" y="{dy + dh - 62}" width="{cw:.1f}" height="26" rx="13" fill="{c["tile"]}"/>'
                  f'<text x="{cx + cw / 2:.1f}" y="{dy + dh - 45}" text-anchor="middle" class="m" font-size="11.5" fill="{c["text2"]}">{s}</text>')
        cx += cw + 6
    caption = "one chat ⇄ one chat"
    diagram = (f'<g class="rise" style="animation-delay:.12s">'
               f'<rect x="{dx}" y="{dy}" width="{dw}" height="{dh}" rx="{R_INNER + 2}" fill="{c["inner"]}"/>'
               f'{node(ax, "Telegram", "telegram")}{node(bx, "Bale", None)}{flows}'
               f'<text x="{dx + dw / 2}" y="{ny + nh + 34}" text-anchor="middle" class="m" font-size="11.5" fill="{c["text3"]}">{caption}</text>'
               f'{chips}</g>')
    css = (".flow{fill:none;stroke-width:1.5;stroke-linecap:round;stroke-dasharray:2 6;animation:flow 1.4s linear infinite;}"
           ".back{animation-direction:reverse;}@keyframes flow{to{stroke-dashoffset:-16;}}")
    used = {"display": name, "sans": "Featured" + lang + desc + label + "TelegramBale",
            "mono": meta + "".join(chips_txt) + caption}
    body = f"<defs>{style(used, css)}</defs>\n{tile(c, 0, 0, W, H, 0, left)}\n{diagram}"
    return svg(W, H, f"{name}: {desc} {label} stars", body)


ICONS = {
    "star": STAR,
    "commit": "M1 7h3.2M9.8 7H13M7 4.6a2.4 2.4 0 1 0 0 4.8a2.4 2.4 0 1 0 0-4.8z",
    "users": "M5 6.4a2.3 2.3 0 1 0 0-4.6a2.3 2.3 0 1 0 0 4.6zM1 12.2c0-2.2 1.8-3.6 4-3.6s4 1.4 4 3.6M9.6 1.9a2.3 2.3 0 0 1 0 4.4M10.8 8.8c1.3.4 2.2 1.6 2.2 3.4",
    "box": "M7 1.2l5.3 3v5.6L7 12.8 1.7 9.8V4.2zM1.7 4.2L7 7.2l5.3-3M7 7.2v5.6",
}


def stats(t: str, d: dict) -> str:
    c = THEMES[t]
    col = (W - 3 * GAP) / 4
    mh = 128
    H = 2 * mh + GAP
    metrics = [("star", "Stars earned", fmt(d["total_stars"])),
               ("commit", "Contributions this year", fmt(d["contrib"])),
               ("users", "Followers", fmt(d["followers"])),
               ("box", "Public projects", str(d["repos"]))]
    parts = []
    for i, (ic, label, val) in enumerate(metrics):
        x, y = (i % 2) * (col + GAP), (i // 2) * (mh + GAP)
        parts.append(tile(c, x, y, col, mh, i * 0.06,
                          f'<path transform="translate({x + PAD:.1f} {y + PAD + 1})" d="{ICONS[ic]}" fill="none" stroke="{c["text2"]}" '
                          f'stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>'
                          f'<text x="{x + PAD + 22:.1f}" y="{y + PAD + 12}" class="s" font-size="13" fill="{c["text2"]}">{esc(label)}</text>'
                          f'<text x="{x + PAD - 1:.1f}" y="{y + mh - PAD - 2}" class="d" font-size="40" letter-spacing="-1.4" fill="{c["fg"]}">{esc(val)}</text>'))

    # languages: a tall tile spanning the right half
    lx, lw = 2 * (col + GAP), 2 * col + GAP
    total = sum(d["langs"].values()) or 1
    top = sorted(d["langs"].items(), key=lambda kv: -kv[1])[:5]
    other = total - sum(v for _, v in top)
    if other > 0:
        top.append(("Other", other))
    palette = [c["accent"], c["warm"], c["fg"], c["text3"], c["text2"], c["line"]]
    now = dt.date.today()
    today = f"{now.day} {now:%B %Y}"
    tg, _ = tag(c, lx + PAD, PAD, "Languages")
    lead, lead_v = top[0] if top else ("—", 0)
    lead_pct = f"{lead_v / total * 100:.1f}%"
    head = (f'<text x="{lx + lw - PAD}" y="{PAD + 16.5}" text-anchor="end" class="s" font-size="12" fill="{c["text3"]}">Updated {today}</text>'
            f'<text x="{lx + PAD - 1}" y="104" class="d" font-size="40" letter-spacing="-1.4" fill="{c["fg"]}">{esc(lead)}'
            f'<tspan class="s" font-size="15" letter-spacing="0" fill="{c["text3"]}" dx="10">{lead_pct} of my public code</tspan></text>')
    bx, bw, by = lx + PAD, lw - 2 * PAD, 128
    segs, x = [], bx
    for i, (k, v) in enumerate(top):
        w = bw * v / total
        segs.append(f'<rect x="{x:.1f}" y="{by}" width="{max(w - 3, 2):.1f}" height="10" rx="3" fill="{palette[i]}"/>')
        x += w
    bar = (f'<clipPath id="bar"><rect x="{bx}" y="{by}" width="{bw}" height="10" rx="5"/></clipPath>'
           f'<g clip-path="url(#bar)"><g class="grow" style="animation-delay:.4s">{"".join(segs)}</g></g>')
    legend, legend_txt = "", ""
    cw = bw if len(top) <= 3 else (bw - 24) / 2  # one column unless it would need more than three rows
    for i, (k, v) in enumerate(top):
        pct = f"{v / total * 100:.1f}%"
        x, y = bx + (i // 3) * (cw + 24), 180 + (i % 3) * 30
        legend += (f'<circle cx="{x + 4}" cy="{y - 4.5}" r="4" fill="{palette[i]}"/>'
                   f'<text x="{x + 16}" y="{y}" class="s" font-size="14" fill="{c["fg"]}">{esc(k)}</text>'
                   f'<text x="{x + cw}" y="{y}" text-anchor="end" class="m" font-size="12" fill="{c["text3"]}">{pct}</text>')
        legend_txt += pct
    parts.append(tile(c, lx, 0, lw, H, .25, tg + head + bar + legend))
    used = {"display": "".join(m[2] for m in metrics) + lead,
            "sans": "".join(m[1] for m in metrics) + "Languages Updated " + today + " of my public code" + lead_pct
                    + "".join(k for k, _ in top),
            "mono": legend_txt}
    body = f"<defs>{style(used)}</defs>\n" + "\n".join(parts)
    return svg(W, H, f"{fmt(d['total_stars'])} stars, {fmt(d['contrib'])} contributions this year, "
                     f"{d['followers']} followers, {d['repos']} public projects. Mostly {lead}.", body)


def main() -> None:
    d = collect()
    for i, (repo, name, lang, desc, meta) in enumerate(PROJECTS):
        build = bridge_card if i == 0 else card
        for t in THEMES:
            write(f"card-{repo}-{t}.svg", build(t, name, lang, desc, meta, d["stars"].get(repo, 0)), DIST)
    for t in THEMES:
        write(f"stats-{t}.svg", stats(t, d), DIST)
    print(json.dumps({k: d[k] for k in ("total_stars", "followers", "repos", "contrib")}))


if __name__ == "__main__":
    main()
