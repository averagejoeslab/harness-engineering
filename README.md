# Harness Engineering in a Hurry

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

An **agent** is anything that loops over three steps: it observes, thinks, and acts, then does it again.

An agent built on a language model has two parts. The **model** is its mind, and it only thinks: tokens go in, and it predicts the next one, over and over, until it predicts it should stop. On its own it can't see anything, and it can't do anything with what it writes.

The **harness** is its body, and does everything else. **Harness engineering** is the practice of building it: turning a model that only predicts the next token into an agent that observes its environment and acts on it. A harness does that with five primitives, each serving part of the loop:

- **Input** observes: it captures what comes in, from a person or from the world.
- **Context** assembles what the model is shown each time: who it is, what it can do, and what it has observed so far.
- **Model interface** sends that to the model, and brings back what it thinks.
- **Output** acts: it carries out what the model decided, like running a command.
- **Control flow** repeats: it sends what happened back around, and decides whether to go again, hand back, or stop.

We'll build them one at a time, outward from the model, around one task: [`shop/`](./shop/) has a bug, and the request is *"The tests are failing. Find out why and fix it."*

You need [uv](https://docs.astral.sh/uv/) and an [Anthropic API key](https://console.anthropic.com/):

```bash
git clone https://github.com/averagejoeslab/harness-engineering
cd harness-engineering/shop
export ANTHROPIC_API_KEY=your-key
```

`git checkout .` puts the bug back whenever you need it.

## 1. Model interface

All we have is a model. The first primitive, the **model interface**, reaches it: `request_response()` sends a request and returns the model's response. Every later step talks to the model through it.

In [`1_model_interface.py`](./1_model_interface.py):

```python
# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

message = "The tests are failing. Find out why and fix it."   # the request, hardcoded
output = request_response(max_tokens=16384, messages=[{"role": "user", "content": message}])
print(output.model_dump_json(indent=2))
```

We send it the task, hardcoded, and print what comes back:

```bash
uv run ../1_model_interface.py
```

```
{
  "content": [
    …
    {
      "text": "I can't see your code or test output in this conversation, and I don't have tools to look at your repository, so I can't tell yet why the tests are failing. Could you share:\n\n1. **The failing test output**: the full error message and stack trace, copied as text.\n2. **The relevant code**: the function or module under test and the test file itself.\n3. **How you run the tests**: for example `pytest`, `npm test`, or `go test ./...`, plus the language and framework versions if you know them.\n4. **Recent changes**: anything you changed before the failures started, such as dependency upgrades, refactors, or config edits.\n5. **Scope**: whether all tests fail or only some, and whether they fail locally, in CI, or both.\n\nOnce I have the error output and the code involved, I can work out the root cause and suggest a specific fix.",
      "type": "text"
    }
  ],
  "stop_reason": "end_turn",
  …
}
```

(shortened)

The model answered, but it can't act, so it asks us to share the code. And the request is hardcoded, so nobody can ask anything else. We'll fix both by following the data's flow, starting where it begins: input.

## 2. Input

Next in the flow is **input**, which captures what comes in. `capture_input()` reads what you type into the terminal while the program runs, or takes a one-off request from the command line.

In [`2_input.py`](./2_input.py), `capture_input()` is added, and what it captures replaces the hardcoded message:

```python
# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: a one-off request on the command line, or what a person types
    if len(sys.argv) > 1: return " ".join(sys.argv[1:])
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line
message = capture_input()                                # input: the request, typed or from the command line

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": message}])
print(output.model_dump_json(indent=2))
```

We run it, and type the task at the `<` prompt:

```bash
uv run ../2_input.py
```

```
< The tests are failing. Find out why and fix it.
{
  "content": [
    …
    {
      "text": "I can't see your code or test output in this conversation, so I can't tell yet why the tests are failing. Could you share:\n\n1. **The failing test output**: the full error message and stack trace (copy-paste, not a screenshot if possible).\n2. **The relevant code**: the test file and the source file(s) it exercises.\n3. **How you run the tests**: e.g. `pytest`, `npm test`, `go test ./...`, `cargo test`.\n4. **Recent changes**: anything you changed before they started failing, such as dependency upgrades, refactors, or config changes.\n5. **Environment details** (if relevant): language/runtime version, OS, and whether the failure also happens in CI or only locally.\n\nIf you can paste the output of the test command, that's usually enough for me to find the cause. If the project is small, pasting the failing test and the function it covers will help me suggest a concrete fix.",
      "type": "text"
    }
  ],
  "stop_reason": "end_turn",
  …
}
```

(shortened)

Now anyone can ask, but the model can still only reply in words: it asks us to share the code, because it can't act. That's next in the flow: output.

## 3. Output

Next is **output**, which handles what the model sends back. We describe one tool, `shell`, so the model can ask to run a command. `handle_output()` runs each command it asks for, `show()` prints the model's words after `>`, and `nested()` puts what a command printed under it, after `└`.

In [`3_output.py`](./3_output.py), `tools`, `show()`, `nested()` and `handle_output()` are added:

```python
# ── output: the one tool ────────────────────────────────────────────────────
tools = [{"name": "shell", "description": "Run a shell command", "input_schema": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}]

def show(text):                                          # output: the model's words, after >
    print("> " + text.replace("\n", "\n  "))

def nested(result):                                      # output: what a command printed, nested under it with └
    return "  └ " + "\n    ".join(result.rstrip("\n").split("\n"))

def handle_output(output):                               # output: handles the model's outputs, running each command it asks for
    results = []
    for block in output:
        if block.type == "text": show(block.text)
        if block.type == "tool_use":
            print(f"$ {block.input['cmd']}")
            done = subprocess.run(block.input["cmd"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            result = done.stdout or f"(exit {done.returncode})"
            print(nested(result))
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})  # input: from the world
    return results

output = request_response(max_tokens=16384, tools=tools, messages=[{"role": "user", "content": message}]).content
results = handle_output(output)                          # what the commands printed: nothing sends it back yet
```

We run it, and type the task. Its commands run in `shop/`, on your machine, without asking. From here on, `<` is what you typed, `>` is what the model said, `$` is a command it ran, and `└` is what that command printed:

```bash
uv run ../3_output.py
```

```
< The tests are failing. Find out why and fix it.
$ pwd; ls; git status --short | head
  └ /home/user/harness-engineering/shop
    prices.py
    test_prices.py
```

It ran a command, but what the command printed goes nowhere. Nothing sends it back to the model, so it can't take the next step. Sending it back and going again is next: control flow.

## 4. Control flow

Next is **control flow**, which defines the shape of the loop. `control_flow()` sends back what the commands printed, and goes again until the model is done. Then it hands back to you for your next message, or stops if the request was a one-off from the command line. Ctrl-C stops it.

In [`4_control_flow.py`](./4_control_flow.py), `control_flow()` is added:

```python
# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    messages = [{"role": "user", "content": capture_input()}]
    while True:
        output = request_response(max_tokens=16384, tools=tools, messages=messages).content
        messages.append({"role": "assistant", "content": output})
        results = handle_output(output)
        if results:                                      # a command ran: send back what it printed, and go again
            messages.append({"role": "user", "content": results})
            continue
        if len(sys.argv) > 1: break                      # stop: a one-off request is done
        messages.append({"role": "user", "content": capture_input()})   # hand back: the person's next message

control_flow()
```

We run it and type the task:

```bash
uv run ../4_control_flow.py
```

````
< The tests are failing. Find out why and fix it.
$ ls; git status --short | head; (npm test || pytest || make test || cargo test || go test ./...) 2>&1 | tail -50
  └ …
$ sed -i 's/return round(subtotal - discount, 2)/return round(subtotal * (1 - discount \/ 100), 2)/' prices.py && python -m pytest -q 2>&1 | tail -3
  └ …
> The tests pass now: both of them, when I re-ran `pytest`.
  
  **Cause:** `total()` in `prices.py` subtracted `discount` as a flat amount, even though its docstring and the test treat it as a percentage. With `discount=10` on a 25 subtotal, it returned 15 (25 − 10) instead of 22.5.
<
````

(shortened)

It looked, found the bug, fixed it, and checked. **This is an agent:** it keeps going until the task is done, then hands back to you. But it doesn't know what it is, where it is, or how best to use its body. That's the last primitive: context.

## 5. Context

Last is **context**: what the model is shown on each call. It's the agent's working memory, and it's sent in roles. The **system prompt** is its mind: who it is, what drives it, when and where it was born, and how carefully to act. The **tool** is its body: the shell, and how to use it. The **messages** are the world: what you type and what each command printed, each stamped with the time so it always knows "now". When the messages grow too long, `compact()` summarizes the oldest part.

In [`harness.py`](./harness.py), `stamp()`, `system()`, `assemble_context()` and `compact()` are added, and the tool's description becomes its body. Here's how the pieces are put together:

```python
def stamp(text, start=None):                             # current inputs: when it came in, and how long it ran if it ran
    now = datetime.datetime.now()
    ran = f", ran {(now - start).total_seconds():.1f}s" if start else ""
    return f"[{now:%Y-%m-%d %H:%M:%S}{ran}] {text}"

def assemble_context(messages):                          # context: the mind as the system prompt, the body as the tool, the world as the messages
    return {"system": system(), "tools": tools, "messages": messages}

def compact(messages, drop):                             # current inputs: too long to send, so the older part is summarized
    turns = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    if drop > len(turns): sys.exit("[the conversation can't be summarized small enough]")
    keep = messages[turns[drop]:] if drop < len(turns) else [messages[turns[-1]]]
    summary = request_response(max_tokens=2048, system=system(), messages=keep + [{"role": "user", "content": "This conversation is too long to send. Summarize it into a gist that keeps what matters for carrying on."}])
    gist = next((b.text for b in summary.content if b.type == "text"), "")
    return [{"role": "user", "content": f"[the earlier conversation, summarized] {gist}"}]
```

We run it and ask who it is:

```bash
uv run ../harness.py
```

```
< Who are you, and where are you working?
$ pwd; whoami; hostname; uname -sr; ls -la | head -30
  └ /home/user/harness-engineering/shop
    root
    vm
    Linux 6.18.44-fc-v114
    total 16
    drwxr-xr-x 2 root root 4096 Oct 12 06:09 .
    drwxr-xr-x 6 root root 4096 Oct 12 03:44 ..
    -rw-r--r-- 1 root root  216 Oct 12 06:09 prices.py
    -rw-r--r-- 1 root root  322 Oct 11 03:54 test_prices.py
> I'm an AI agent that works for whoever messages me. I act through a single shell tool, and I check my work by reading results back instead of guessing. I run on the Claude model `claude-sonnet-5-5`, inside a small harness that sends your messages to the model, runs the commands it asks for, and returns the output.
  
  Where I'm working, as I just checked:
  - **Machine:** a Linux VM named `vm` (kernel 6.18.44), where I'm logged in as `root`.
  - **Directory:** `/home/user/harness-engineering/shop`. Every command I run starts here.
  - **Contents:** two files, `prices.py` and `test_prices.py`. I haven't opened either yet.
  - **Session start:** 2026-10-12 06:09.
  
  I'll read freely, but I'll go one step at a time and check each change as I make it. For anything I can't undo, I'll ask you first. What would you like me to do?
<
```

It knows what it is, and that its body is a shell, from what it's shown. The commands it ran only checked the machine and the folder.

That's all five primitives. [`harness.py`](./harness.py) is a complete harness: with a model inside, it's an agent that knows what it is, works through the shell, and keeps going until the task is done.
