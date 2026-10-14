"""Slide templates for the Harness Engineering decks: every slide is one <section> in the Slides subset."""
import html, re

SANS = "'IBM Plex Sans', Arial, sans-serif"
MONO = "'JetBrains Mono', 'Courier New', monospace"

DARK, PANEL, LIGHT, CARD, LINE = "#14171C", "#1E232B", "#F5F2EB", "#FBF9F4", "#E0DACE"
INK, MUTED = "#1A1D23", "#555C68"
ON_DARK, ON_DARK_MUTED = "#ECE8DF", "#A9B0BC"
AMBER, AMBER_INK, BLUE, BLUE_INK = "#F0A33A", "#8F5100", "#7FB2FF", "#2457A6"
GRAY, OUT = "#8C94A3", "#AEB6C2"

SLIDES = {}                                              # id -> html
FOOT = {"label": ""}                                     # the footer's section label, set per section

def section(label):
    FOOT["label"] = label

def add(sid, body):
    assert sid not in SLIDES, sid
    SLIDES[sid] = body

def md(text, code=BLUE_INK):                            # **bold** and `code`, escaped
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"`(.+?)`", lambda m: f'<span style="color:{code}">{m.group(1)}</span>', text)

def notes(text):
    return f"<aside>{html.escape(text, quote=False)}</aside>"

def footer(dark=False):
    color = ON_DARK_MUTED if dark else MUTED
    return (f'<p style="position:absolute;left:128px;bottom:64px;width:1664px;font-family:{MONO};font-size:24px;'
            f'color:{color}">harness engineering · {html.escape(FOOT["label"])}</p>')

def open_section(sid, bg, color, layout="display:flex;flex-direction:column;gap:40px", pad="128px 128px 160px"):
    return f'<section id="{sid}" data-transition="fade" style="background:{bg};color:{color};font-family:{SANS};padding:{pad};{layout}">'

def header(eyebrow, title, dark=False):
    eb = AMBER if dark else AMBER_INK
    tc = ON_DARK if dark else INK
    return (f'<div style="display:flex;flex-direction:column;gap:16px">'
            f'<p style="font-family:{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:{eb}">{html.escape(eyebrow)}</p>'
            f'<h2 style="font-size:64px;font-weight:600;line-height:1.15;color:{tc}">{md(title)}</h2></div>')

def p(text, size=32, color=None, extra=""):
    c = f"color:{color};" if color else ""
    return f'<p style="font-size:{size}px;line-height:1.4;{c}{extra}">{md(text)}</p>'

# ── code and terminal panels: one <p> per line, spaces kept as &#160;, no wrapping ──
def _sp(text):
    return html.escape(text, quote=False).replace(" ", "&#160;")

KEYS = ("def ", "return ", "if ", "for ", "while ", "with ", "import ", "from ", "elif ", "else:", "try:", "except ")

def code_line(line):
    if not line.strip():
        return f'<p style="white-space:nowrap">&#160;</p>'
    body, comment = line, ""
    if line.lstrip().startswith("#"):
        body, comment = "", line
    elif "  # " in line:
        i = line.index("  # ")
        body, comment = line[:i], line[i:]
    out = ""
    stripped = body.lstrip()
    lead = body[:len(body) - len(stripped)]
    key = next((k for k in KEYS if stripped.startswith(k)), None)
    if key:
        out += _sp(lead) + f'<span style="color:{BLUE}">{_sp(key.rstrip())}</span>' + _sp(stripped[len(key.rstrip()):])
    else:
        out += _sp(body)
    if comment:
        out += f'<span style="color:{GRAY}">{_sp(comment)}</span>'
    return f'<p style="white-space:nowrap">{out}</p>'

TERM = {"u": AMBER, "m": ON_DARK, "c": BLUE, "o": OUT, "t": GRAY, "y": GRAY, "h": GRAY, "n": ON_DARK}

def term_line(line):                                     # first character is the kind: u you, m model, c command, o output, t thinking, y approval, h note
    kind, text = line[0], line[1:]
    if not text.strip():
        return f'<p style="white-space:nowrap">&#160;</p>'
    style = f"white-space:nowrap;color:{TERM[kind]}" + (";font-style:italic" if kind in "th" else "")
    return f'<p style="{style}">{_sp(text)}</p>'

def panel(lines, kind="code", size=24, bg=DARK, extra=""):
    render = code_line if kind == "code" else term_line
    body = "".join(render(l) for l in lines)
    return (f'<div style="background:{bg};border-radius:16px;padding:32px 40px;overflow:hidden;{extra}">'
            f'<div style="display:flex;flex-direction:column;font-family:{MONO};font-size:{size}px;line-height:1.45;color:{ON_DARK}">{body}</div></div>')

def pill(text, dark=False):                              # the command you run, above a run
    bg, fg = (PANEL, ON_DARK) if dark else ("#E8E3D8", INK)
    return (f'<div style="display:flex;flex-direction:row"><p style="font-family:{MONO};font-size:24px;background:{bg};color:{fg};'
            f'padding:10px 20px;border-radius:10px;white-space:nowrap">{_sp(text)}</p></div>')

def card(title, text, bg=CARD, border=LINE, title_color=INK, text_color=MUTED, extra="flex:1"):
    return (f'<div style="{extra};display:flex;flex-direction:column;gap:12px;background:{bg};border:1px solid {border};border-radius:16px;padding:32px">'
            f'<h3 style="font-size:40px;font-weight:600;line-height:1.2;color:{title_color}">{md(title)}</h3>'
            f'<p style="font-size:32px;line-height:1.4;color:{text_color}">{md(text)}</p></div>')

def row(*children, gap=24, extra=""):
    return f'<div style="display:flex;flex-direction:row;gap:{gap}px;{extra}">' + "".join(children) + "</div>"

def table(head, rows, widths, size=32, first_bold=True, mono_first=False):
    cells = "".join(f'<th style="width:{w}%;text-align:left;font-weight:600;color:{INK}">{md(h)}</th>' for h, w in zip(head, widths))
    out = f'<table style="font-size:{size}px;color:{INK};border:1px solid {LINE};border-radius:12px"><tr style="background:#EAE5DA">{cells}</tr>'
    for i, r in enumerate(rows):
        bg = CARD if i % 2 == 0 else LIGHT
        tds = ""
        for j, c in enumerate(r):
            text = md(c)
            if j == 0 and first_bold: text = f"<b>{text}</b>"
            tds += f"<td>{text}</td>"
        out += f'<tr style="background:{bg}">{tds}</tr>'
    return out + "</table>"

# ── slide kinds ──
def cover(sid, eyebrow, title, sub, note):
    add(sid, open_section(sid, DARK, ON_DARK, "display:flex;flex-direction:column;justify-content:space-between", "128px")
        + f'<div style="display:flex;flex-direction:column;gap:32px">'
        + f'<p style="font-family:{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:{AMBER}">{html.escape(eyebrow)}</p>'
        + f'<h1 style="font-size:120px;font-weight:600;line-height:1.1;color:{ON_DARK}">{md(title)}</h1>'
        + f'<p style="font-size:40px;line-height:1.35;color:{ON_DARK_MUTED};width:1300px">{md(sub)}</p></div>'
        + f'<div style="display:flex;flex-direction:row;justify-content:space-between;align-items:flex-end">'
        + f'<div style="display:flex;flex-direction:column;gap:8px"><p style="font-size:32px;font-weight:600;color:{ON_DARK}">Chase Dovey · Average Joes Lab</p>'
        + f'<p style="font-family:{MONO};font-size:24px;color:{ON_DARK_MUTED}">github.com/averagejoeslab/harness-engineering</p></div>'
        + f'<p style="font-family:{MONO};font-size:32px;color:{AMBER}">agent = harness(model)</p></div>'
        + notes(note) + "</section>")

def divider(sid, part, title, sentence, note):
    add(sid, open_section(sid, DARK, ON_DARK, "display:flex;flex-direction:column;justify-content:center;gap:32px", "128px")
        + f'<p style="font-family:{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:{AMBER}">{html.escape(part)}</p>'
        + f'<h1 style="font-size:120px;font-weight:600;line-height:1.1;color:{ON_DARK}">{md(title)}</h1>'
        + f'<p style="font-size:40px;line-height:1.35;color:{ON_DARK_MUTED};width:1400px">{md(sentence)}</p>'
        + notes(note) + "</section>")

def statement(sid, eyebrow, text, sub, note, dark=False):
    bg, fg, sc, eb = (DARK, ON_DARK, ON_DARK_MUTED, AMBER) if dark else (LIGHT, INK, MUTED, AMBER_INK)
    add(sid, open_section(sid, bg, fg, "display:flex;flex-direction:column;justify-content:center;gap:40px")
        + f'<p style="font-family:{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:{eb}">{html.escape(eyebrow)}</p>'
        + f'<h1 style="font-size:72px;font-weight:600;line-height:1.15;color:{fg};width:1600px">{md(text)}</h1>'
        + (f'<p style="font-size:40px;line-height:1.4;color:{sc};width:1500px">{md(sub, BLUE if dark else BLUE_INK)}</p>' if sub else "")
        + footer(dark) + notes(note) + "</section>")

def content(sid, eyebrow, title, body, note, dark=False):
    add(sid, open_section(sid, DARK if dark else LIGHT, ON_DARK if dark else INK)
        + header(eyebrow, title, dark) + body + footer(dark) + notes(note) + "</section>")

def missing(sid, eyebrow, text, nxt, note, body=""):     # the cliffhanger: amber, what this version still can't do
    add(sid, open_section(sid, AMBER, INK, "display:flex;flex-direction:column;justify-content:space-between;gap:40px")
        + f'<div style="display:flex;flex-direction:column;gap:32px">'
        + f'<p style="font-family:{MONO};font-size:24px;letter-spacing:2px;text-transform:uppercase;color:{INK}">{html.escape(eyebrow)}</p>'
        + f'<h1 style="font-size:72px;font-weight:600;line-height:1.15;color:{INK};width:1600px">{md(text, INK)}</h1></div>'
        + body
        + f'<p style="font-size:40px;font-weight:600;color:{INK}">Next → {md(nxt, INK)}</p>'
        + f'<p style="position:absolute;left:128px;bottom:64px;width:1664px;font-family:{MONO};font-size:24px;color:{INK}">harness engineering · {html.escape(FOOT["label"])}</p>'
        + notes(note) + "</section>")

def progress(step):                                      # the five build steps, this one lit
    names = ["Model interface", "Input", "Output", "Control flow", "Context"]
    out = ""
    for i, n in enumerate(names, 1):
        if i == step: bg, fg, border = AMBER, INK, AMBER
        elif i < step: bg, fg, border = "#2A2F38", ON_DARK, "#2A2F38"
        else: bg, fg, border = LIGHT, MUTED, "#C9C2B4"
        out += (f'<div style="flex:1;display:flex;flex-direction:column;gap:4px;background:{bg};border:2px solid {border};border-radius:12px;padding:16px 20px">'
                f'<p style="font-family:{MONO};font-size:24px;color:{fg}">step {i}</p>'
                f'<p style="font-size:32px;font-weight:600;color:{fg}">{n}</p></div>')
    return row(out, gap=16)
