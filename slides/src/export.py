"""One deck as a single HTML page to present from in any browser, and to print to PDF.
Arrow keys or a click move between slides, N shows the speaker notes, F goes full screen."""
import html, math, re

def connector(m):                                        # <x-connector> is the Slides app's own element: draw it as an SVG line
    x1, y1, x2, y2 = (int(m.group(i)) for i in range(1, 5))
    head, color, width = m.group(5), m.group(6), int(m.group(7))
    pad = 4 * width
    left, top = min(x1, x2) - pad, min(y1, y2) - pad
    w, h = abs(x2 - x1) + 2 * pad, abs(y2 - y1) + 2 * pad
    a, b, c, d = x1 - left, y1 - top, x2 - left, y2 - top
    out = (f'<svg style="position:absolute;left:{left}px;top:{top}px;overflow:visible" width="{w}" height="{h}" aria-hidden="true">'
           f'<line x1="{a}" y1="{b}" x2="{c}" y2="{d}" stroke="{color}" stroke-width="{width}" stroke-linecap="round"/>')
    if head == "end":
        length = math.hypot(c - a, d - b) or 1
        ux, uy = (c - a) / length, (d - b) / length
        size = 4 * width
        bx, by = c - ux * size, d - uy * size
        points = f"{c},{d} {bx - uy * size / 2},{by + ux * size / 2} {bx + uy * size / 2},{by - ux * size / 2}"
        out += f'<polygon points="{points}" fill="{color}"/>'
    return out + "</svg>"

def plain(section):
    return re.sub(r'<x-connector x1="(\d+)" y1="(\d+)" x2="(\d+)" y2="(\d+)" head="(\w+)" style="color:([^;]+);border-width:(\d+)px"></x-connector>',
                  connector, section)

STYLE = """
html, body { margin: 0; height: 100%; background: #0B0D10; }
.slide { position: absolute; left: 50%; top: 50%; width: 1920px; height: 1080px; transform-origin: center; }
.slide:not(.on) { display: none; }
.slide section { position: relative; width: 1920px; height: 1080px; box-sizing: border-box; overflow: hidden; }
.slide section * { margin: 0; box-sizing: border-box; }
.slide section aside { display: none; }
.slide section table { border-collapse: collapse; width: 100%; }
.slide section td, .slide section th { padding: .35em .6em; border-top: 1px solid #E0DACE; text-align: left; vertical-align: top; }
.slide section ul, .slide section ol { padding-left: 1.2em; }
#notes { position: fixed; left: 0; right: 0; bottom: 0; max-height: 35%; overflow: auto; display: none; padding: 16px 24px 36px;
         background: #1E232B; color: #ECE8DF; font: 18px/1.5 'IBM Plex Sans', Arial, sans-serif; }
body.notes #notes { display: block; }
#count { position: fixed; right: 16px; bottom: 10px; color: #8C94A3; font: 14px 'JetBrains Mono', monospace; }
@media print {
  @page { size: 1920px 1080px; margin: 0; }
  html, body { height: auto; background: none; }
  .slide, .slide:not(.on) { display: block !important; position: static !important; transform: none !important; break-after: page; }
  #notes, #count { display: none !important; }
}
"""

SCRIPT = """
const slides = [...document.querySelectorAll('.slide')], notes = document.getElementById('notes'), count = document.getElementById('count');
let at = Math.min(Math.max(parseInt(location.hash.slice(1)) || 1, 1), slides.length) - 1;
function fit() { const k = Math.min(innerWidth / 1920, innerHeight / 1080); slides.forEach(s => s.style.transform = `translate(-50%, -50%) scale(${k})`); }
function show(i) {
  at = Math.min(Math.max(i, 0), slides.length - 1);
  slides.forEach((s, j) => s.classList.toggle('on', j === at));
  const aside = slides[at].querySelector('aside');
  notes.textContent = aside ? aside.textContent : '(no notes)';
  count.textContent = `${at + 1} / ${slides.length}`;
  history.replaceState(null, '', '#' + (at + 1));
}
addEventListener('resize', fit);
addEventListener('keydown', e => {
  if (['ArrowRight', 'ArrowDown', 'PageDown', ' '].includes(e.key)) { e.preventDefault(); show(at + 1); }
  else if (['ArrowLeft', 'ArrowUp', 'PageUp'].includes(e.key)) { e.preventDefault(); show(at - 1); }
  else if (e.key === 'Home') show(0);
  else if (e.key === 'End') show(slides.length - 1);
  else if (e.key === 'n' || e.key === 'N') document.body.classList.toggle('notes');
  else if (e.key === 'f' || e.key === 'F') document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen();
});
addEventListener('click', e => { if (!notes.contains(e.target)) show(e.clientX > innerWidth / 2 ? at + 1 : at - 1); });
fit(); show(at);
"""

def page(title, faces, sections):
    links = "".join(f'<link rel="stylesheet" href="{html.escape(f["href"])}">' for f in faces.values())
    body = "\n".join(f'<div class="slide">{plain(s)}</div>' for s in sections)
    return (f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{html.escape(title)}</title>{links}<style>{STYLE}</style></head>\n<body>\n{body}\n'
            f'<div id="notes"></div><div id="count"></div><script>{SCRIPT}</script></body></html>\n')
