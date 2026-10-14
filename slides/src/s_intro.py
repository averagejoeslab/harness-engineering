from lib import *

# ── Opening ──
section("opening")
cover("cover", "Building the body of an agent", "Harness Engineering",
      "A model only predicts the next token. Build the body that turns it into an agent, one primitive at a time, then get it ready for production.",
      "Welcome. Today we build the body of an agent from scratch. Everything you see comes from the harness-engineering repo: real code and real runs, and you can reproduce all of it.")

statement("one-idea", "The one idea",
          "A model only predicts the next token. The harness is everything that turns that into an agent.",
          "`Agent = Harness(Model)`",
          "If people remember one thing, it's this. The model is the mind; the harness is the body. Harness engineering is the practice of building that body.")

content("leave-with", "Where we're going", "What you'll leave with",
        row(card("The five primitives", "Input, context, model interface, output and control flow: every agent's body, reduced to five parts."),
            card("A working harness", "Built one primitive at a time in Python, and evaluated on tasks with known answers."),
            card("Production readiness", "Six questions to ask of every primitive, from persistence to safety & security."), gap=32),
        "Three outcomes. First the vocabulary: five primitives. Then a harness you build yourself, step by step, on one small task. Then what it takes to leave it running alone.")

# ── What is an agent? ──
section("what is an agent?")
divider("d-agent", "Part 1", "What is an agent?",
        "A system that loops: it observes its inputs, thinks about them, and acts.",
        "Before we build one, we need to agree on what an agent is. We'll use a loop you already run yourself.")

content("dark-room", "A thought experiment", "You're suddenly somewhere completely dark",
        row(card("Observe", "You can't see a thing. There's a floor under your feet, and silence.", DARK, DARK, AMBER, ON_DARK_MUTED),
            card("Think", "Where am I? A room, a cave, a field? That becomes your goal: find out.", DARK, DARK, AMBER, ON_DARK_MUTED),
            card("Act", "You reach out to learn more.", DARK, DARK, AMBER, ON_DARK_MUTED), gap=32)
        + p("What do you do next?", 40, MUTED),
        "Ask the room: what would you do? Let a few people answer. Whatever they say, it's the same shape: notice something, think about it, do something to learn more.")

content("the-loop", "The agent loop", "Observe → think → act, and repeat",
        table(["Observe", "Think", "Act"],
              [["the dark, a floor, silence", "where am I? find out", "reach out"],
               ["something flat and cool", "a wall, so a room: find a switch", "slide your hand along it"],
               ["smooth, smooth, then a small edge", "that's a switch", "flip it"]],
              [32, 36, 32], first_bold=False)
        + p("**Light.** Now you can see where you are, and the loop repeats with whatever you notice next. Every turn started from what the last one taught you.", 32, MUTED),
        "Three turns of the loop. Notice the goal changed as it learned: find out where I am, then find a switch. And each turn starts from what the last one taught you. Acting can also mean waiting and watching.")

statement("no-goal-needed", "What makes it an agent",
          "Nobody has to give it a goal.",
          "An agent can set its own goal from what it observes, change it as it learns, or simply keep watching. What makes it an agent is the loop.",
          "People often define agents by goals or autonomy. Here the definition is the loop itself: observe, think, act, repeat.")

content("you-are-an-agent", "From you to a machine", "Your mind thinks. Your body observes and acts.",
        row(card("In the dark", "Your **mind** did the thinking. Your **body** observed and acted: your hand felt the wall and flipped the switch."),
            card("In an agent", "A **model** does the thinking. A **harness** observes and acts. Together they run the same loop, one turn at a time."), gap=32),
        "This is the bridge. The agents we build have the same two parts as you: a mind and a body. We call them primitives: the model and the harness.")

# ── Agent primitives ──
section("agent primitives")
divider("d-primitives", "Part 2", "Agent primitives",
        "Two parts: a model that thinks, and a harness that observes and acts.",
        "Now we name the parts precisely: what the model does, what it can't do, and the five primitives of the harness.")

add("agent-equals", open_section("agent-equals", DARK, ON_DARK, "display:flex;flex-direction:column;justify-content:center;gap:48px")
    + f'<p style="font-family:{MONO};font-size:96px;font-weight:600;color:{AMBER}">Agent = Harness(Model)</p>'
    + row(card("The model: the mind", "Does the thinking. Tokens go in, and it predicts the next one.", PANEL, PANEL, ON_DARK, ON_DARK_MUTED),
          card("The harness: the body", "Captures input, assembles context, calls the model, handles its output, and defines the loop.", PANEL, PANEL, ON_DARK, ON_DARK_MUTED), gap=32)
    + p("A model alone is a brain in a jar. A harness alone is a body without a head.", 40, ON_DARK_MUTED)
    + footer(True) + notes("The core equation. Neither part is an agent alone: the model can only think, and the harness has nothing to decide what to do. Together they close the loop.") + "</section>")

content("autoregressive", "The model", "It predicts one token at a time",
        table(["Pass", "Reads", "Samples"],
              [["1", "The capital of France", '" is"'],
               ["2", "The capital of France is", '" Paris"'],
               ["3", "The capital of France is Paris", '"."'],
               ["4", "The capital of France is Paris.", "(end)"]],
              [12, 63, 25])
        + p("Each sampled token is appended to what it reads, and it predicts again, until it predicts that it should stop. This is **autoregression**: `TokensOut = Model(TokensIn)`.", 32, MUTED),
        "Real tokens, spaces included. Each pass reads everything before it, including what it just wrote. That's the whole job of a model.")

def bars(title, items):
    out = f'<div style="flex:1;display:flex;flex-direction:column;gap:20px"><h3 style="font-size:40px;font-weight:600;line-height:1.2">{md(title)}</h3>'
    for label, pct, picked in items:
        color = AMBER if picked else "#C9C2B4"
        out += (f'<div style="display:flex;flex-direction:row;align-items:center;gap:16px">'
                f'<p style="font-family:{MONO};font-size:32px;width:200px;white-space:nowrap">{html.escape(label)}</p>'
                f'<div style="width:{max(6, round(pct * 3.6))}px;height:36px;background:{color};border-radius:6px"></div>'
                f'<p style="font-size:32px;font-weight:600;white-space:nowrap">{pct}%{" sampled" if picked else ""}</p></div>')
    return out + "</div>"

content("probabilities", "Chances, then a sample", "Every next token is a chance, then a sample",
        row(bars("Pass 1 reads: The capital of France", [('" is"', 82, True), ('","', 6, False), ('" has"', 4, False), ("the rest", 8, False)]),
            bars("Pass 2 reads: … France is", [('" Paris"', 94, True), ('" a"', 2, False), ('" located"', 1, False), ("the rest", 3, False)]), gap=64)
        + p("The likeliest token usually wins, but not always. Chances here are illustrative.", 32, MUTED),
        "The model gives every possible next token a chance, and one is sampled. The numbers are made up for illustration, but the shape is real: one token usually dominates, and sometimes a less likely one is picked.")

content("model-cant", "The model's limits", "What a model can't do on its own",
        row(card("Capture its inputs", "It only sees what it's handed."),
            card("Assemble its context", "It can't decide what it's shown, or know what time it is."),
            card("Act on its outputs", "Its words change nothing in the world."),
            card("Define the loop", "It answers once, then stops."), gap=24)
        + p("`TokensOut = Model(TokensIn)`. That's all a model does. Everything else is the harness.", 40, MUTED),
        "Four things a model can't do. Each one becomes a job for the harness. Keep this list in mind: each build step fills one gap.")

content("five-primitives", "The harness", "The five harness primitives",
        table(["Primitive", "What it does", "For example"],
              [["Input", "captures what comes in", "a message, the result of an action"],
               ["Context", "assembles what the model is shown", "instructions, the message"],
               ["Model interface", "requests a response from the model", "an API, a local model"],
               ["Output", "handles the model's outputs", "a reply, an action"],
               ["Control flow", "defines the shape of the loop", "go again, hand back, stop"]],
              [24, 40, 36]),
        "Five primitives. Every agent you've used, from a coding assistant to a chatbot that books flights, is a model inside these five. They differ only in how each primitive is built.")

def box(left, w, title, sub, dark=False, top=120, h=130):
    bg, fg, sc, b = (DARK, ON_DARK, ON_DARK_MUTED, DARK) if dark else (LIGHT, INK, MUTED, "#C9C2B4")
    inner = f'<p style="font-size:32px;font-weight:600;color:{fg};text-align:center">{html.escape(title)}</p>'
    if sub: inner += f'<p style="font-family:{MONO};font-size:24px;color:{sc};text-align:center">{html.escape(sub)}</p>'
    return (f'<div style="position:absolute;left:{left}px;top:{top}px;width:{w}px;height:{h}px;background:{bg};border:2px solid {b};'
            f'border-radius:16px;display:flex;flex-direction:column;justify-content:center;align-items:center;gap:4px">{inner}</div>')

def conn(x1, y1, x2, y2, head="end"):
    return f'<x-connector x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" head="{head}" style="color:{MUTED};border-width:3px"></x-connector>'

loop = (f'<div style="position:relative;width:1664px;height:440px">'
        f'<div style="position:absolute;left:0px;top:0px;width:1380px;height:440px;background:{CARD};border:3px solid #C9C2B4;border-radius:24px"></div>'
        f'<p style="position:absolute;left:40px;top:28px;width:400px;font-family:{MONO};font-size:24px;color:{MUTED}">harness</p>'
        + box(40, 220, "input", "") + box(320, 240, "context", "") + box(620, 400, "model", "tokens in → next token ↺", True)
        + box(1080, 240, "output", "") + box(1440, 224, "world", "")
        + conn(260, 185, 320, 185) + conn(560, 185, 620, 185) + conn(1020, 185, 1080, 185) + conn(1320, 185, 1440, 185)
        + conn(1200, 250, 1200, 350, "none") + conn(1200, 350, 150, 350, "none") + conn(150, 350, 150, 250)
        + f'<p style="position:absolute;left:380px;top:366px;width:660px;font-size:24px;color:{MUTED};text-align:center">what happened: a message, a tool\'s result</p>'
        + "</div>")
content("loop-diagram", "The harness", "The model's loop, inside the harness",
        loop + p("Input captures, context assembles, the **model interface** makes the call, output acts on the world, and **control flow** is the shape of the whole loop.", 32, MUTED),
        "Trace one turn: something comes in, the harness assembles what the model sees, calls it, acts on what it says, and what happened comes back around as new input. The model's own loop, token by token, sits inside the harness's loop.")
