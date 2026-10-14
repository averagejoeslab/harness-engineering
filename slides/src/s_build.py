from lib import *

section("building a harness")
divider("d-build", "Part 3", "Building a harness",
        "We build outward from the model, one primitive at a time, on one small task.",
        "Now we build. Every version gets the same task, and we watch how far it gets and what stops it.")

steps = [("1", "Reach the model", "model interface"), ("2", "Let someone ask", "input"), ("3", "Let it act", "output"),
         ("4", "Let it keep going", "control flow"), ("5", "Give it context", "context")]
cards = "".join(
    f'<div style="flex:1;display:flex;flex-direction:column;gap:12px;background:{CARD};border:1px solid {LINE};border-radius:16px;padding:28px">'
    f'<p style="font-family:{MONO};font-size:24px;color:{AMBER_INK}">step {n}</p>'
    f'<h3 style="font-size:40px;font-weight:600;line-height:1.2">{t}</h3>'
    f'<p style="font-size:32px;color:{MUTED}">{prim}</p></div>' for n, t, prim in steps)
content("build-outward", "The plan", "Build outward from the model",
        row(cards, gap=20)
        + p("We use Claude Sonnet through Anthropic's Python SDK. Pick the model for the work first; then shape the body around the mind inside it.", 32, MUTED),
        "First reach the model, then let someone ask it something, let it act, let it keep going, and finally tell it what it is. The order follows the data's flow outward from the model.")

content("setup", "Setup", "One repo, one task",
        panel(["git clone https://github.com/averagejoeslab/harness-engineering",
               "cd harness-engineering/shop",
               "export ANTHROPIC_API_KEY=your-key"])
        + row(card("The task", "`shop/` is a tiny project with a bug: `total()` in `prices.py` should take a percentage discount off a basket, and its test fails."),
              card("The request, every time", "“The tests are failing. Find out why and fix it.” `git checkout .` puts the bug back."), gap=32),
        "You need uv, an Anthropic API key, and Docker for the production part. Every command runs from shop. The agent changes the task's files as we go, so git checkout dot resets it. Keep your key in your environment, never in a file you commit.")

# ── Step 1 ──
section("step 1 · reach the model")
content("s1-what", "Step 1 · Model interface", "Reach the model",
        progress(1)
        + p("All we have is a model. The **model interface** reaches it: `request_response()` sends a request and returns the model's response.", 40)
        + p("Every later step talks to the model through it. To use another provider or format, change only this primitive.", 32, MUTED),
        "The first primitive. It's tiny, and that's the point: one function every other part goes through.")

content("s1-code", "Step 1 · 1_model_interface.py", "One function to reach the model",
        panel(["# /// script",
               "# dependencies = [\"anthropic\"]",
               "# ///",
               "from anthropic import Anthropic",
               "",
               "client = Anthropic()",
               "MODEL = \"claude-sonnet-5-5\"",
               "def request_response(**request):  # model interface: requests a response from the model",
               "    return client.messages.create(model=MODEL, **request)",
               "",
               "message = \"The tests are failing. Find out why and fix it.\"  # the request, hardcoded",
               "output = request_response(max_tokens=16384, messages=[{\"role\": \"user\", \"content\": message}])",
               "print(output.model_dump_json(indent=2))"]),
        "The header declares dependencies inline, so uv run installs them. request_response passes everything through to the Messages API. The request itself is hardcoded for now.")

content("s1-run", "Step 1 · the run", "It answers, but it can't act",
        pill("uv run ../1_model_interface.py")
        + panel(["n{",
                 "n  \"content\": [",
                 "n    { \"type\": \"thinking\", \"thinking\": \"\", \"signature\": \"CAQS7gUK…\" },",
                 "n    { \"type\": \"text\",",
                 "m      \"text\": \"I can't see your code or test output in this conversation, and I don't have",
                 "m               tools to look at your repository, so I can't tell yet why the tests are failing.",
                 "m               Could you share: 1. The failing test output …\" }",
                 "n  ],",
                 "n  \"stop_reason\": \"end_turn\",",
                 "n  \"usage\": { \"input_tokens\": 24, \"output_tokens\": 313 }",
                 "n}"], "term"),
        "The response, trimmed. It's a reasonable answer: it asks us to share the code, because it can't look for itself. Note input tokens: 24. It's seen nothing but our sentence.")

missing("s1-missing", "Step 1 · still missing", "It can only talk, and nobody can ask it anything else.",
        "Step 2 · Let someone ask: `input`",
        "Two gaps: the request is hardcoded, and the model can't act. We follow the data's flow and start where it begins: input.")

# ── Step 2 ──
section("step 2 · let someone ask")
content("s2-what", "Step 2 · Input", "Let someone ask",
        progress(2)
        + p("**Input** captures what comes in. `capture_input()` takes a one-off request from the command line, or what a person types at the `<` prompt.", 40)
        + p("Later, input also carries what the world sends back: the result of an action.", 32, MUTED),
        "Input is how the outside reaches the agent. Right now that's a person; soon it will also be the results of its own actions.")

content("s2-code", "Step 2 · 2_input.py", "Capture what comes in",
        panel(["def capture_input():  # input: a one-off request on the command line, or what a person types",
               "    if len(sys.argv) > 1: return \" \".join(sys.argv[1:])",
               "    line = \"\"",
               "    while not line.strip(): line = input(\"< \")  # Enter on an empty line: ask again",
               "    return line",
               "message = capture_input()  # input: the request, typed or from the command line",
               "",
               "output = request_response(max_tokens=16384, messages=[{\"role\": \"user\", \"content\": message}])",
               "print(output.model_dump_json(indent=2))"]),
        "Two ways in: arguments on the command line for one-off requests and scripts, or a prompt for a person. The rest is unchanged from step 1.")

content("s2-run", "Step 2 · the run", "Anyone can ask now",
        pill("uv run ../2_input.py")
        + panel(["u< The tests are failing. Find out why and fix it.",
                 "n{",
                 "n  \"content\": [",
                 "n    { \"type\": \"thinking\", \"thinking\": \"\", \"signature\": \"CAQSiAYK…\" },",
                 "n    { \"type\": \"text\",",
                 "m      \"text\": \"I can't see your code or test output in this conversation, so I can't tell",
                 "m               yet why the tests are failing. Could you share: 1. The failing test output …\" }",
                 "n  ],",
                 "n  \"usage\": { \"input_tokens\": 24, \"output_tokens\": 350 }",
                 "n}"], "term"),
        "We type the task at the prompt. Same kind of answer: it still asks us to share the code.")

missing("s2-missing", "Step 2 · still missing", "Anyone can ask. But it still only replies in words.",
        "Step 3 · Let it act: `output`",
        "It asks us for the code because it can't look. Next in the flow is output: let it act.")

# ── Step 3 ──
section("step 3 · let it act")
content("s3-what", "Step 3 · Output", "Let it act",
        progress(3)
        + p("**Output** handles the model's outputs. Besides text, the model can answer with a `tool_use` block: a request to run a tool. We give it one tool, a shell.", 32)
        + panel(['{"type": "tool_use", "id": "toolu_…", "name": "shell", "input": {"cmd": "ls"}}'])
        + p("From here on: `<` what you typed · `>` what the model said · `$` a command it ran · `└` what it printed", 32, MUTED),
        "Why one shell? On my wager that through the shell all things are possible: files, programs, the network, even the desktop. From here on the terminal uses four marks.")

content("s3-code", "Step 3 · 3_output.py", "Run each command it asks for",
        panel(["tools = [{\"name\": \"shell\", \"description\": \"Run a shell command\", \"input_schema\": {\"type\": \"object\",",
               "          \"properties\": {\"cmd\": {\"type\": \"string\"}}, \"required\": [\"cmd\"]}}]",
               "",
               "def handle_output(output):  # output: handles the model's outputs, running each command it asks for",
               "    results = []",
               "    for block in output:",
               "        if block.type == \"text\": show(block.text)",
               "        if block.type == \"tool_use\":",
               "            print(f\"$ {block.input['cmd']}\")",
               "            done = subprocess.run(block.input[\"cmd\"], shell=True, stdout=subprocess.PIPE,",
               "                                  stderr=subprocess.STDOUT, text=True, errors=\"replace\")",
               "            result = done.stdout or f\"(exit {done.returncode})\"",
               "            print(nested(result))",
               "            results.append({\"type\": \"tool_result\", \"tool_use_id\": block.id, \"content\": result})",
               "    return results"]),
        "One tool, described by a JSON schema with one field: cmd. handle_output prints text after the > mark, runs each command, prints what it printed, and collects a tool_result for each. show and nested only format the screen.")

content("s3-run", "Step 3 · the run", "It acts, once",
        pill("uv run ../3_output.py")
        + panel(["u< The tests are failing. Find out why and fix it.",
                 "c$ pwd; ls; git status --short | head",
                 "o  └ /home/user/harness-engineering/shop",
                 "o    prices.py",
                 "o    test_prices.py"], "term")
        + p("It went straight to a command. Its commands run in `shop/`, on your machine, without asking: remember that for production.", 32, MUTED),
        "It looked around. But the results went nowhere: nothing sends them back to the model. And note it ran on our machine without asking. We'll come back to that in safety and security.")

missing("s3-missing", "Step 3 · still missing", "It acted once. What the command printed never reached the model.",
        "Step 4 · Let it keep going: `control flow`",
        "What the command printed is new input, from the world, and nothing sends it back. So it can't take the next step.")

# ── Step 4 ──
section("step 4 · let it keep going")
content("s4-what", "Step 4 · Control flow", "Let it keep going",
        progress(4)
        + p("**Control flow** defines the shape of the loop. `control_flow()` decides what happens after each response:", 32)
        + row(card("Go again", "A command ran: send back what it printed, and call the model again."),
              card("Hand back", "The model is done: your turn to type the next message."),
              card("Stop", "A one-off request from the command line is done. Ctrl-C stops it too."), gap=24),
        "Three shapes: go again, hand back, stop. The inner loop runs the model and its tools until it's done; the outer loop hands back to the person.")

content("s4-code", "Step 4 · 4_control_flow.py", "Send results back, and go again",
        panel(["def control_flow():  # control flow: defines the shape of the loop",
               "    messages = [{\"role\": \"user\", \"content\": capture_input()}]",
               "    while True:",
               "        output = request_response(max_tokens=16384, tools=tools, messages=messages).content",
               "        messages.append({\"role\": \"assistant\", \"content\": output})",
               "        results = handle_output(output)",
               "        if results:  # a command ran: send back what it printed, and go again",
               "            messages.append({\"role\": \"user\", \"content\": results})",
               "            continue",
               "        if len(sys.argv) > 1: break  # stop: a one-off request is done",
               "        messages.append({\"role\": \"user\", \"content\": capture_input()})  # hand back: the next message",
               "",
               "control_flow()"]),
        "The messages list is the conversation. Results go back in a user turn, the world's turn. If nothing ran, the model is done: stop or hand back.")

content("s4-run", "Step 4 · the run", "It finds the bug, fixes it, and checks",
        pill("uv run ../4_control_flow.py")
        + panel(["u< The tests are failing. Find out why and fix it.",
                 "c$ ls; git status --short | head; (npm test || pytest || make test || cargo test || go test ./...) 2>&1 | tail -50",
                 "o  └ …  test_prices.py .F  …  E       AssertionError: 15 != 22.5",
                 "c$ cat prices.py test_prices.py",
                 "o  └ def total(items, discount=0):",
                 "o        return round(subtotal - discount, 2)  …",
                 "m> The docstring says the discount is a percentage, but the code subtracts it as a flat amount.",
                 "c$ sed -i 's/return round(subtotal - discount, 2)/return round(subtotal * (1 - discount \\/ 100), 2)/' …",
                 "c$ pytest -q 2>&1 | tail -3; cat prices.py",
                 "o  └ 2 passed in 0.01s",
                 "m> The tests pass now: both of them, when I re-ran `pytest`."], "term")
        + p("**This is an agent:** it keeps going until the task is finished, then hands back to you.", 32),
        "Trimmed, but real. It tried every test runner at once, read the code, spotted the flat discount, fixed it, and re-ran the tests. One run in between failed because pytest wasn't in its Python; it recovered on its own. This is the moment: it's an agent now.")

missing("s4-missing", "Step 4 · still missing", "Ask who it is, and it has to go looking.",
        "Step 5 · Give it context: `context`",
        "It doesn't know what it is, what its body is, or how best to use it. Watch: it runs four commands to answer a question about itself.",
        panel(["u< Who are you, and where are you working?",
               "c$ pwd", "c$ whoami", "c$ hostname", "c$ uname -a",
               "m> I'm an AI assistant. I can run shell commands on your behalf, and I just used that",
               "m  to look at the environment."], "term", extra="width:1500px"))
