from lib import *

# ── Step 5 ──
section("step 5 · give it context")
content("s5-what", "Step 5 · Context", "Give it context",
        progress(5)
        + p("**Context** is what the model is shown on each call. From the agent's side, it's working memory: everything it has in mind at this moment.", 40)
        + p("Whatever isn't in its context, the agent doesn't have in mind. So what we put there, and how, shapes everything it does.", 32, MUTED),
        "The last primitive, and the deepest. We'll take it in parts: roles, placing a chunk, fitting the window, then how harness.py does it.")

ladder = [("system", "the mind: who it is, its drives, how it operates", "most authority"),
          ("tools", "the body: what it can do, and how", ""),
          ("user", "the world: people and programs reaching it", ""),
          ("assistant", "the self, acting: its words and actions", ""),
          ("user", "a tool's result: what the world returned", "least")]
rows = ""
for i, (role, what, auth) in enumerate(ladder):
    shade = ["#14171C", "#2E3440", "#555C68", "#8A919C", "#B9BEC6"][i]
    fg = ON_DARK if i < 3 else INK
    rows += (f'<div style="display:flex;flex-direction:row;align-items:center;gap:24px">'
             f'<p style="width:240px;font-family:{MONO};font-size:32px;font-weight:600;background:{shade};color:{fg};padding:16px 24px;border-radius:12px">{role}</p>'
             f'<p style="flex:1;font-size:32px">{md(what)}</p>'
             f'<p style="width:260px;font-size:24px;color:{MUTED};text-align:right">{auth}</p></div>')
content("s5-roles", "Step 5 · roles", "Every chunk sits in a role",
        p("The model learned in training how much authority each role carries. For Claude, from most to least:", 32, MUTED)
        + f'<div style="display:flex;flex-direction:column;gap:16px">{rows}</div>',
        "Once we know which chunks we want in context, the roles and their hierarchy decide how to organize them. The model learned this ladder in training. Note the last row: a tool's result comes back in the user role, with the least authority.")

content("s5-tokens", "Step 5 · roles are tokens", "Underneath, roles are tokens too",
        panel(["<｜begin▁of▁sentence｜>You are an agent.",
               "<｜User｜>Which files are in this folder?",
               "<｜Assistant｜></think>"], size=32)
        + p("A short context in DeepSeek's published format, every token real (one line, broken here to fit). `<｜User｜>` and `<｜Assistant｜>` mark the roles; `</think>` switches its thinking off.", 32, MUTED)
        + p("Role markers tell the model who is speaking, so it writes only its own turn and stops at the end of it. That's what makes it more than autocomplete.", 32),
        "Each provider has its own markers. Claude's aren't published, so later we show the request the harness sends instead. The model writes on from the end, one token at a time, and stops with its end token.")

content("s5-placing", "Step 5 · placing a chunk", "Three questions place every chunk",
        row(card("Who does it serve?", "The agent's identity, its body, the person, the world."),
            card("How much does it matter?", "Rules it must follow, or information to weigh."),
            card("Where did it come from?", "You, the person, or something it read in the world."), gap=32)
        + p("The answers pick its role, and **its role should never give it more authority than its source.**", 40),
        "This rule matters again in security: text from a file the agent read must never sit somewhere with more authority than the file deserves.")

content("s5-window", "Step 5 · fitting the window", "The window has a fixed size",
        p("The harness assembles context fresh on each call. As a session grows, the window fills. It can count tokens to see that coming, or wait for the “too long” error. Either way, it has to make room:", 32, MUTED)
        + table(["Strategy", "What it does", "Keeps", "Loses"],
                [["Sliding window", "drops the oldest messages", "the recent", "the start, maybe the task"],
                 ["Compaction", "summarizes the oldest part", "the gist", "the detail"],
                 ["Cherry-picked assembly", "includes only what this moment needs", "focus", "the rest, until it's fetched"]],
                [24, 32, 16, 28]),
        "Three strategies, each a trade. harness.py uses compaction: it waits for the too-long error, then summarizes the oldest part.")

content("s5-assembly", "Step 5 · harness.py", "How harness.py assembles context",
        table(["Role", "Holds", "What goes there"],
              [["system", "the mind", "who it is, its drives, its model, its loop, when and where it was born, how carefully to change things, its own harness code"],
               ["tools", "the body", "the shell, named for this computer, with how to use it"],
               ["user", "the world", "what you type, stamped with when it came in; each result, stamped with how long it ran"],
               ["assistant", "the self", "its words and commands, as they came back"]],
              [16, 16, 68], 28)
        + p("**Size:** it waits for the “too long” error, then `compact()` summarizes the oldest part into a user message.", 32, MUTED),
        "The mind, the body, the world. Timestamps on every message mean it always knows what now is. It even sees its own harness code, minus the parts it's already reading.")

content("s5-order", "Step 5 · the body's description", "An order of operations for the body",
        table(["", "Operation", "How it checks the result"],
              [["1", "Files and data, directly: commands and scripts", "the exit code and the result"],
               ["2", "The app's own interface: its CLI or API", "ask the app for its state"],
               ["3", "Named controls: accessibility buttons and fields", "list the window's controls"],
               ["4", "Pixels, only for what's truly visual", "compare a new screenshot with the last"]],
              [6, 54, 40], 28)
        + p("Use the most precise operation that can reach the target, and read the result back. Fall back only when it can't. What it reads back, not what it expected, decides whether it worked.", 32, MUTED),
        "The tool's description centers on this. The shop task only needs the first. The point is that the shell can reach everything a person can, if the agent knows the order to try things in.")

content("s5-code", "Step 5 · harness.py", "Stamp, assemble, compact",
        panel(["def stamp(text, start=None):  # current inputs: when it came in, and how long it ran",
               "    now = datetime.datetime.now()",
               "    ran = f\", ran {(now - start).total_seconds():.1f}s\" if start else \"\"",
               "    return f\"[{now:%Y-%m-%d %H:%M:%S}{ran}] {text}\"",
               "",
               "def system():  # self model: the mind, as the system prompt",
               "    return [{\"type\": \"text\", \"cache_control\": {\"type\": \"ephemeral\"}, \"text\": f\"\"\"# Mind …\"\"\"}]",
               "",
               "def assemble_context(messages):  # mind as system prompt, body as tool, world as messages",
               "    return {\"system\": system(), \"tools\": tools, \"messages\": messages}",
               "",
               "def compact(messages, drop):  # too long to send, so the older part is summarized",
               "    …  # keep the newer turns, ask the model for a gist, and carry on from it",
               "    return [{\"role\": \"user\", \"content\": f\"[the earlier conversation, summarized] {gist}\"}]"]),
        "Four functions. stamp gives every input a time. system is the mind. assemble_context puts mind, body and world in their roles. compact runs when the API says the prompt is too long.")

content("s5-run", "Step 5 · the run", "It knows what it is",
        pill("uv run ../harness.py")
        + panel(["u< Who are you, and where are you working?",
                 "c$ pwd; whoami; hostname; uname -sr; ls -la | head -30",
                 "o  └ /home/user/harness-engineering/shop …",
                 "m> I'm an AI agent that works for whoever messages me. I act through a single shell tool, and I",
                 "m  check my work by reading results back instead of guessing. I run on the Claude model",
                 "m  `claude-sonnet-5-5`, inside a small harness that sends your messages to the model, runs the",
                 "m  commands it asks for, and returns the output.",
                 "m  …",
                 "m  I'll read freely, but I'll go one step at a time and check each change as I make it. For",
                 "m  anything I can't undo, I'll ask you first. What would you like me to do?"], "term")
        + p("Its commands only checked the machine and the folder. **That's all five primitives.**", 32),
        "Compare with step 4: it knew what it was, and that its body is a shell, from what it's shown. harness.py is a complete harness. What it lacks is proof.")

# ── Evaluating ──
section("evaluating the harness")
divider("d-eval", "Part 4", "Evaluating the harness",
        "We've seen it do one task, once. Tasks with known answers tell us more.",
        "A working demo isn't evidence. Evaluation is how we know a change didn't break anything.")

statement("one-run", "Why evaluate", "One good run proves nothing.",
          "Any change can change what the agent does: its instructions, its model, its tools. Will it do the task again, or a different one?",
          "Every change to the mind, the body or the model is a change in behavior. You need a way to check that isn't watching it by eye.")

content("tasks", "tasks.py", "Tasks with known right answers",
        table(["Task", "Passes when"],
              [["Fix the failing test", "the tests pass, and the test file is unchanged"],
               ["Add a `count()` function", "it returns the right numbers"],
               ["Write the names of the `.py` files into a file", "the file lists exactly them"],
               ["Answer a question without changing anything", "nothing changed, and the answer is right"],
               ["Name the operating system, into a file", "the file names it"]],
              [50, 50])
        + p("Each runs in a fresh copy of `shop/`. We check **what it did**, not what it says.", 32, MUTED),
        "Five tasks. Note the first check: the test file must be unchanged, so deleting or editing the test doesn't count as a fix. Checking what it did, not what it says, keeps it honest.")

content("tasks-run", "tasks.py · the run", "5 of 5",
        pill("git checkout . && uv run ../tasks.py")
        + panel(["oPASS  The tests are failing. Find out why and fix it.",
                 "oPASS  Add a function count(items) to prices.py that returns how many items are in the basket, …",
                 "oPASS  Write the names of the .py files in this folder, one per line, sorted, into files.txt.",
                 "oPASS  What does total() return for an empty basket? Don't change anything.",
                 "oPASS  Which operating system is this computer running? Write just its name into os.txt.",
                 "u5/5 passed"], "term")
        + p("Run it after every change. A failing task tells you where to look.", 40),
        "It copies shop as it is, so put the bug back first. Five of five. This is the habit: change something, run the tasks.")
