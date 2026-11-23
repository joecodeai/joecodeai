"""Render the static SVG assets used by the profile README.

All artwork is plain SVG with CSS/SMIL animation, so it renders inside GitHub's <img> sandbox
(no scripts, no external fonts). Run from the repository root:

    python scripts/build_assets.py
"""

from __future__ import annotations

from html import escape
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "assets"

SANS = "'Segoe UI',-apple-system,BlinkMacSystemFont,'Helvetica Neue',Ubuntu,Arial,sans-serif"
MONO = "'JetBrains Mono','SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace"

BG0, BG1 = "#05060d", "#0c0a1f"
CYAN, BLUE, VIOLET, MAGENTA = "#22d3ee", "#3b82f6", "#a855f7", "#ec4899"
TEXT, MUTED, DIM = "#e2e8f0", "#94a3b8", "#475569"
MONO_W = 0.6  # advance width of a monospace glyph, in em


REDUCED_MOTION = (
    "@media (prefers-reduced-motion: reduce){.l,.chip,.pop,.rise{animation:none!important;opacity:1!important}}"
)


def svg(w: int, h: int, title: str, desc: str, body: str, style: str = "") -> str:
    style += REDUCED_MOTION
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-labelledby="title desc">\n'
        f'<title id="title">{escape(title)}</title>\n<desc id="desc">{escape(desc)}</desc>\n'
        f"<style>{style}</style>\n{body}\n</svg>\n"
    )


def neon_gradient(gid: str, width: int, dur: int = 8) -> str:
    """Horizontal cyan-blue-violet-magenta gradient that slowly flows sideways."""
    return (
        f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{width}" y2="0" '
        f'spreadMethod="reflect">'
        f'<stop offset="0" stop-color="{CYAN}"/><stop offset=".35" stop-color="{BLUE}"/>'
        f'<stop offset=".7" stop-color="{VIOLET}"/><stop offset="1" stop-color="{MAGENTA}"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="0 0;{width} 0;0 0" '
        f'dur="{dur}s" repeatCount="indefinite"/></linearGradient>'
    )


def card_bg(w: int, h: int, r: int = 20) -> str:
    return (
        f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="{r}" fill="url(#bg)" '
        f'stroke="url(#edge)" stroke-opacity=".55"/>'
    )


def card_defs(w: int, h: int) -> str:
    return (
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BG0}"/>'
        f'<stop offset="1" stop-color="{BG1}"/></linearGradient>'
        f'<linearGradient id="edge" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{CYAN}"/>'
        f'<stop offset=".5" stop-color="{VIOLET}" stop-opacity=".4"/><stop offset="1" stop-color="{MAGENTA}"/>'
        f"</linearGradient>"
        f'<filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="3" '
        f'result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>'
        f'<filter id="soft" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="40"/>'
        f"</filter>"
    )


def mono_width(text: str, size: float) -> float:
    return len(text) * size * MONO_W


# ---------------------------------------------------------------------------------------------
# Hero banner
# ---------------------------------------------------------------------------------------------

PHRASES = [
    "AI Engineer",
    "real-time computer vision on NVIDIA GPUs",
    "LLM agents, RAG and fine-tuning",
    "from model to production",
]


def typing_lines(x: float, y: float, size: int, slot: float = 4.0) -> str:
    """Type each phrase, hold it, erase it, then move on. SMIL keeps it working inside <img>."""
    n = len(PHRASES)
    total = n * slot
    out = []
    for i, phrase in enumerate(PHRASES):
        w = mono_width(phrase, size)
        a, b, c, d = (i + 0.0) / n, (i + 0.38) / n, (i + 0.8) / n, (i + 0.95) / n
        times = [0.0, a, b, c, d, 1.0]
        widths = [0, 0, w, w, 0, 0]
        if i == 0:
            times, widths = times[1:], widths[1:]
        kt = ";".join(f"{t:.4f}" for t in times)
        vw = ";".join(f"{v:.1f}" for v in widths)
        vx = ";".join(f"{x + v:.1f}" for v in widths)
        vis = ";".join("1" if a <= t < d or (t == a) else "0" for t in times)
        out.append(
            f'<clipPath id="type{i}"><rect x="{x}" y="{y - size}" height="{size * 1.4}" width="0">'
            f'<animate attributeName="width" values="{vw}" keyTimes="{kt}" dur="{total}s" '
            f'repeatCount="indefinite"/></rect></clipPath>'
            f'<text x="{x}" y="{y}" textLength="{w:.1f}" lengthAdjust="spacingAndGlyphs" '
            f'clip-path="url(#type{i})" class="type">{escape(phrase)}</text>'
            f'<rect y="{y - size + 3}" width="{size * 0.55:.1f}" height="{size + 2}" fill="{CYAN}" opacity="0">'
            f'<animate attributeName="x" values="{vx}" keyTimes="{kt}" dur="{total}s" repeatCount="indefinite"/>'
            f'<animate attributeName="opacity" values="{vis}" keyTimes="{kt}" dur="{total}s" calcMode="discrete" '
            f'repeatCount="indefinite"/></rect>'
        )
    return "".join(out)


def perspective_floor(w: int, h: int, horizon: int) -> str:
    vx = w / 2
    lines = []
    for k in range(-14, 15):
        x_bottom = vx + k * 95
        lines.append(f'<line x1="{vx}" y1="{horizon}" x2="{x_bottom}" y2="{h}"/>')
    # Horizontal rungs: y = horizon + c / z. Each rung slides to the next nearer position.
    c, zs = 900.0, [12, 9, 7, 5.5, 4.3, 3.4, 2.7, 2.15, 1.7]
    ys = [horizon + c / z for z in zs]
    ys = [y for y in ys if y < h + 60] + [h + 60]
    for i in range(len(ys) - 1):
        y0, y1 = ys[i], ys[i + 1]
        lines.append(
            f'<line x1="0" x2="{w}" y1="{y0:.1f}" y2="{y0:.1f}">'
            f'<animate attributeName="y1" values="{y0:.1f};{y1:.1f}" dur="2.4s" repeatCount="indefinite"/>'
            f'<animate attributeName="y2" values="{y0:.1f};{y1:.1f}" dur="2.4s" repeatCount="indefinite"/></line>'
        )
    return "".join(lines)


def orbit_core(cx: int, cy: int) -> str:
    rings = [
        (128, 40, CYAN, "6 10", 18, 0),
        (104, 76, VIOLET, "2 8", 26, 1),
        (80, 22, MAGENTA, "14 8", 12, 0),
    ]
    out = [f'<g transform="translate({cx} {cy})">']
    out.append(f'<circle r="150" fill="{VIOLET}" opacity=".18" filter="url(#soft)"/>')
    for rx, ry, color, dash, dur, rev in rings:
        tilt = {CYAN: -18, VIOLET: 24, MAGENTA: 60}[color]
        out.append(
            f'<g transform="rotate({tilt})"><ellipse rx="{rx}" ry="{ry}" fill="none" stroke="{color}" '
            f'stroke-width="1.6" stroke-dasharray="{dash}" opacity=".85">'
            f'<animate attributeName="stroke-dashoffset" from="0" to="{-160 if rev else 160}" dur="{dur}s" '
            f'repeatCount="indefinite"/></ellipse>'
            f'<circle r="4.5" fill="{color}" filter="url(#glow)"><animateMotion dur="{dur / 2}s" '
            f'repeatCount="indefinite" path="M{rx},0 A{rx},{ry} 0 1,1 {-rx},0 A{rx},{ry} 0 1,1 {rx},0" '
            f'keyPoints="{"1;0" if rev else "0;1"}" keyTimes="0;1" calcMode="linear"/></circle></g>'
        )
    # Core: a detection box around a glowing nucleus, the "vision meets language" mark.
    out.append(
        f'<circle r="20" fill="url(#core)"><animate attributeName="r" values="18;23;18" dur="3s" '
        f'repeatCount="indefinite"/></circle>'
        f'<g fill="none" stroke="{CYAN}" stroke-width="2" opacity=".9">'
        f'<path d="M-44,-30 v-12 h12 M44,-30 v-12 h-12 M-44,30 v12 h12 M44,30 v12 h-12">'
        f'<animate attributeName="opacity" values=".35;1;.35" dur="2.2s" repeatCount="indefinite"/></path></g>'
        f'<text y="128" text-anchor="middle" class="mono" font-size="11" fill="{CYAN}" opacity=".8">'
        f"vision · language · systems</text>"
    )
    out.append("</g>")
    return "".join(out)


def hero() -> str:
    w, h = 1200, 400
    style = (
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
        f".type{{font-family:{MONO};font-size:24px;fill:{TEXT}}}"
        "@keyframes blink{50%{opacity:.15}}.blink{animation:blink 1.6s ease-in-out infinite}"
        "@keyframes rise{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
        ".rise{opacity:0;animation:rise .9s ease-out forwards}"
    )
    defs = (
        "<defs>"
        + card_defs(w, h)
        + neon_gradient("name", 620, 10)
        + f'<radialGradient id="core"><stop offset="0" stop-color="#fff"/><stop offset=".35" stop-color="{CYAN}"/>'
        f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="fadeg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000"/>'
        f'<stop offset=".25" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff"/>'
        f"</linearGradient>"
        f'<mask id="fade"><rect y="290" width="{w}" height="{h - 290}" fill="url(#fadeg)"/></mask>'
        f'<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{CYAN}" '
        f'stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}" stop-opacity=".22"/>'
        f'<stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></linearGradient>'
        f'<clipPath id="card"><rect width="{w}" height="{h}" rx="24"/></clipPath>'
        "</defs>"
    )
    chips = []
    x = 80
    for label, color in [("COMPUTER VISION", CYAN), ("LLM SYSTEMS", VIOLET), ("MLOPS", MAGENTA)]:
        cw = mono_width(label, 12) + 30
        chips.append(
            f'<g class="rise" style="animation-delay:{0.6 + len(chips) * 0.15:.2f}s">'
            f'<rect x="{x}" y="236" width="{cw:.0f}" height="30" rx="15" fill="{color}" fill-opacity=".08" '
            f'stroke="{color}" stroke-opacity=".7"/>'
            f'<circle cx="{x + 14}" cy="251" r="3" fill="{color}" class="blink"/>'
            f'<text x="{x + 24}" y="255.5" class="mono" font-size="12" fill="{color}" letter-spacing=".5">'
            f"{label}</text></g>"
        )
        x += cw + 12
    hud = (
        f'<g fill="none" stroke="{CYAN}" stroke-width="1.5" opacity=".55">'
        f'<path d="M24,58 v-34 h34"/><path d="M{w - 24},58 v-34 h-34"/>'
        f'<path d="M24,{h - 58} v34 h34"/><path d="M{w - 24},{h - 58} v34 h-34"/></g>'
    )
    body = (
        defs
        + '<g clip-path="url(#card)">'
        + f'<rect width="{w}" height="{h}" fill="url(#bg)"/>'
        + f'<circle cx="180" cy="80" r="160" fill="{CYAN}" opacity=".16" filter="url(#soft)">'
        f'<animate attributeName="cx" values="180;260;180" dur="14s" repeatCount="indefinite"/></circle>'
        + f'<circle cx="720" cy="360" r="200" fill="{MAGENTA}" opacity=".12" filter="url(#soft)">'
        f'<animate attributeName="cx" values="720;600;720" dur="18s" repeatCount="indefinite"/></circle>'
        + f'<g stroke="{VIOLET}" stroke-width="1" opacity=".55" mask="url(#fade)">'
        + perspective_floor(w, h, 290)
        + "</g>"
        + f'<line x1="0" x2="{w}" y1="290" y2="290" stroke="url(#name)" stroke-width="1.2" opacity=".7"/>'
        + orbit_core(955, 150)
        + hud
        + f'<text x="80" y="64" class="mono" font-size="14" fill="{MUTED}">~/joecodeai '
        f'<tspan fill="{DIM}">$</tspan> <tspan fill="{TEXT}">./profile --render</tspan></text>'
        + f'<circle cx="{w - 196}" cy="59" r="4.5" fill="#22c55e" class="blink"/>'
        f'<text x="{w - 184}" y="64" class="mono" font-size="13" fill="{MUTED}">Kochi, India</text>'
        + '<g class="rise" style="animation-delay:.1s"><text x="78" y="150" class="sans" font-size="78" '
        'font-weight="800" letter-spacing="-1.5" fill="url(#name)" filter="url(#glow)">Joel Thomas</text></g>'
        + f'<text x="80" y="206" class="mono" font-size="24" fill="{CYAN}">&gt;</text>'
        + typing_lines(110, 206, 24)
        + "".join(chips)
        + f'<rect width="{w}" height="70" fill="url(#scan)"><animate attributeName="y" values="-70;{h}" '
        f'dur="7s" repeatCount="indefinite"/></rect>'
        + "</g>"
        + f'<rect x=".75" y=".75" width="{w - 1.5}" height="{h - 1.5}" rx="24" fill="none" stroke="url(#edge)" '
        f'stroke-opacity=".6" stroke-width="1.5"/>'
    )
    return svg(
        w,
        h,
        "Joel Thomas",
        "AI Engineer working on real-time computer vision, LLM agents, RAG and fine-tuning, "
        "and taking models to production. Based in Kochi, India.",
        body,
        style,
    )


# ---------------------------------------------------------------------------------------------
# Section headers and footer
# ---------------------------------------------------------------------------------------------


def header(num: str, title: str, caption: str, light: bool = False) -> str:
    ink = "#0f172a" if light else TEXT
    w, h = 1000, 64
    tx = 92
    title_w = len(title) * 14.2 + 8
    line_x = tx + title_w + 18
    style = f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
    body = (
        "<defs>"
        + neon_gradient("line", w, 6)
        + '<filter id="glow" x="-50%" y="-200%" width="200%" height="500%"><feGaussianBlur stdDeviation="2.5"/>'
        "</filter></defs>"
        + f'<text x="8" y="40" class="mono" font-size="15" fill="{VIOLET}">// {num}</text>'
        + f'<text x="{tx}" y="41" class="sans" font-size="22" font-weight="700" letter-spacing="3.5" '
        f'fill="{ink}">{escape(title.upper())}</text>'
        + f'<line x1="{line_x:.0f}" x2="{w - 8}" y1="34" y2="34" stroke="url(#line)" stroke-width="1.5" '
        f'opacity=".6"/>'
        + f'<circle cy="34" r="3.5" fill="{CYAN}"><animate attributeName="cx" values="{line_x:.0f};{w - 8}" '
        f'dur="3.5s" repeatCount="indefinite"/><animate attributeName="opacity" values="0;1;1;0" '
        f'keyTimes="0;.1;.85;1" dur="3.5s" repeatCount="indefinite"/></circle>'
        + f'<circle cy="34" r="7" fill="{CYAN}" filter="url(#glow)" opacity=".7">'
        f'<animate attributeName="cx" values="{line_x:.0f};{w - 8}" dur="3.5s" repeatCount="indefinite"/></circle>'
        + f'<text x="{w - 8}" y="58" text-anchor="end" class="mono" font-size="11" fill="{DIM}">'
        f"{escape(caption)}</text>"
    )
    return svg(w, h, title, caption, body, style)


def footer() -> str:
    w, h = 1000, 90
    style = f".mono{{font-family:{MONO}}}"
    bars = []
    for i in range(60):
        x = 20 + i * 16
        base = 6 + (i * 37 % 23)
        bars.append(
            f'<rect x="{x}" y="{40 - base / 2:.1f}" width="6" height="{base}" rx="3" fill="url(#line)" opacity=".7">'
            f'<animate attributeName="height" values="{base};{base * 2.2:.1f};{base}" dur="{1.6 + (i % 7) * 0.2:.1f}s" '
            f'repeatCount="indefinite"/><animate attributeName="y" values="{40 - base / 2:.1f};{40 - base * 1.1:.1f};'
            f'{40 - base / 2:.1f}" dur="{1.6 + (i % 7) * 0.2:.1f}s" repeatCount="indefinite"/></rect>'
        )
    body = (
        "<defs>"
        + neon_gradient("line", w, 6)
        + "</defs>"
        + "".join(bars)
        + f'<text x="{w / 2}" y="84" text-anchor="middle" class="mono" font-size="12" fill="{DIM}">'
        f"// end of transmission · build, measure, ship</text>"
    )
    return svg(w, h, "Footer", "Animated equaliser bars in neon colours.", body, style)


# ---------------------------------------------------------------------------------------------
# About: terminal card
# ---------------------------------------------------------------------------------------------

ABOUT = [
    ("cmd", "whoami"),
    ("out", "Joel Thomas · AI Engineer · Kochi, India"),
    ("cmd", "cat focus.txt"),
    ("hl", "real-time computer vision    detection · tracking · re-id · DeepStream · TensorRT"),
    ("hl", "LLM systems                  RAG · tool-calling agents · fine-tuning · evals · guardrails"),
    ("hl", "production                   FastAPI · PostgreSQL · Redis · Docker · Kubernetes · CI/CD"),
    ("cmd", "cat background.txt"),
    ("out", "2024 →    AI Engineer: production CV pipelines and on-prem LLM systems"),
    ("out", "2025 →    M.Tech, AI & Data Science · BITS Pilani (expected 2027)"),
    ("out", "2023-24   AI Research Intern · Kyungpook National University, South Korea"),
    ("out", "2022-24   B.Tech, Electronics Engineering · Kyungpook National University"),
    ("cmd", "echo $MOTTO"),
    ("motto", "measure it, then ship it."),
]


def about() -> str:
    w = 1000
    lh = 27
    top = 78
    h = top + lh * len(ABOUT) + 54
    style = (
        f".mono{{font-family:{MONO};font-size:14.5px}}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".l{opacity:0;animation:in .35s ease-out forwards}"
        "@keyframes blink{50%{opacity:0}}.cur{animation:blink 1s steps(1) infinite}"
    )
    rows = []
    y = top
    for i, (kind, text) in enumerate(ABOUT):
        delay = 0.25 + i * 0.28
        if kind == "cmd":
            content = (
                f'<tspan fill="{MAGENTA}">joel</tspan><tspan fill="{DIM}">@</tspan>'
                f'<tspan fill="{CYAN}">kochi</tspan><tspan fill="{DIM}">:~$ </tspan>'
                f'<tspan fill="{TEXT}">{escape(text)}</tspan>'
            )
        elif kind == "hl":
            label, rest = text[:29], text[29:]
            content = f'<tspan fill="{VIOLET}">▸ {escape(label)}</tspan><tspan fill="{MUTED}">{escape(rest)}</tspan>'
        elif kind == "motto":
            content = f'<tspan fill="url(#neon)" font-weight="700">{escape(text)}</tspan>'
        else:
            content = f'<tspan fill="{MUTED}">{escape(text)}</tspan>'
        x = 36 if kind == "cmd" else 52
        rows.append(
            f'<text x="{x}" y="{y}" class="mono l" xml:space="preserve" style="animation-delay:{delay:.2f}s">'
            f"{content}</text>"
        )
        y += lh + (8 if kind != "cmd" and i + 1 < len(ABOUT) and ABOUT[i + 1][0] == "cmd" else 0)
    h = y + 40
    cursor_delay = 0.25 + len(ABOUT) * 0.28
    rows.append(
        f'<text x="36" y="{y}" class="mono l" style="animation-delay:{cursor_delay:.2f}s">'
        f'<tspan fill="{MAGENTA}">joel</tspan><tspan fill="{DIM}">@</tspan><tspan fill="{CYAN}">kochi</tspan>'
        f'<tspan fill="{DIM}">:~$ </tspan></text>'
        f'<rect x="{36 + mono_width("joel@kochi:~$ ", 14.5):.0f}" y="{y - 14}" width="9" height="18" fill="{CYAN}" '
        f'class="cur"/>'
    )
    chrome = (
        f'<rect x="1" y="1" width="{w - 2}" height="44" rx="19" fill="#ffffff" fill-opacity=".03"/>'
        f'<line x1="1" x2="{w - 1}" y1="45" y2="45" stroke="#ffffff" stroke-opacity=".08"/>'
        f'<circle cx="30" cy="23" r="6.5" fill="{MAGENTA}"/><circle cx="52" cy="23" r="6.5" fill="{VIOLET}"/>'
        f'<circle cx="74" cy="23" r="6.5" fill="{CYAN}"/>'
        f'<text x="{w / 2}" y="28" text-anchor="middle" class="mono" fill="{DIM}" font-size="13">'
        f"joel@kochi: ~ — zsh</text>"
    )
    body = "<defs>" + card_defs(w, h) + neon_gradient("neon", 400, 6) + "</defs>" + card_bg(w, h) + chrome
    body += "".join(rows)
    return svg(
        w,
        h,
        "About Joel",
        "Terminal-style summary. Focus: real-time computer vision, LLM systems, production engineering. "
        "Background: AI Engineer since 2024; M.Tech AI and Data Science at BITS Pilani; AI Research Intern "
        "and B.Tech Electronics at Kyungpook National University, South Korea.",
        body,
        style,
    )


# ---------------------------------------------------------------------------------------------
# Tech stack panel
# ---------------------------------------------------------------------------------------------

STACK = [
    ("Computer Vision", CYAN, ["PyTorch", "YOLO", "OpenCV", "DeepStream", "TensorRT", "ONNX Runtime",
                                "OpenVINO", "GStreamer", "Milvus"]),
    ("LLMs & Agents", VIOLET, ["Llama 3", "Qwen", "Hugging Face", "LangChain", "LoRA / PEFT", "RAG",
                              "Tool calling", "MCP", "Ollama"]),
    ("Backend & Data", BLUE, ["Python", "FastAPI", "PostgreSQL", "Redis", "SQLAlchemy", "TypeScript",
                             "Next.js", "Streamlit", "C++"]),
    ("MLOps & Cloud", MAGENTA, ["Docker", "Kubernetes", "Helm", "Terraform", "GitHub Actions", "Prometheus",
                               "Grafana", "OpenTelemetry", "GCP", "Linux"]),
]  # fmt: skip


def stack() -> str:
    w = 1000
    size = 13
    chip_h, gap = 30, 10
    x0, x1 = 250, w - 32
    rows_svg = []
    y = 40
    n = 0
    for label, color, items in STACK:
        row_top = y
        x = x0
        chips = []
        for item in items:
            cw = mono_width(item, size) + 26
            if x + cw > x1:
                x = x0
                y += chip_h + gap
            chips.append(
                f'<g class="chip" style="animation-delay:{0.15 + n * 0.05:.2f}s">'
                f'<rect x="{x:.0f}" y="{y}" width="{cw:.0f}" height="{chip_h}" rx="8" fill="{color}" '
                f'fill-opacity=".07" stroke="{color}" stroke-opacity=".45"/>'
                f'<text x="{x + 13:.0f}" y="{y + 19.5}" class="mono" font-size="{size}" fill="{TEXT}">'
                f"{escape(item)}</text></g>"
            )
            x += cw + gap
            n += 1
        block_h = y + chip_h - row_top
        mid = row_top + block_h / 2
        rows_svg.append(
            f'<rect x="32" y="{row_top}" width="4" height="{block_h}" rx="2" fill="{color}"/>'
            f'<text x="50" y="{mid + 6:.0f}" class="sans" font-size="17" font-weight="700" fill="{color}">'
            f"{escape(label)}</text>" + "".join(chips)
        )
        y += chip_h + 26
    h = y + 10
    style = (
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
        "@keyframes pop{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}"
        ".chip{opacity:0;animation:pop .45s ease-out forwards}"
    )
    shimmer = (
        f'<linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
        f'<stop offset=".5" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#fff" '
        f'stop-opacity="0"/></linearGradient><clipPath id="cl"><rect width="{w}" height="{h}" rx="20"/></clipPath>'
    )
    body = (
        "<defs>"
        + card_defs(w, h)
        + shimmer
        + "</defs>"
        + card_bg(w, h)
        + "".join(rows_svg)
        + f'<g clip-path="url(#cl)"><rect y="0" width="220" height="{h}" fill="url(#sh)" '
        f'transform="skewX(-20)"><animate attributeName="x" values="-400;{w + 300}" dur="6s" '
        f'repeatCount="indefinite"/></rect></g>'
    )
    desc = "; ".join(f"{label}: {', '.join(items)}" for label, _, items in STACK)
    return svg(w, h, "Tech stack", desc, body, style)


# ---------------------------------------------------------------------------------------------
# Project cards
# ---------------------------------------------------------------------------------------------


def metric_tiles(metrics: list[tuple[str, str, str]], x: int, y: int) -> str:
    out = []
    tile_w, tile_h = 178, 92
    for i, (value, line1, line2) in enumerate(metrics):
        tx = x + i * (tile_w + 12)
        out.append(
            f'<g class="pop" style="animation-delay:{0.3 + i * 0.15:.2f}s">'
            f'<rect x="{tx}" y="{y}" width="{tile_w}" height="{tile_h}" rx="12" fill="#ffffff" fill-opacity=".035" '
            f'stroke="#ffffff" stroke-opacity=".09"/>'
            f'<text x="{tx + 16}" y="{y + 38}" class="sans" font-size="27" font-weight="800" fill="url(#neon)">'
            f"{escape(value)}</text>"
            f'<text x="{tx + 16}" y="{y + 61}" class="mono" font-size="11" fill="{MUTED}">{escape(line1)}</text>'
            f'<text x="{tx + 16}" y="{y + 77}" class="mono" font-size="11" fill="{DIM}">{escape(line2)}</text></g>'
        )
    return "".join(out)


def tag_row(tags: list[str], x: int, y: int, color: str) -> str:
    out = []
    for t in tags:
        cw = mono_width(t, 11) + 18
        out.append(
            f'<rect x="{x:.0f}" y="{y}" width="{cw:.0f}" height="22" rx="11" fill="{color}" fill-opacity=".08" '
            f'stroke="{color}" stroke-opacity=".35"/><text x="{x + 9:.0f}" y="{y + 15}" class="mono" '
            f'font-size="11" fill="{color}">{escape(t)}</text>'
        )
        x += cw + 8
    return "".join(out)


def project_card(
    *,
    index: str,
    kind: str,
    color: str,
    name: str,
    tagline: list[str],
    metrics: list[tuple[str, str, str]],
    tags: list[str],
    visual: str,
    desc: str,
) -> str:
    w, h = 1000, 360
    style = (
        f".mono{{font-family:{MONO}}}.sans{{font-family:{SANS}}}"
        "@keyframes pop{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
        ".pop{opacity:0;animation:pop .5s ease-out forwards}"
        "@keyframes blink{50%{opacity:.2}}.blink{animation:blink 1.4s ease-in-out infinite}"
    )
    text = "".join(
        f'<text x="40" y="{116 + i * 23}" class="sans" font-size="16" fill="{MUTED}">{escape(t)}</text>'
        for i, t in enumerate(tagline)
    )
    body = (
        "<defs>"
        + card_defs(w, h)
        + neon_gradient("neon", 240, 6)
        + f'<clipPath id="cl"><rect width="{w}" height="{h}" rx="20"/></clipPath>'
        + "</defs>"
        + card_bg(w, h)
        + f'<g clip-path="url(#cl)"><circle cx="{w - 120}" cy="60" r="150" fill="{color}" opacity=".12" '
        f'filter="url(#soft)"/></g>'
        + f'<text x="40" y="44" class="mono" font-size="12" fill="{color}" letter-spacing="1.5">'
        f"PROJECT {index} · {escape(kind)}</text>"
        + f'<text x="40" y="86" class="sans" font-size="38" font-weight="800" fill="{TEXT}" letter-spacing="-.5">'
        f"{escape(name)}</text>"
        + text
        + metric_tiles(metrics, 40, 170)
        + tag_row(tags, 40, 296, color)
        + visual
        + f'<text x="{w - 40}" y="44" text-anchor="end" class="mono" font-size="12" fill="{DIM}">'
        f"github.com/joecodeai/{name.lower()} ↗</text>"
    )
    return svg(w, h, name, desc, body, style)


def streamsight_visual() -> str:
    x0, y0 = 640, 92
    tw, th, gap = 150, 92, 12
    out = []
    boxes = [
        ((28, 30, 30, 44), "11", (40, 0)),
        ((86, 32, 28, 42), "07", (-24, 0)),
        ((40, 30, 30, 44), "07", (30, 0)),
        ((70, 32, 28, 42), "23", (-26, 0)),
    ]
    for i in range(4):
        cx = x0 + (i % 2) * (tw + gap)
        cy = y0 + (i // 2) * (th + gap)
        (bx, by, bw, bh), tid, (dx, dy) = boxes[i]
        col = MAGENTA if tid == "07" else CYAN
        out.append(
            f'<rect x="{cx}" y="{cy}" width="{tw}" height="{th}" rx="10" fill="#0b1020" stroke="#ffffff" '
            f'stroke-opacity=".12"/>'
            f'<text x="{cx + 9}" y="{cy + 16}" class="mono" font-size="9.5" fill="{DIM}">CAM 0{i + 1}</text>'
            f'<circle cx="{cx + tw - 12}" cy="{cy + 12}" r="3.5" fill="#ef4444" class="blink"/>'
            f'<line x1="{cx + 6}" x2="{cx + tw - 6}" y1="{cy + th - 14}" y2="{cy + th - 14}" stroke="#ffffff" '
            f'stroke-opacity=".06"/>'
            f'<g><animateTransform attributeName="transform" type="translate" values="0 0;{dx} {dy};0 0" '
            f'dur="{5 + i}s" repeatCount="indefinite"/>'
            f'<rect x="{cx + bx}" y="{cy + by}" width="{bw}" height="{bh}" rx="3" fill="{col}" fill-opacity=".1" '
            f'stroke="{col}" stroke-width="1.6"/>'
            f'<rect x="{cx + bx}" y="{cy + by - 13}" width="34" height="12" rx="2" fill="{col}"/>'
            f'<text x="{cx + bx + 4}" y="{cy + by - 4}" class="mono" font-size="9" fill="#05060d" '
            f'font-weight="700">id {tid}</text></g>'
        )
    # Cross-camera re-identification link between the two sightings of id 07.
    ax, ay = x0 + tw + gap + 86 + 14, y0 + 32 + 42
    bx_, by_ = x0 + 40 + 15, y0 + th + gap + 30
    out.append(
        f'<path d="M{ax},{ay} C{ax + 40},{ay + 60} {bx_ - 40},{by_ - 60} {bx_},{by_}" fill="none" '
        f'stroke="{MAGENTA}" stroke-width="1.5" stroke-dasharray="5 5" opacity=".8">'
        f'<animate attributeName="stroke-dashoffset" from="0" to="-40" dur="1.5s" repeatCount="indefinite"/></path>'
        f'<text x="{x0 + 2 * tw + gap}" y="{y0 + 2 * th + gap + 22}" text-anchor="end" class="mono" '
        f'font-size="10.5" fill="{MAGENTA}">cross-camera re-id ⟷</text>'
    )
    return "".join(out)


def ledgerline_visual() -> str:
    x0, y0 = 600, 84
    out = [
        f'<rect x="{x0 + 70}" y="{y0}" width="290" height="38" rx="12" fill="{VIOLET}" fill-opacity=".14"/>'
        f'<text x="{x0 + 84}" y="{y0 + 24}" class="mono" font-size="11.5" fill="{TEXT}">'
        f"How did revenue change last year?</text>",
        f'<rect x="{x0}" y="{y0 + 50}" width="360" height="116" rx="12" fill="#0b1020" stroke="#ffffff" '
        f'stroke-opacity=".12"/>',
    ]
    # Answer "lines" that write themselves, with citation chips.
    for i, (lw, cite) in enumerate([(230, "S1"), (280, "M1"), (190, "Q1")]):
        ly = y0 + 74 + i * 26
        out.append(
            f'<rect x="{x0 + 16}" y="{ly - 6}" width="0" height="8" rx="4" fill="{MUTED}" opacity=".35">'
            f'<animate attributeName="width" values="0;{lw};{lw};0" keyTimes="0;.3;.9;1" dur="6s" '
            f'begin="{i * 0.5}s" repeatCount="indefinite"/></rect>'
            f'<rect x="{x0 + 16 + lw + 8}" y="{ly - 9}" width="26" height="14" rx="7" fill="{CYAN}" fill-opacity=".2">'
            f'<animate attributeName="opacity" values="0;0;1;1;0" keyTimes="0;.28;.32;.9;1" dur="6s" '
            f'begin="{i * 0.5}s" repeatCount="indefinite"/></rect>'
            f'<text x="{x0 + 16 + lw + 21}" y="{ly + 1.5}" text-anchor="middle" class="mono" font-size="9" '
            f'fill="{CYAN}" opacity="0">{cite}<animate attributeName="opacity" values="0;0;1;1;0" '
            f'keyTimes="0;.28;.32;.9;1" dur="6s" begin="{i * 0.5}s" repeatCount="indefinite"/></text>'
        )
    out.append(
        f'<rect x="{x0 + 16}" y="{y0 + 140}" width="112" height="18" rx="9" fill="#22c55e" fill-opacity=".14"/>'
        f'<text x="{x0 + 26}" y="{y0 + 153}" class="mono" font-size="10" fill="#4ade80">✓ figures grounded</text>'
    )
    # Spend sparkline with a flagged anomaly.
    pts = [(0, 40), (30, 34), (60, 38), (90, 26), (120, 30), (150, 20), (180, 24), (210, 8), (240, 22),
           (270, 16), (300, 18), (330, 12), (360, 14)]  # fmt: skip
    path = " ".join(f"{'M' if i == 0 else 'L'}{x0 + px},{y0 + 184 + py}" for i, (px, py) in enumerate(pts))
    out.append(
        f'<path d="{path}" fill="none" stroke="url(#neon)" stroke-width="2" stroke-dasharray="520" '
        f'stroke-dashoffset="520"><animate attributeName="stroke-dashoffset" values="520;0;0" keyTimes="0;.6;1" '
        f'dur="6s" repeatCount="indefinite"/></path>'
        f'<circle cx="{x0 + 210}" cy="{y0 + 192}" r="5" fill="none" stroke="{MAGENTA}" stroke-width="2">'
        f'<animate attributeName="r" values="4;9;4" dur="1.6s" repeatCount="indefinite"/></circle>'
        f'<text x="{x0 + 222}" y="{y0 + 182}" class="mono" font-size="10" fill="{MAGENTA}">anomaly flagged</text>'
    )
    return "".join(out)


def projects() -> dict[str, str]:
    return {
        "project-streamsight.svg": project_card(
            index="01",
            kind="COMPUTER VISION",
            color=CYAN,
            name="StreamSight",
            tagline=[
                "Real-time multi-camera video analytics: detection, tracking,",
                "cross-camera re-identification, pose-based alerts, event API.",
            ],
            metrics=[
                ("1,955 FPS", "DeepStream, 3 streams", "detect + track + re-id"),
                ("1.3 ms", "YOLO11 detector p50", "TensorRT FP16"),
                ("C++", "custom DeepStream", "YOLO11 parser"),
            ],
            tags=["YOLO11", "TensorRT", "DeepStream", "ByteTrack", "OSNet", "Milvus", "FastAPI"],
            visual=streamsight_visual(),
            desc="StreamSight: real-time multi-camera video analytics. 1,955 FPS total on DeepStream for three "
            "streams with detection, tracking and re-identification; YOLO11 detector at 1.3 ms p50 with TensorRT "
            "FP16; custom C++ DeepStream parser.",
        ),
        "project-ledgerline.svg": project_card(
            index="02",
            kind="LLM SYSTEMS · FINTECH",
            color=VIOLET,
            name="Ledgerline",
            tagline=[
                "Agentic financial intelligence: cited answers over SEC filings,",
                "fine-tuned text-to-SQL, fraud signals, guardrails, MCP server.",
            ],
            metrics=[
                ("84.6%", "agent accuracy", "26-question eval"),
                ("25→100%", "text-to-SQL, 1.5B", "after LoRA fine-tune"),
                ("0.88", "recall@6, hybrid", "search + reranker"),
            ],
            tags=["Agents", "RAG", "LoRA", "MCP", "FastAPI", "Next.js", "Kubernetes"],
            visual=ledgerline_visual(),
            desc="Ledgerline: agentic financial intelligence platform. 84.6% answer accuracy on a 26-question "
            "agent evaluation; a LoRA fine-tuned 1.5B text-to-SQL model goes from 25% to 100% execution accuracy "
            "on held-out phrasings; hybrid retrieval with reranking reaches 0.88 recall at 6.",
        ),
    }


HEADERS = [
    ("about", "01", "About", "whoami"),
    ("stack", "02", "Tech stack", "tools I ship with"),
    ("projects", "03", "Featured projects", "public, reproducible, measured"),
    ("activity", "04", "Activity", "refreshed daily by GitHub Actions"),
    ("connect", "05", "Connect", "say hello"),
]


def headers() -> dict[str, str]:
    """Section headers sit on the page background, so they come in dark- and light-theme versions."""
    out = {}
    for slug, num, title, caption in HEADERS:
        out[f"header-{slug}.svg"] = header(num, title, caption)
        out[f"header-{slug}-light.svg"] = header(num, title, caption, light=True)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "hero.svg": hero(),
        "about.svg": about(),
        "stack.svg": stack(),
        "footer.svg": footer(),
        **headers(),
        **projects(),
    }
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"wrote assets/{name} ({len(content.encode()) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
