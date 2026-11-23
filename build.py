#!/usr/bin/env python3
"""Builds the GitHub profile README and its SVG cards (light + dark).

Edit PROFILE / PROJECTS / RESEARCH / JOURNEY / TOOLBOX below, then run from this folder:

    python3 build.py

Writes README.md and assets/*.svg. The header photo is assets/photo.jpg
(square, ~240 px); replace it to change the picture. Standard library only.

The activity card reads your contribution calendar from GitHub using the
GITHUB_TOKEN environment variable (as in the GitHub Action) or, locally, the
`gh` CLI. The last result is cached in assets/contributions.json; set
NO_FETCH=1 to build from that cache without network access.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import math
import os
import random
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
GITHUB_LOGIN = "jhasanjiv5"
CHALLENGE = ("2026-10-26", "2026-11-24", "30 Ideas · 30 Days")  # highlighted on the activity card

# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
PROFILE = dict(
    name="Sanjiv S. Jha",
    headline="Applied AI researcher who ships",
    subline="PhD, AI & Ubiquitous Computing · University of St.Gallen",
    themes=["Explainable AI", "Privacy-aware AI", "Ambient intelligence"],
    #open_to="Open to applied-AI & ML engineering roles",
    where="Switzerland · Germany · Remote",
    stats=[("7", "peer-reviewed papers"), ("6 yrs", "applied AI research"),
           ("29", "apps built in 30 days"), ("10+", "students mentored")],
    linkedin="https://www.linkedin.com/in/snjivza/",
    scholar="https://scholar.google.com/citations?user=tHPrrWoAAAAJ",
    website="https://jhasanjiv5.github.io",
)

LAB = "https://github.com/jhasanjiv5/30_day_30_ideas"
PROJECTS = [
    dict(slug="lab", kind="Built", title="30 Ideas · 30 Days", accent="#0a66c2",
         line1="29 AI prototypes in a month, each scored", line2="for maturity, research and business value",
         stack=["Swift", "TypeScript", "Go", "Python"], url=LAB),
    dict(slug="aces", kind="Research", title="ACES", accent="#7c3aed",
         line1="Actionable, contextual explanations", line2="for smart environments",
         stack=["Knowledge graphs", "SPARQL", "XAI"], url="https://github.com/jhasanjiv5/ContexualExplainerSystem"),
    dict(slug="kavach", kind="Built", title="Kavach", accent="#c2410c",
         line1="Local security guard for AI coding agents:", line2="blocks leaked secrets and prompt injection",
         stack=["Go", "Local LLM", "Agent hooks"], url=f"{LAB}/tree/main/kavach"),
    dict(slug="drishya", kind="Built", title="Drishya", accent="#b45309",
         line1="Turns research papers into narrated,", line2="cited video podcasts with grounded Q&A",
         stack=["FastAPI", "React", "Manim", "RAG"], url=f"{LAB}/tree/main/drishya"),
    dict(slug="saathi", kind="Built", title="Saathi", accent="#0f766e",
         line1="An audio companion that narrates where you", line2="walk, without ever storing your location",
         stack=["Swift 6", "On-device LLM", "HealthKit"], url=f"{LAB}/tree/main/Saathi"),
    dict(slug="compliance", kind="Built", title="ComplianceCopilot", accent="#1d4ed8",
         line1="Ask questions of compliance documents", line2="with local LLMs and vector search",
         stack=["FastAPI", "React", "Local RAG"], url="https://github.com/jhasanjiv5/ComplianceCopilot"),
]

RESEARCH = [
    ("2024", "Proactive multimodal question answering",
     "Combines video, audio, activity and sensor data; 12% more accurate zero-shot QA with LLMs than recent benchmarks."),
    ("2023", "Scene understanding over time",
     "Tracks objects and their relationships as a scene changes, using scene graphs."),
    ("2022", "Actionable explanations (ACES)",
     "Counterfactual explanations for smart environments from sensors and semantic knowledge graphs."),
]

# The career road: three rows that wind left → right → left → right.
# Each stop: (year, role, place, technologies picked up in that stretch).
# Tech categories colour the dot on each chip: lang, web, data, iot, ai, apple.
JOURNEY = [
    [  # row 1
        ("2012", "B.E. Computer Engineering", "University of Mumbai", [("C", "lang"), ("C++", "lang")]),
        ("2013", "Co-founder & tech lead", "HelloWelt · 3D-print marketplace", [("PHP", "web"), ("WordPress", "web"), ("MySQL", "data")]),
        ("2014", "Software trainer", "Aptech", [("C#", "lang"), ("Python", "lang")]),
    ],
    [  # row 2
        ("2015", "M.Sc. Computer Science", "University of Zurich", [("Raspberry Pi", "iot"), ("OpenCV", "ai")]),
        ("2016", "SAP UI5 developer", "Accenture", [("SAP Fiori", "web"), ("Node-RED", "iot")]),
        ("2018", "Blockchain developer", "Equidato", [("Node.js", "web"), ("Ethereum", "data")]),
    ],
    [  # row 3
        ("2019", "Research & teaching assistant", "University of St.Gallen", [("SPARQL", "data"), ("Scene graphs", "ai"), ("LLMs + RAG", "ai")]),
        ("2025", "PhD, Computer Science", "University of St.Gallen", [("MCP", "ai"), ("Vertex AI", "ai")]),
        ("2026", "30 Ideas · 30 Days", "29 AI prototypes", [("Swift", "apple"), ("Go", "lang"), ("TypeScript", "web")]),
    ],
]
TECH_COLORS = dict(lang="#0a66c2", web="#c2410c", data="#0f766e", iot="#b45309", ai="#7c3aed", apple="#db2777")
TECH_LABELS = dict(lang="Languages", web="Web", data="Data & ledgers", iot="IoT", ai="AI / ML", apple="Apple")

TOOLBOX = [
    ("AI / ML", ["PyTorch", "scikit-learn", "OpenCV", "LLMs", "RAG", "LangGraph", "MCP"]),
    ("Languages", ["Python", "Swift", "TypeScript", "Go", "C#", "C++"]),
    ("Systems", ["Docker", "GCP", "Vertex AI", "FastAPI", "React", "SPARQL"]),
]

# ---------------------------------------------------------------------------
# Design tokens (GitHub-like neutrals, LinkedIn-like blue)
# ---------------------------------------------------------------------------
THEMES = {
    "light": dict(page="#ffffff", card="#ffffff", border="#d0d7de", text="#1f2328", muted="#59636e",
                  chip="#f6f8fa", accent="#0a66c2", green="#057642", ring="#ffffff"),
    "dark": dict(page="#0d1117", card="#161b22", border="#30363d", text="#e6edf3", muted="#9198a1",
                 chip="#21262d", accent="#4493f8", green="#3fb950", ring="#161b22"),
}
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif"


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_width(s: str, size: float) -> float:
    """Rough width of sans-serif text, good enough for laying out chips."""
    return sum(0.33 if c in "il.,:;|' " else 0.62 if c.isupper() else 0.53 for c in s) * size


def svg_open(w: int, h: int, title: str, t: dict) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{esc(title)}">
<title>{esc(title)}</title>
<style>
  text {{ font-family: {FONT}; fill: {t['text']}; }}
  .muted {{ fill: {t['muted']}; }}
  .pulse {{ animation: pulse 2.6s ease-in-out infinite; transform-box: fill-box; transform-origin: center; }}
  @keyframes pulse {{ 50% {{ opacity: .35; transform: scale(1.6); }} }}
  .twinkle {{ animation: twinkle 4s ease-in-out infinite; }}
  @keyframes twinkle {{ 50% {{ opacity: .15; }} }}
</style>
"""


def chip(x, y, label, t, size=13, fill=None, color=None, h=26) -> tuple[str, float]:
    w = text_width(label, size) + 22
    out = (f'<rect x="{x:.1f}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{fill or t["chip"]}" '
           f'stroke="{t["border"]}" stroke-width="1"/>'
           f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + size * 0.36:.1f}" font-size="{size}" text-anchor="middle"'
           f'{f" style=" + chr(34) + "fill:" + color + chr(34) if color else ""}>{esc(label)}</text>')
    return out, w


# ---------------------------------------------------------------------------
# Header: LinkedIn-style profile card
# ---------------------------------------------------------------------------
def header(t: dict, theme: str) -> str:
    w, h = 1000, 440
    rng = random.Random(7)
    s = [svg_open(w, h, f"{PROFILE['name']}: {PROFILE['headline']}. {PROFILE['subline']}.", t)]
    s.append(f"""<defs>
  <linearGradient id="cover" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0a3d7a"/><stop offset=".55" stop-color="#0a66c2"/><stop offset="1" stop-color="#0f766e"/>
  </linearGradient>
  <clipPath id="card"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16"/></clipPath>
  <clipPath id="photo"><circle cx="128" cy="160" r="84"/></clipPath>
</defs>""")
    s.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="16" fill="{t["card"]}" stroke="{t["border"]}"/>')
    # cover banner with a faint neural-network pattern
    s.append('<g clip-path="url(#card)">')
    s.append(f'<rect x="0" y="0" width="{w}" height="150" fill="url(#cover)"/>')
    nodes = [(rng.uniform(260, 990), rng.uniform(12, 140)) for _ in range(26)]
    for i, (x1, y1) in enumerate(nodes):
        for x2, y2 in nodes[i + 1:]:
            if (x1 - x2) ** 2 + (y1 - y2) ** 2 < 120 ** 2:
                s.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#ffffff" stroke-opacity=".16"/>')
    for i, (x, y) in enumerate(nodes):
        s.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rng.uniform(2, 3.6):.1f}" fill="#ffffff" fill-opacity=".55" '
                 f'class="twinkle" style="animation-delay:{(i % 7) * .55:.2f}s"/>')
    s.append('</g>')
    # photo with a LinkedIn-style "open to work" frame
    photo = ASSETS / "photo.jpg"
    cx, cy = 128, 160

    def pt(r, deg):
        a = math.radians(deg)
        return cx + r * math.cos(a), cy + r * math.sin(a)

    s.append(f'<circle cx="{cx}" cy="{cy}" r="93" fill="{t["ring"]}"/>')
    if photo.exists():
        data = base64.b64encode(photo.read_bytes()).decode()
        s.append(f'<image x="{cx - 84}" y="{cy - 84}" width="168" height="168" clip-path="url(#photo)" '
                 f'preserveAspectRatio="xMidYMid slice" href="data:image/jpeg;base64,{data}"/>')
    else:
        s.append(f'<circle cx="{cx}" cy="{cy}" r="84" fill="{t["chip"]}"/>')
    s.append(f'<circle cx="{cx}" cy="{cy}" r="85" fill="none" stroke="{t["green"]}" stroke-width="5"/>')
    (bx1, by1), (bx2, by2) = pt(84, 152), pt(84, 28)
    s.append(f'<path d="M {bx1:.1f} {by1:.1f} A 84 84 0 0 0 {bx2:.1f} {by2:.1f}" fill="none" '
             f'stroke="{t["green"]}" stroke-width="17"/>')
    (tx1, ty1), (tx2, ty2) = pt(88.5, 152), pt(88.5, 28)
    s.append(f'<path id="arc-{theme}" d="M {tx1:.1f} {ty1:.1f} A 88.5 88.5 0 0 0 {tx2:.1f} {ty2:.1f}" fill="none"/>')
    s.append(f'<text font-size="11.5" font-weight="700" letter-spacing="1.4" style="fill:#ffffff">'
             f'<textPath href="#arc-{theme}" xlink:href="#arc-{theme}" startOffset="50%" text-anchor="middle">#OPENTOWORK</textPath></text>')
    # name block
    s.append(f'<text x="236" y="196" font-size="34" font-weight="700">{esc(PROFILE["name"])}</text>')
    s.append(f'<text x="236" y="228" font-size="19">{esc(PROFILE["headline"])}</text>')
    s.append(f'<text x="236" y="254" font-size="15" class="muted">{esc(PROFILE["subline"])}</text>')
    s.append(f'<circle cx="242" cy="277" r="4.5" fill="{t["green"]}" class="pulse"/>')
    # s.append(f'<text x="254" y="282" font-size="14" font-weight="600" style="fill:{t["green"]}">{esc(PROFILE["open_to"])}</text>')
    # s.append(f'<text x="{254 + text_width(PROFILE["open_to"], 14) + 14:.0f}" y="282" font-size="14" class="muted">· {esc(PROFILE["where"])}</text>')
    # theme chips on the right
    for i, th in enumerate(PROFILE["themes"]):
        cw = text_width(th, 13) + 22
        c, _ = chip(w - 32 - cw, 172 + i * 36, th, t, fill=t["card"], color=t["accent"])
        s.append(c)
    # stats row
    s.append(f'<line x1="32" y1="316" x2="{w - 32}" y2="316" stroke="{t["border"]}"/>')
    col = (w - 64) / 4
    for i, (big, small) in enumerate(PROFILE["stats"]):
        x = 32 + i * col
        if i:
            s.append(f'<line x1="{x:.0f}" y1="338" x2="{x:.0f}" y2="414" stroke="{t["border"]}"/>')
        s.append(f'<text x="{x + col / 2:.0f}" y="378" font-size="32" font-weight="700" text-anchor="middle" style="fill:{t["accent"]}">{esc(big)}</text>')
        s.append(f'<text x="{x + col / 2:.0f}" y="402" font-size="14" text-anchor="middle" class="muted">{esc(small)}</text>')
    s.append("</svg>\n")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Project card
# ---------------------------------------------------------------------------
def tile(p: dict, t: dict, theme: str) -> str:
    w, h = 480, 214
    s = [svg_open(w, h, f"{p['title']}: {p['line1']} {p['line2']}", t)]
    cid = f"clip-{p['slug']}-{theme}"
    s.append(f'<defs><clipPath id="{cid}"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12"/></clipPath></defs>')
    s.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{t["card"]}" stroke="{t["border"]}"/>')
    s.append(f'<rect x="0" y="0" width="{w}" height="5" fill="{p["accent"]}" clip-path="url(#{cid})"/>')
    kind_w = text_width(p["kind"].upper(), 11) + 20
    s.append(f'<rect x="24" y="26" width="{kind_w:.0f}" height="22" rx="11" fill="{p["accent"]}" fill-opacity=".12"/>')
    s.append(f'<text x="{24 + kind_w / 2:.0f}" y="41" font-size="11" font-weight="700" letter-spacing=".8" text-anchor="middle" '
             f'style="fill:{p["accent"] if theme == "light" else t["text"]}">{p["kind"].upper()}</text>')
    s.append(f'<text x="24" y="86" font-size="24" font-weight="700">{esc(p["title"])}</text>')
    s.append(f'<text x="24" y="116" font-size="15" class="muted">{esc(p["line1"])}</text>')
    s.append(f'<text x="24" y="137" font-size="15" class="muted">{esc(p["line2"])}</text>')
    x = 24
    for st in p["stack"]:
        c, cw = chip(x, 162, st, t, size=12, h=24)
        s.append(c)
        x += cw + 8
    s.append(f'<text x="{w - 24}" y="179" font-size="14" font-weight="600" text-anchor="end" style="fill:{t["accent"]}">View →</text>')
    s.append("</svg>\n")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Career road
# ---------------------------------------------------------------------------
def journey(t: dict, theme: str) -> str:
    w, h = 1000, 600
    rows_y = [140, 330, 520]
    left, right, r = 110, 890, 95
    starts = [(50, 1), (right, -1), (left, 1)]      # (x where the row starts, direction)
    ends = [right, left, 955]
    road = "#e6eaef" if theme == "light" else "#262c36"
    dash = "#ffffff" if theme == "light" else "#8b949e"
    d = (f"M 50 {rows_y[0]} H {right} A {r} {r} 0 0 1 {right} {rows_y[1]} "
         f"H {left} A {r} {r} 0 0 0 {left} {rows_y[2]} H 955")
    alt = "Career road: " + "; ".join(f"{y} {role}, {place} ({', '.join(n for n, _ in tech)})"
                                      for row in JOURNEY for y, role, place, tech in row)
    s = [svg_open(w, h, alt, t)]
    s.append(f"""<style>
  .lane {{ animation: drive 1.6s linear infinite; }}
  @keyframes drive {{ to {{ stroke-dashoffset: -22; }} }}
</style>""")
    s.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{t["card"]}" stroke="{t["border"]}"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{t["border"]}" stroke-width="44" stroke-linecap="round" stroke-linejoin="round"/>')
    s.append(f'<path id="road-{theme}" d="{d}" fill="none" stroke="{road}" stroke-width="40" stroke-linecap="round"/>')
    s.append(f'<path d="{d}" fill="none" stroke="{dash}" stroke-opacity=".9" stroke-width="2" stroke-dasharray="12 10" class="lane"/>')
    # a traveller moving along the road
    s.append(f'<circle r="6" fill="{t["accent"]}" stroke="{t["card"]}" stroke-width="2">'
             f'<animateMotion dur="26s" repeatCount="indefinite" rotate="auto"><mpath href="#road-{theme}" xlink:href="#road-{theme}"/></animateMotion></circle>')

    row_fracs = [[0.03, 0.37, 0.70], [0.03, 0.37, 0.70], [0.03, 0.43, 0.68]]  # where each stop sits along its row
    for ri, row in enumerate(JOURNEY):
        y = rows_y[ri]
        x0, direction = starts[ri]
        length = abs(ends[ri] - x0)
        marks = [x0 + direction * f * length for f in row_fracs[ri]]
        for si, (year, role, place, tech) in enumerate(row):
            mx = marks[si]
            seg_end = marks[si + 1] if si + 1 < len(marks) else ends[ri]
            # technologies scattered along the middle of the road
            x = mx + direction * 26
            for name, cat in tech:
                cw = text_width(name, 11.5) + 30
                cx0 = x if direction > 0 else x - cw
                if (direction > 0 and cx0 + cw > seg_end - 8) or (direction < 0 and cx0 < seg_end + 8):
                    print(f"warning: no room for {name!r} after {year}; adjust row_fracs"); break
                s.append(f'<rect x="{cx0:.1f}" y="{y - 11}" width="{cw:.1f}" height="22" rx="11" fill="{t["card"]}" stroke="{t["border"]}"/>')
                s.append(f'<circle cx="{cx0 + 12:.1f}" cy="{y}" r="4" fill="{TECH_COLORS[cat]}"/>')
                s.append(f'<text x="{cx0 + 21:.1f}" y="{y + 4}" font-size="11.5" font-weight="600">{esc(name)}</text>')
                x += direction * (cw + 8)
            # milestone marker + label above the road
            anchor = "start" if direction > 0 else "end"
            s.append(f'<circle cx="{mx:.1f}" cy="{y}" r="10" fill="{t["card"]}" stroke="{t["accent"]}" stroke-width="3.5"/>')
            s.append(f'<line x1="{mx:.1f}" y1="{y - 24}" x2="{mx:.1f}" y2="{y - 76}" stroke="{t["accent"]}" stroke-width="2" stroke-opacity=".5"/>')
            lx = mx + (8 if direction > 0 else -8)
            s.append(f'<text x="{lx:.1f}" y="{y - 64}" font-size="15" font-weight="800" text-anchor="{anchor}" style="fill:{t["accent"]}">{esc(year)}</text>')
            s.append(f'<text x="{lx:.1f}" y="{y - 46}" font-size="13.5" font-weight="600" text-anchor="{anchor}">{esc(role)}</text>')
            s.append(f'<text x="{lx:.1f}" y="{y - 29}" font-size="12" text-anchor="{anchor}" class="muted">{esc(place)}</text>')
    # finish flag
    fx, fy = 955, rows_y[2]
    s.append(f'<line x1="{fx}" y1="{fy - 4}" x2="{fx}" y2="{fy - 44}" stroke="{t["text"]}" stroke-width="2"/>')
    s.append(f'<path d="M {fx} {fy - 44} L {fx + 26} {fy - 37} L {fx} {fy - 30} Z" fill="{t["green"]}"/>')
    # legend
    lx = 28
    for cat, label in TECH_LABELS.items():
        s.append(f'<circle cx="{lx + 5}" cy="{h - 22}" r="4.5" fill="{TECH_COLORS[cat]}"/>')
        s.append(f'<text x="{lx + 15}" y="{h - 18}" font-size="12" class="muted">{esc(label)}</text>')
        lx += text_width(label, 12) + 40
    s.append("</svg>\n")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Activity card (contribution calendar)
# ---------------------------------------------------------------------------
CONTRIB_QUERY = ("query($login:String!){user(login:$login){contributionsCollection{"
                 "contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}")


def load_contributions() -> dict | None:
    cache = ASSETS / "contributions.json"
    data = None
    if os.environ.get("NO_FETCH") != "1":
        try:
            token = os.environ.get("GITHUB_TOKEN")
            if token:
                req = urllib.request.Request(
                    "https://api.github.com/graphql",
                    data=json.dumps({"query": CONTRIB_QUERY, "variables": {"login": GITHUB_LOGIN}}).encode(),
                    headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    data = json.load(resp)
            else:
                out = subprocess.run(["gh", "api", "graphql", "-f", f"query={CONTRIB_QUERY}", "-f", f"login={GITHUB_LOGIN}"],
                                     capture_output=True, text=True, timeout=30, check=True)
                data = json.loads(out.stdout)
            cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
            days = [{"date": d["date"], "count": d["contributionCount"]} for w in cal["weeks"] for d in w["contributionDays"]]
            data = {"total": cal["totalContributions"], "days": days, "fetched": dt.date.today().isoformat()}
            cache.write_text(json.dumps(data, indent=1), encoding="utf-8")
        except Exception as exc:  # network, auth or API shape problems: fall back to the cache
            print(f"note: could not fetch contributions ({exc.__class__.__name__}); using cache")
            data = None
    if data is None and cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
    return data


def activity(t: dict, theme: str, data: dict) -> str:
    days = data["days"]
    counts = {d["date"]: d["count"] for d in days}
    active = sum(1 for d in days if d["count"])
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)
    c0, c1, label = CHALLENGE
    today = days[-1]["date"]
    in_ch = [d for d in days if c0 <= d["date"] <= min(c1, today)]
    ch_active = sum(1 for d in in_ch if d["count"])
    stats = [(str(data["total"]), "contributions in the last year"), (str(active), "active days"),
             (f"{longest} days", "longest streak"), (f"{ch_active} / {len(in_ch)}", "challenge days with commits")]

    levels = (["#ebedf0", "#c7ddf5", "#7fb0e8", "#3d86d6", "#0a66c2"] if theme == "light"
              else ["#21262d", "#103a6b", "#1a5aa6", "#2f7fd8", "#58a6ff"])

    def level(n):
        return 0 if n == 0 else 1 if n == 1 else 2 if n <= 3 else 3 if n <= 7 else 4

    w, h = 1000, 300
    alt = (f"GitHub activity: {data['total']} contributions in the last year, {active} active days, "
           f"longest streak {longest} days, commits on {ch_active} of {len(in_ch)} days of the {label} challenge.")
    s = [svg_open(w, h, alt, t)]
    s.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{t["card"]}" stroke="{t["border"]}"/>')
    col = (w - 64) / 4
    for i, (big, small) in enumerate(stats):
        x = 32 + i * col
        if i:
            s.append(f'<line x1="{x:.0f}" y1="26" x2="{x:.0f}" y2="84" stroke="{t["border"]}"/>')
        color = t["green"] if i == 3 else t["accent"]
        s.append(f'<text x="{x + col / 2:.0f}" y="60" font-size="28" font-weight="700" text-anchor="middle" style="fill:{color}">{esc(big)}</text>')
        s.append(f'<text x="{x + col / 2:.0f}" y="82" font-size="13" text-anchor="middle" class="muted">{esc(small)}</text>')

    # heatmap: columns are weeks (Sunday first), rows are weekdays
    first = dt.date.fromisoformat(days[0]["date"])
    start = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    last = dt.date.fromisoformat(today)
    weeks = ((last - start).days // 7) + 1
    cell, gap = 13, 3
    gx, gy = w - 32 - weeks * (cell + gap) + gap, 150
    for r, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        s.append(f'<text x="{gx - 10}" y="{gy + r * (cell + gap) + 10}" font-size="11" text-anchor="end" class="muted">{name}</text>')
    seen_month = None
    ch_cols = []
    for wk in range(weeks):
        for wd in range(7):
            day = start + dt.timedelta(days=wk * 7 + wd)
            if day < first or day > last:
                continue
            iso = day.isoformat()
            x, y = gx + wk * (cell + gap), gy + wd * (cell + gap)
            if wd == 0 or day == first:
                if day.month != seen_month and day.day <= 7 + (0 if wk else 7):
                    s.append(f'<text x="{x}" y="{gy - 10}" font-size="11" class="muted">{day.strftime("%b")}</text>')
                    seen_month = day.month
            n = counts.get(iso, 0)
            if c0 <= iso <= c1:
                ch_cols.append(wk)
            s.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="3" fill="{levels[level(n)]}">'
                     f'<title>{iso}: {n} contribution{"s" if n != 1 else ""}</title></rect>')
    if ch_cols:
        bx1 = gx + min(ch_cols) * (cell + gap) - 4
        bx2 = gx + max(ch_cols) * (cell + gap) + cell + 4
        s.append(f'<rect x="{bx1}" y="{gy - 4}" width="{bx2 - bx1}" height="{7 * (cell + gap) + 5}" rx="6" fill="none" '
                 f'stroke="{t["green"]}" stroke-width="2" stroke-dasharray="5 4" class="lane"/>')
        s.append(f'<text x="{bx2}" y="{gy - 26}" font-size="12" font-weight="700" text-anchor="end" style="fill:{t["green"]}">{esc(label)} ↓</text>')
    s.append(f"""<style>.lane {{ animation: march 1.4s linear infinite; }} @keyframes march {{ to {{ stroke-dashoffset: -18; }} }}</style>""")
    # legend + freshness
    ly = gy + 7 * (cell + gap) + 22
    s.append(f'<text x="{gx}" y="{ly}" font-size="11" class="muted">Updated {esc(data.get("fetched", today))}</text>')
    lx = w - 32 - 5 * (cell + gap) - 34
    s.append(f'<text x="{lx - 8}" y="{ly}" font-size="11" text-anchor="end" class="muted">Less</text>')
    for i, c in enumerate(levels):
        s.append(f'<rect x="{lx + i * (cell + gap)}" y="{ly - 11}" width="{cell}" height="{cell}" rx="3" fill="{c}"/>')
    s.append(f'<text x="{lx + 5 * (cell + gap) + 4}" y="{ly}" font-size="11" class="muted">More</text>')
    s.append("</svg>\n")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# Toolbox
# ---------------------------------------------------------------------------
def toolbox(t: dict) -> str:
    w, h = 1000, 176
    alt = "Toolbox: " + "; ".join(g + ": " + ", ".join(items) for g, items in TOOLBOX)
    s = [svg_open(w, h, alt, t)]
    s.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="{t["card"]}" stroke="{t["border"]}"/>')
    for r, (group, items) in enumerate(TOOLBOX):
        y = 28 + r * 46
        s.append(f'<text x="28" y="{y + 19}" font-size="14" font-weight="700" class="muted">{esc(group.upper())}</text>')
        x = 150
        for it in items:
            c, cw = chip(x, y, it, t, size=14, h=28)
            s.append(c)
            x += cw + 10
    s.append("</svg>\n")
    return "\n".join(s)


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------
def pic(name: str, alt: str, width: str = "100%") -> str:
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img src="assets/{name}.svg" alt="{esc(alt)}" width="{width}"></picture>')


def readme(has_activity: bool = False) -> str:
    def cell(p):
        return f'<a href="{p["url"]}">{pic(p["slug"], p["title"] + ": " + p["line1"] + " " + p["line2"])}</a>'

    grid = "\n".join(
        f'<tr>\n<td width="50%">{cell(PROJECTS[i])}</td>\n<td width="50%">{cell(PROJECTS[i + 1])}</td>\n</tr>'
        for i in range(0, len(PROJECTS), 2)
    )
    research = "\n".join(f"| {y} | **{t}** | {d} |" for y, t, d in RESEARCH)
    activity_section = ("\n### Activity\n\n<p align=\"center\">" + pic("activity", "GitHub activity over the last year, with the "
                        + CHALLENGE[2] + " challenge highlighted") + "</p>\n") if has_activity else ""
    journey_alt = "Career road: " + "; ".join(f"{y} {role}, {place}" for row in JOURNEY for y, role, place, _ in row)
    toolbox_alt = "Toolbox: " + "; ".join(g + ": " + ", ".join(items) for g, items in TOOLBOX)
    header_alt = f"{PROFILE['name']}: {PROFILE['headline']}. {PROFILE['subline']}. {PROFILE['open_to']}."

    return f"""<!-- Generated by build.py — edit the content there, then run: python3 build.py -->
<p align="center">{pic("header", header_alt)}</p>

<p align="center">
I turn AI research into working systems: explainable, privacy-aware assistants that understand the places and people around them.<br>
<sub>PhD on transparent, privacy-preserving intelligent systems · 7 peer-reviewed papers · building one prototype a day.</sub>
</p>

<p align="center">
<a href="{PROFILE['linkedin']}"><b>LinkedIn</b></a> &nbsp;·&nbsp;
<a href="{PROFILE['scholar']}"><b>Google Scholar</b></a> &nbsp;·&nbsp;
<a href="{PROFILE['website']}"><b>Website &amp; CV</b></a> &nbsp;·&nbsp;
<a href="{LAB}"><b>30-day lab</b></a>
</p>

---

### What are you here for?

<details>
<summary><b>💼 I'm hiring:</b> what can you do for my team?</summary>

- **Take AI from paper to product.** Six years of applied AI research, and a month of turning ideas into working apps (Swift, TypeScript, Go, Python).
- **Build trustworthy AI.** Explanations users can act on, on-device and local models, and guardrails such as [Kavach]({LAB}/tree/main/kavach).
- **Work end to end.** Sensors and IoT pipelines, LLM/RAG back ends, web and native front ends, Docker and GCP.
- **Lead and teach.** Mentored 10+ students; co-founded a start-up; programme committees at IEEE ICTAI 2025, Mensch und Computer 2024 and IoT 2021.

{PROFILE['open_to']} · {PROFILE['where']} · full CV on my [website]({PROFILE['website']}).
</details>

<details>
<summary><b>🔬 I'm a researcher:</b> what do you work on?</summary>

| Year | Work | In one line |
| :---: | :--- | :--- |
{research}

Themes: explainable AI, ubiquitous and ambient computing, multimodal LLMs, privacy by design. Full list on [Google Scholar]({PROFILE['scholar']}).
</details>

<details>
<summary><b>👀 Just show me something cool</b></summary>

- 🎧 [Saathi]({LAB}/tree/main/Saathi): an audio companion that tells you about the place you're walking through.
- 🎬 [Drishya]({LAB}/tree/main/drishya): research papers turned into narrated, cited video podcasts.
- 🛡️ [Kavach]({LAB}/tree/main/kavach): a local security guard for AI coding agents.
- 🧪 [The whole lab notebook]({LAB}): 29 apps, scored and charted.
</details>

---

### Featured work

<table>
{grid}
</table>

### The road so far

<p align="center">{pic("journey", journey_alt)}</p>
<p align="center"><sub>From Mumbai to St.Gallen, from embedded C to explainable AI: the tools on the road are what each stretch was built with.</sub></p>
{activity_section}
### Toolbox

<p align="center">{pic("toolbox", toolbox_alt)}</p>

<p align="center"><sub>English · German · Hindi</sub></p>
"""


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    count = 0
    for theme, t in THEMES.items():
        suffix = "" if theme == "light" else "-dark"
        (ASSETS / f"header{suffix}.svg").write_text(header(t, theme), encoding="utf-8")
        (ASSETS / f"toolbox{suffix}.svg").write_text(toolbox(t), encoding="utf-8")
        (ASSETS / f"journey{suffix}.svg").write_text(journey(t, theme), encoding="utf-8")
        for p in PROJECTS:
            (ASSETS / f"{p['slug']}{suffix}.svg").write_text(tile(p, t, theme), encoding="utf-8")
        count += len(PROJECTS) + 3
    contrib = load_contributions()
    if contrib:
        for theme, t in THEMES.items():
            suffix = "" if theme == "light" else "-dark"
            (ASSETS / f"activity{suffix}.svg").write_text(activity(t, theme, contrib), encoding="utf-8")
            count += 1
    (ROOT / "README.md").write_text(readme(has_activity=bool(contrib)), encoding="utf-8")
    print(f"wrote README.md and {count} SVGs (light + dark) in assets/")


if __name__ == "__main__":
    main()
