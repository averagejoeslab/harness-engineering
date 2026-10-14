from lib import *

# ── Lightning talk ──
section("lightning talk")
cover("lt-cover", "Lightning talk · 10 minutes", "Harness Engineering",
      "Every agent is a model inside the same five primitives. Here they are, and how to make them production-ready.",
      "Ten minutes, one idea: Agent = Harness(Model). Move fast; the repo has everything for anyone who wants depth.")

# ── Conference talk ──
section("conference talk")
cover("cf-cover", "Conference talk", "Harness Engineering",
      "A model only predicts the next token. Here's the body that turns it into an agent: five primitives, built one at a time, then made ready for production.",
      "Thirty to forty minutes. Sections one to three in full, one slide per build step, then evaluation, safety and security, and the close.")

# ── Workshop ──
section("workshop")
cover("ws-cover", "Workshop · half a day", "Harness Engineering",
      "Build an agent's body from five primitives on your own machine, evaluate it, and get it ready for production.",
      "Welcome everyone. Today is hands-on: you'll run every step yourself. Check setup first so nobody is stuck later.")

content("ws-agenda", "Workshop", "The plan for today",
        table(["Time", "Part", "You'll do"],
              [["0:00", "Welcome and setup check", "clone the repo, set your key"],
               ["0:15", "What is an agent? Agent primitives", "listen, discuss"],
               ["0:40", "Building a harness: steps 1–4", "Lab 1: build an agent"],
               ["1:35", "Break", ""],
               ["1:50", "Step 5: context", "follow along"],
               ["2:20", "Evaluating the harness", "Lab 2: break it, then catch it"],
               ["2:45", "Getting it ready for production", "Lab 3: attack your agent"],
               ["3:30", "Wrap-up and questions", ""]],
              [12, 48, 40], 28, first_bold=False)
        + p("Suggested timings: adjust to the room.", 24, MUTED),
        "About three and three-quarter hours. The labs are where people learn; protect their time and cut lecture before cutting labs.")

content("ws-setup", "Workshop · before we start", "Check your setup",
        row(card("uv", "Runs every script, and installs each one's dependencies on first run."),
            card("An Anthropic API key", "In your environment, never in a file you commit."),
            card("Docker, running", "Needed for the production harness and `security.py`."), gap=24)
        + panel(["git clone https://github.com/averagejoeslab/harness-engineering",
                 "cd harness-engineering/shop",
                 "export ANTHROPIC_API_KEY=your-key",
                 "uv run ../1_model_interface.py     # you should see a JSON response"]),
        "Have everyone run step 1 now. If they get JSON back, they're ready. Help anyone stuck on Docker during the first lecture block; it's only needed after the break.")

def lab(sid, n, title, steps, tip, note):
    items = "".join(f'<div style="display:flex;flex-direction:row;gap:24px;align-items:flex-start">'
                    f'<p style="font-family:{MONO};font-size:32px;font-weight:600;color:{AMBER};width:48px">{i}</p>'
                    f'<p style="flex:1;font-size:32px;line-height:1.4;color:{ON_DARK}">{md(s, BLUE)}</p></div>'
                    for i, s in enumerate(steps, 1))
    add(sid, open_section(sid, DARK, ON_DARK)
        + header(f"Lab {n} · your turn", title, True)
        + f'<div style="display:flex;flex-direction:column;gap:24px">{items}</div>'
        + f'<p style="font-size:32px;line-height:1.4;color:{ON_DARK_MUTED};border-left:6px solid {AMBER};padding:8px 0px 8px 24px">{md(tip, BLUE)}</p>'
        + footer(True) + notes(note) + "</section>")

lab("ws-lab1", 1, "Build an agent, one primitive at a time",
    ["In `shop/`, run `1_model_interface.py`, `2_input.py`, `3_output.py` and `4_control_flow.py` in turn.",
     "Give each the task. Note which primitive stops each version.",
     "Run `git checkout .`, then give `4_control_flow.py` a new request: *add a count() function*.",
     "Read `4_control_flow.py` top to bottom. Find all five primitives, or the four that are there."],
    "From step 3 on, its commands run on your machine without asking. Watch what it runs.",
    "Twenty minutes. Walk the room. The common surprise is how little code step 4 needs to become an agent.")

lab("ws-lab2", 2, "Break it, then catch it",
    ["Run `uv run ../tasks.py` on `harness.py`: expect 5/5.",
     "Change one thing: a line of the mind in `system()`, the tool's description, or the model.",
     "Run the tasks again. What failed, and why?",
     "Add a sixth task to `tasks.py`, with a check on what it did, not what it says."],
    "A good check is one that doing nothing fails, and a correct answer passes.",
    "Twenty-five minutes. Ask people to share the smallest change that broke a task. The lesson: any change is a behavior change.")

lab("ws-lab3", 3, "Attack your own agent",
    ["Start Docker. Run `uv run ../security.py`: expect 4/4.",
     "Write a fifth attack: a new place to hide an instruction, or a new secret to protect.",
     "Run it on `harness_prod.py`. Does a guard hold, and which one?",
     "Check your check: doing nothing should pass it, and obeying the planted text should fail it."],
    "Only aim attacks at the boxed `harness_prod.py`, and only in a throwaway folder.",
    "Thirty minutes inside the production block. Good fifth attacks: an instruction in a file name, in a test's error message, or in a commit message.")
