"""Builds the decks: the master and four cut for a purpose.
Each is written as decks/<name>/project/deck.json + project/slides/<id>.html (the Slides format),
and as <name>.html, one page to present from in any browser.    python3 build.py"""
import json, os, re, sys, shutil, datetime
from html.parser import HTMLParser
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "src"))
import lib
LABELS = {}
_add = lib.add
def add(sid, body):                                      # remember each slide's section label
    LABELS[sid] = lib.FOOT["label"]; _add(sid, body)
lib.add = add
import s_intro, s_build, s_context, s_prod, s_prod2, s_extra, export
BEFORE_VIDEO = set(SLIDES := lib.SLIDES)
import s_video
VIDEO_ONLY = set(SLIDES) - BEFORE_VIDEO

OUT = os.path.join(HERE, "decks")
NOW = "2026-10-14T04:09:34Z"                          # when the decks were first created
FACES = {"ibm-plex-sans": {"family": "IBM Plex Sans", "href": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&display=swap"},
         "jetbrains-mono": {"family": "JetBrains Mono", "href": "https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,400;0,600;1,400&display=swap"}}

EXTRA = ("lt-", "cf-", "ws-")
MASTER = [s for s in SLIDES if not s.startswith(EXTRA) and s not in VIDEO_ONLY]

NICE = {"opening": "Opening: the one idea, and what you'll leave with.",
        "what is an agent?": "What is an agent? A system that observes, thinks and acts, in a loop.",
        "agent primitives": "Agent primitives: a model that thinks, a harness that observes and acts.",
        "building a harness": "Building a harness outward from the model, on one small task.",
        "step 1 · reach the model": "Step 1: the model interface reaches the model.",
        "step 2 · let someone ask": "Step 2: input lets someone ask.",
        "step 3 · let it act": "Step 3: output lets it act through one shell.",
        "step 4 · let it keep going": "Step 4: control flow lets it keep going; now it's an agent.",
        "step 5 · give it context": "Step 5: context tells it what it is and how to use its body.",
        "evaluating the harness": "Evaluating the harness on tasks with known right answers.",
        "production": "Getting it ready for production: six questions of every primitive.",
        "production · persistence": "Persistence: what should outlast the session?",
        "production · safety & security": "Safety & Security: what could do harm, and who could make it?",
        "production · observability": "Observability: what did it actually do?",
        "production · resilience": "Resilience: what if something breaks?",
        "production · performance": "Performance: why is it slow or costly?",
        "production · evaluation": "Evaluation: how do we know it still works?",
        "what you built": "What you built, and every agent is these five.",
        "lightning talk": "Lightning talk: Agent = Harness(Model) in ten minutes.",
        "conference talk": "Opening: the one idea, and what you'll leave with.",
        "workshop": "Welcome, the plan for today, and a setup check."}

def sections_by_label(order, skip=()):
    out, last = {}, None
    for sid in order:
        if sid in skip: continue
        label = LABELS[sid]
        if sid.endswith("cover") and label in ("lightning talk", "conference talk", "workshop"): label = label
        if label != last:
            out[f"s{len(out) + 1}"] = {"description": NICE[label], "start": sid}
            last = label
    return out

def lint(sid, body):                                     # tags balance, and the slide stays inside the subset's counts
    class P(HTMLParser):
        def __init__(self): super().__init__(); self.stack, self.n = [], 0
        def handle_starttag(self, tag, attrs):
            self.n += 1
            if tag not in ("br", "hr", "img"): self.stack.append(tag)
        def handle_endtag(self, tag):
            assert self.stack and self.stack[-1] == tag, f"{sid}: </{tag}> closes {self.stack[-1:]}"
            self.stack.pop()
    p = P(); p.feed(body); assert not p.stack, f"{sid}: unclosed {p.stack}"
    assert p.n <= 200, f"{sid}: {p.n} elements"
    small = [int(x) for x in re.findall(r"font-size:(\d+)px", body) if int(x) < 24]
    assert not small, f"{sid}: text under 24px"
    assert len(re.findall(r"<aside>(.*?)</aside>", body, re.S)[0]) <= 4000

def write(name, title, order, sections):
    root = os.path.join(OUT, name)
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(os.path.join(root, "project", "slides"))
    deck = {"v": 4, "createdOnFiles": {"v": 1, "at": NOW}, "lists": "css", "title": title, "order": order,
            "sections": sections, "cover": order[0], "faces": FACES, "designSystems": []}
    json.dump(deck, open(os.path.join(root, "project", "deck.json"), "w"), indent=1, ensure_ascii=False)
    for sid in order:
        open(os.path.join(root, "project", "slides", f"{sid}.html"), "w").write(SLIDES[sid])
    open(os.path.join(HERE, f"{name}.html"), "w").write(export.page(title, FACES, [SLIDES[sid] for sid in order]))
    print(f"{name:12} {len(order):3} slides, {len(sections)} sections")

for sid, body in SLIDES.items(): lint(sid, body)

write("master", "Harness Engineering — Master Deck", MASTER, sections_by_label(MASTER))

lightning = ["lt-cover", "one-idea", "the-loop", "agent-equals", "five-primitives", "loop-diagram", "s4-run",
             "six-questions", "safety-vs-security", "built", "every-agent", "next-steps"]
write("lightning", "Harness Engineering — Lightning Talk", lightning, {"s1": {"description": NICE["lightning talk"], "start": "lt-cover"}})

conference = ["cf-cover", "one-idea", "leave-with",
              "d-agent", "dark-room", "the-loop", "no-goal-needed", "you-are-an-agent",
              "d-primitives", "agent-equals", "autoregressive", "probabilities", "model-cant", "five-primitives", "loop-diagram",
              "d-build", "build-outward", "s1-missing", "s2-missing", "s3-missing", "s4-run", "s4-missing", "s5-what", "s5-assembly", "s5-run",
              "d-eval", "one-run", "tasks",
              "d-prod", "six-questions", "safety-vs-security", "safety-box", "security-threats", "security-guards", "security-runs", "security-eval",
              "d-close", "built", "every-agent", "next-steps"]
conf_sections = {"s1": {"description": NICE["opening"], "start": "cf-cover"},
                 "s2": {"description": NICE["what is an agent?"], "start": "d-agent"},
                 "s3": {"description": NICE["agent primitives"], "start": "d-primitives"},
                 "s4": {"description": "Building a harness: one slide per step, then the agent that knows what it is.", "start": "d-build"},
                 "s5": {"description": NICE["evaluating the harness"], "start": "d-eval"},
                 "s6": {"description": "Production, through its sharpest question: safety & security.", "start": "d-prod"},
                 "s7": {"description": NICE["what you built"], "start": "d-close"}}
write("conference", "Harness Engineering — Conference Talk", conference, conf_sections)

workshop = ["ws-cover", "ws-agenda", "ws-setup"] + MASTER[1:]
for after, lab in (("s4-missing", "ws-lab1"), ("tasks-run", "ws-lab2"), ("security-eval", "ws-lab3")):
    workshop.insert(workshop.index(after) + 1, lab)
ws_sections = sections_by_label(workshop, skip={"ws-lab1", "ws-lab2", "ws-lab3"})
write("workshop", "Harness Engineering — Workshop", workshop, ws_sections)

build = lambda n: [f"s{n}-what", f"s{n}-code", f"s{n}-run"]
video = (["v-cover", "v1",
          "v1a", "one-idea", "leave-with", "dark-room", "the-loop", "no-goal-needed", "you-are-an-agent",
          "v1b", "agent-equals", "autoregressive", "probabilities", "model-cant", "five-primitives", "loop-diagram",
          "v1c", "build-outward", "setup", "leave-alone", "six-questions",
          "v2"] + build(1) + ["mi-production", "mi-retries", "mi-stream", "mi-record", "s1-missing",
          "v3"] + build(2) + ["in-production", "in-approval", "in-results", "s2-missing",
          "v4"] + build(3) + ["out-production", "safety-box", "safety-run", "out-secrets", "out-secret-run", "res-timeout", "perf-parallel", "s3-missing",
          "v5"] + build(4) + ["cf-production", "cf-diary", "persist-run", "obs-record", "cf-compact", "cf-final", "s4-missing",
          "v6", "s5-what", "s5-roles", "s5-tokens", "s5-placing", "s5-window", "s5-assembly", "s5-order", "s5-code", "s5-run",
                 "ctx-production", "persist-memories", "ctx-memory", "ctx-trust", "ctx-injection-run", "ctx-cache", "obs-thinking", "s5-done",
          "v7", "one-run", "tasks", "tasks-run", "security-threats", "security-eval", "eval-again",
                 "built", "every-agent", "next-steps"])
video_sections = {}
def vs(start, text): video_sections[f"s{len(video_sections) + 1}"] = {"description": text, "start": start}
vs("v-cover", "Video 1, introduction: what an agent is.")
vs("v1b", "Video 1, introduction: agent primitives.")
vs("v1c", "Video 1, introduction: the plan.")
for v, name in (("v2", "model interface"), ("v3", "input"), ("v4", "output"), ("v5", "control flow"), ("v6", "context")):
    n = v[1]
    vs(v, f"Video {n}: building {name}.")
    vs({"v2": "mi-production", "v3": "in-production", "v4": "out-production", "v5": "cf-production", "v6": "ctx-production"}[v], f"Video {n}: {name} in production.")
vs("v7", "Video 7, conclusion: evaluating the harness.")
vs("built", "Video 7, conclusion: what you built.")
write("video", "Harness Engineering — Video Series", video, video_sections)
assert len(set(video)) == len(video), "a slide twice in the video deck"
