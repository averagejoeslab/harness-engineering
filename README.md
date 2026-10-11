# Harness engineering

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

An agent has two parts: **a model** and **a harness**.

**Agent = Harness(Model)**

## The model

A model predicts. Tokens go in, it returns the most probable next token, and that token is added to the input. It repeats until it predicts `<eos>`, the end-of-sequence token.

```
            ┌──────────── append ◄────────────┐
            ▼                                 │
TokensIn ─► Model ─► most probable next token ─┤
                                               │
                                     is it <eos>? ── yes ─► TokensOut
```

**TokensOut = Model(TokensIn)**

That's all it does.

## The harness

The harness is everything else. It's been called a framework, a scaffold, a runtime and an orchestration layer, and the industry has mostly settled on *harness*.

Think of the model as an engine. On its own, it just turns. The harness is the rest of the vehicle: it's what makes the engine go somewhere.

Every harness does five things. These are its primitives:

| Primitive | What it does |
|---|---|
| **Input** | captures what comes in |
| **Context** | assembles the minimum the model needs to act well on this input |
| **Model interface** | requests a response from the model |
| **Output** | handles the response: shows it, or runs it as a tool |
| **Control flow** | decides what happens next: go again, hand back, or stop |

```
           ┌────────────────────────────── harness ───────────────────────────────┐
           │ ┌────────────────────────── control flow ──────────────────────────┐ │
           │ │                                                                  │ │
person ────┼─┼─► input ─► context ─► model interface ─► output ─────────────────┼─┼──► person
           │ │      ▲                   │      ▲            │                   │ │
           │ │      │                   ▼      │            ▼                   │ │
           │ │      │                 ┌──────────┐      runs a tool             │ │
           │ │      │                 │  model   │          │                   │ │
           │ │      │                 └──────────┘          │                   │ │
           │ │      └────────────────── a tool's result ◄───┘                   │ │
           │ │                                                                  │ │
           │ └──────────────────────────────────────────────────────────────────┘ │
           └──────────────────────────────────────────────────────────────────────┘
```

The model sits inside the harness. Everything around it is the harness: the person's words come in, get assembled into what the model is shown, go to the model, and what comes back is shown or run. Control flow wraps it all, deciding whether to go again.

## Building quark

A quark is one of the smallest particles there is. **quark** is the smallest agent: the five primitives and nothing more. We'll build it one primitive at a time.

Every step gets the same job. A small project, [`shop/`](./shop/), has a function, `total()` in `prices.py`, that adds up a basket and takes off a percentage discount, and a test that fails. The request is always: *"The tests are failing. Find out why and fix it."*

In the runs, `>` is what I typed, `<` is what quark said, and `$` is a command it ran.

### 1. Model interface

We have a model, and no way to reach it. So we request a response, in [`1_model_interface.py`](./1_model_interface.py):

```
           ┌──────────────────────────── harness ─────────────────────────────┐
           │                    model interface                               │
           │                        │      ▲                                  │
           │                        ▼      │                                  │
           │                      ┌──────────┐                                │
           │                      │  model   │                                │
           │                      └──────────┘                                │
           └──────────────────────────────────────────────────────────────────┘
```

```python
from anthropic import Anthropic

model = Anthropic()


def request_response(context):
    return model.messages.create(model="claude-sonnet-5-5", max_tokens=16384, **context)


response = request_response({"messages": [{"role": "user", "content": "The tests are failing. Find out why and fix it."}]})
print(response.model_dump_json(indent=2))
```

What comes back (shortened):

```
{
  "id": "msg_011CfnEtbEGGFJTpJ4xHGpD9",
  "content": [
    {
      "text": "I don't have access to your code, test files, or test output. Nothing came through in your message besides the request. ...",
      "type": "text"
    }
  ],
  "model": "claude-sonnet-5-5",
  "stop_reason": "end_turn",
  ...
}
```

Tokens in, tokens out. But the request is written into the code: nobody can ask it anything.

### 2. Input

So we capture what comes in, in [`2_input.py`](./2_input.py):

```
           ┌──────────────────────────── harness ─────────────────────────────┐
person ────┼─► input ─────────► model interface                               │
           │                        │      ▲                                  │
           │                        ▼      │                                  │
           │                      ┌──────────┐                                │
           │                      │  model   │                                │
           │                      └──────────┘                                │
           └──────────────────────────────────────────────────────────────────┘
```

```python
def capture_input():
    return input("\n> ")
```

and send that instead:

```python
response = request_response({"messages": [{"role": "user", "content": capture_input()}]})
```

Now you can type the request. The answer (shortened) is the same:

```
> The tests are failing. Find out why and fix it.
{
  ...
      "text": "I don't have the code or the test output yet, so I can't tell why the tests are failing. Could you share: ...",
  ...
}
```

It can only talk. It can't look at a file, and its answer is still raw.

### 3. Output

So we give it a tool, bash, and handle the response: show its words, run its commands. That's [`3_output.py`](./3_output.py):

```
           ┌──────────────────────────── harness ─────────────────────────────┐
person ────┼─► input ─────────► model interface ─► output ────────────────────┼──► person
           │                        │      ▲            │                     │
           │                        ▼      │            ▼                     │
           │                      ┌──────────┐      runs a tool               │
           │                      │  model   │          │                     │
           │                      └──────────┘          ▼                     │
           │                                    (its result goes nowhere)     │
           └──────────────────────────────────────────────────────────────────┘
```

```python
bash = {"name": "bash", "description": "Run a shell command",
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}
```

```python
def handle_output(response):
    tool_results = []
    for block in response.content:
        if block.type == "text":
            print("< " + block.text.replace("\n", "\n  "))
        if block.type == "tool_use":
            print(f"$ {block.input['command']}")
            ran = subprocess.run(block.input["command"], shell=True, capture_output=True, text=True)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": ran.stdout + ran.stderr or "(no output)"})
    return tool_results
```

```python
response = request_response({"tools": [bash], "messages": [{"role": "user", "content": capture_input()}]})
handle_output(response)
```

```
> The tests are failing. Find out why and fix it.
< I'll start by exploring the project and running the tests.
$ pwd; ls -la; git status 2>/dev/null | head
```

It acted, and then it stopped. The result of that command went nowhere, so the model never saw it.

### 4. Control flow

So we decide what happens next. If a tool ran, its result goes back and the model goes again. If not, it's your turn. That's [`4_control_flow.py`](./4_control_flow.py):

```
           ┌────────────────────────────── harness ───────────────────────────────┐
           │ ┌────────────────────────── control flow ──────────────────────────┐ │
           │ │                                                                  │ │
person ────┼─┼─► input ─────────► model interface ─► output ────────────────────┼─┼──► person
           │ │      ▲                 │      ▲            │                     │ │
           │ │      │                 ▼      │            ▼                     │ │
           │ │      │               ┌──────────┐      runs a tool               │ │
           │ │      │               │  model   │          │                     │ │
           │ │      │               └──────────┘          │                     │ │
           │ │      └──────────────── a tool's result ◄───┘                     │ │
           │ │                                                                  │ │
           │ └──────────────────────────────────────────────────────────────────┘ │
           └──────────────────────────────────────────────────────────────────────┘
```

```python
def control_flow():
    conversation = []
    while True:
        conversation.append({"role": "user", "content": capture_input()})
        while True:
            response = request_response({"tools": [bash], "messages": conversation})
            conversation.append({"role": "assistant", "content": response.content})
            tool_results = handle_output(response)
            if not tool_results:
                break                                    # done: hand back to the person
            conversation.append({"role": "user", "content": tool_results})   # a tool ran: go again
```

```
> The tests are failing. Find out why and fix it.
< Let me start by looking at the project and running the tests.
$ pwd; ls -la; git status 2>/dev/null | head
$ cat prices.py test_prices.py; python -m pytest -q 2>&1 | tail -30
$ python -m unittest -v 2>&1 | tail -20
< The docstring says the discount is a percentage, but the code subtracts it as a flat amount. So 25 − 10 = 15 instead of 25 × 0.9 = 22.5. I'll fix the code to match the documented behavior.
$ sed -i 's|return round(subtotal - discount, 2)|return round(subtotal * (1 - discount / 100), 2)|' prices.py && cat prices.py && python -m unittest 2>&1 | tail -5
< The tests pass now. The bug was in `prices.py`, not in the tests.
  ...

> Commit the fix.
$ git add prices.py && git commit -q -m "Fix total() to apply discount as a percentage ..." && git log --oneline -3 && git status --short
< I committed the fix as `d6beb65`, "Fix total() to apply discount as a percentage". Only `prices.py` is in the commit.
  ...
```

(shortened)

That's an agent: the inner loop goes until the job's done, and the outer loop hands back to you. "Commit the fix" needed no explaining, because the whole conversation goes back every time.

But it has to go looking for what it needs. Start it fresh and ask the simplest question:

```
> Who are you, and where are you working?
< I'll check the environment first so I can answer accurately.
$ echo "user: $(whoami)"; echo "host: $(hostname)"; echo "cwd: $(pwd)"; uname -a; ls -la | head -20
< I'm an AI assistant. I can run shell commands, and I use that to read files, run code and make changes in the environment I'm given.
  ...
```

(shortened)

### 5. Context

So we assemble the minimum it needs to act well on any input. For quark, that's who it is, where it's working and what day it is:

```
           ┌────────────────────────────── harness ───────────────────────────────┐
           │ ┌────────────────────────── control flow ──────────────────────────┐ │
           │ │                                                                  │ │
person ────┼─┼─► input ─► context ─► model interface ─► output ─────────────────┼─┼──► person
           │ │      ▲                   │      ▲            │                   │ │
           │ │      │                   ▼      │            ▼                   │ │
           │ │      │                 ┌──────────┐      runs a tool             │ │
           │ │      │                 │  model   │          │                   │ │
           │ │      │                 └──────────┘          │                   │ │
           │ │      └────────────────── a tool's result ◄───┘                   │ │
           │ │                                                                  │ │
           │ └──────────────────────────────────────────────────────────────────┘ │
           └──────────────────────────────────────────────────────────────────────┘
```

```python
def assemble_context(conversation):
    instructions = f"You are quark, an agent. You act through bash, in {os.getcwd()}. Today is {datetime.date.today()}."
    return {"system": instructions, "tools": [bash], "messages": conversation}
```

```python
            response = request_response(assemble_context(conversation))
```

```
> Who are you, and where are you working?
< I'm quark, an agent that works by running shell commands through bash. My working directory is /tmp/shop. Today's date is 2026-10-07.
  ...
```

(shortened)

No commands needed. Too little context and it wastes steps finding things out. Too much, and every request costs more and buries what matters.

That's all five primitives, and that's [`quark.py`](./quark.py):

```python
def capture_input():
    return input("\n> ")


def assemble_context(conversation):
    instructions = f"You are quark, an agent. You act through bash, in {os.getcwd()}. Today is {datetime.date.today()}."
    return {"system": instructions, "tools": [bash], "messages": conversation}


def request_response(context):
    return model.messages.create(model="claude-sonnet-5-5", max_tokens=16384, **context)


def handle_output(response):
    tool_results = []
    for block in response.content:
        if block.type == "text":
            print("< " + block.text.replace("\n", "\n  "))
        if block.type == "tool_use":
            print(f"$ {block.input['command']}")
            ran = subprocess.run(block.input["command"], shell=True, capture_output=True, text=True)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": ran.stdout + ran.stderr or "(no output)"})
    return tool_results


def control_flow():
    conversation = []
    while True:
        conversation.append({"role": "user", "content": capture_input()})
        while True:
            response = request_response(assemble_context(conversation))
            conversation.append({"role": "assistant", "content": response.content})
            tool_results = handle_output(response)
            if not tool_results:
                break                                    # done: hand back to the person
            conversation.append({"role": "user", "content": tool_results})   # a tool ran: go again
```

Each function is one primitive, and `control_flow()` holds the other four.

## Run it

You need [uv](https://docs.astral.sh/uv/) and an [Anthropic API key](https://console.anthropic.com/).

```bash
export ANTHROPIC_API_KEY=your-key
uv run quark.py               # or any step: uv run 1_model_interface.py
```

Ctrl-C quits.

> [!WARNING]
> quark runs the model's shell commands without asking. Run it somewhere you can afford to lose.

## From quark to production

quark works, but you wouldn't leave it running on its own. Six concerns stand in the way. Each asks one question of every primitive:

| Concern | The question |
|---|---|
| Persistence | what should outlast the session? |
| Safety | what could do harm? |
| Observability | what should we see? |
| Resilience | what could fail? |
| Performance | what's slow or costly? |
| Evaluation | what could a change break? |

Each concern below adds a few lines to `quark.py`. The result is [`quark_production.py`](./quark_production.py), and every line it adds is marked with the concern it answers.

### Persistence

When quark stops, everything goes with it: the task in progress, and anything you told it. Persistence comes first, because the other concerns depend on what outlasts a session. It gives quark memory, in four kinds:

| Memory | What it holds | Where |
|---|---|---|
| **Working** | the conversation, sent with every request | the context |
| **Episodic** | what happened: every message of every session | `.quark/episodes/`, one file per session |
| **Semantic** | what's true: facts, one per line | `.quark/memory/memory.md` |
| **Procedural** | how to do things: one skill per file | `.quark/skills/` |

**Control flow** writes every message to disk as it happens, so episodic memory is the harness's job, not the model's:

```python
def add(conversation, message):                          # persistence: one message, two places, in the request and on disk
    conversation.append(message)
    remember(message)
```

It also picks up a session that ended mid-task. A command that was running when it stopped may or may not have run, so quark is told to check:

```python
    if last["role"] == "assistant":                      # it stopped while commands were running
        add(conversation, {"role": "user", "content": [{"type": "tool_result", "tool_use_id": block["id"], "is_error": True,
            "content": "[interrupted: it may or may not have run. Check before repeating it.]"} for block in last["content"] if block["type"] == "tool_use"]})
```

**Context** tells quark what its memories are and how to use them, then shows it what it already knows: its facts, and an index of its skills.

```
You have four memories:
- Working memory: this conversation.
- Semantic memory: facts that stay true, one per line as "- subject: fact", in .quark/memory/memory.md. ...
- Procedural memory: skills, one file per method that worked, in .quark/skills/<name>.md. ...
- Episodic memory: every message of every session, one JSON object per line, in .quark/episodes/. ...

Before a task, check what you know: facts first, then skills, then past sessions.
```

quark writes facts and skills itself, with bash, the same way it does everything else. No new tools.

### Safety

Every command runs on your machine, without asking. Ask quark to delete a file, and it does.

**Output** runs commands in a box: a container that sees this folder and nothing else, with no network.

```python
def start_box():                                         # safety: a container that sees this folder and nothing else
    here = os.getcwd()
    subprocess.run(["docker", "run", "-d", "--rm", "--name", BOX, "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
                    "-e", "HOME=/tmp", "-v", f"{here}:{here}", "-w", here, "python:3.13", "sleep", "infinity"],
                   check=True, capture_output=True)
    atexit.register(subprocess.run, ["docker", "rm", "-f", BOX], capture_output=True)
```

**Control flow** runs nothing without a yes. `handle_output` runs a command only if `allowed` says so, and a no goes back to quark as the result:

```python
def allowed(command):                                    # safety: nothing runs without a yes
    return input("  run this? [y/N] ").strip().lower() == "y"
```

**Input** stays open: text quark reads can carry instructions of its own, and no harness fully stops a model from following them. The box and the question limit the damage.

*Persistence still holds:* the box sees this folder, and `.quark/` is in it, so quark can still read and write its memory.

### Observability

After a run, all you have is what scrolled past. So each request and each command writes one line to a record, kept outside the box where quark can't change it:

```python
def record(**step):                                      # observability: one line per step, outside the box
    os.makedirs(os.path.dirname(RECORD), exist_ok=True)
    with open(RECORD, "a") as log:
        log.write(json.dumps({"time": datetime.datetime.now().isoformat(timespec="seconds"), **step}) + "\n")
```

**Model interface** records the tokens each request used. **Output** records each command and how it ended, or that you said no.

*Persistence is different:* episodes are what quark remembers, inside its folder. The record is what you see, in `~/.quark/record.jsonl`.

### Resilience

A request can fail, and a command can hang forever. **Model interface** retries a failed request three times:

```python
model = Anthropic(max_retries=3)                         # resilience: retry a request that fails
```

**Output** stops a command after a minute, and says so:

```python
                ran = subprocess.run(["docker", "exec", BOX, "timeout", "60", "sh", "-c", command], capture_output=True, text=True)
                result = ran.stdout + ran.stderr or "(no output)"
                if ran.returncode == 124:
                    result += "\n[stopped: it ran for over a minute]"
```

And if quark itself crashes, persistence already has the session on disk: the next start offers to continue it.

### Performance

Every request sends the whole conversation again, at full price. **Context** asks for it to be cached, so each request pays full price only for what's new:

```python
    return {"system": instructions, "tools": [bash], "messages": conversation,
            "cache_control": {"type": "ephemeral"}}      # performance: reuse what was already sent
```

Cached tokens cost about a tenth. The record's `cached` field shows how much each request reused.

*Persistence costs a little here:* facts are part of the instructions, so when quark writes a new one, the next request pays full price once.

### Evaluation

Any change can change what quark does: a word in the instructions, a new model, a new tool. So run it on a task with a known right answer, and check the result, not what it says.

**Input** takes a request from the command line, and **control flow** runs it once and stops. [`eval.sh`](./eval.sh) gives quark a bug to fix in a fresh copy of [`shop/`](./shop/), where `total()` takes the discount off as an amount instead of a percentage:

```sh
#!/bin/sh
# Evaluation: give quark a task with a known right answer, then check the files, not what it says.
here=$(pwd)
cd "$(mktemp -d)" && cp "$here"/shop/*.py . && git init -q && git add . && git -c user.name=eval -c user.email=eval@example.com commit -qm start
yes | uv run -q "$here/quark_production.py" "The tests are failing. Find out why and fix it." > /dev/null
python3 -m unittest -q 2>/dev/null && git diff --quiet HEAD -- test_prices.py && echo "PASS: the tests pass, and the test file is unchanged" || echo "FAIL"
```

Each run is a fresh folder, so no memory carries over between runs, and a request from the command line never offers to continue an old session. Run it after every change.

### Run it

`quark_production.py` also needs [Docker](https://docs.docker.com/get-docker/) running.

```bash
uv run quark_production.py    # quark, with the six concerns
./eval.sh                     # check it still works
```

Claude Code, Cursor and every other agent are these same five primitives, hardened in these ways.
