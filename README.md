# Harness Engineering in a Hurry

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

An agent loops: it **observes**, **thinks**, and **acts**, then does it again. It has two parts. The **model** is its mind: tokens go in, and it predicts what comes next. The **harness** is its body: it gets the model its input, carries out what the model says, and keeps the loop going.

Harness engineering is building that body. A harness has five primitives:

| Primitive | What it does |
|---|---|
| **Model interface** | sends a request to the model and returns its response |
| **Input** | captures what comes in |
| **Output** | handles what the model sends back |
| **Control flow** | defines the shape of the loop |
| **Context** | assembles what the model is shown |

We'll build them one at a time, on one task: [`shop/`](./shop/) has a bug, and the request is *"The tests are failing. Find out why and fix it."*

You need [uv](https://docs.astral.sh/uv/) and an [Anthropic API key](https://console.anthropic.com/):

```bash
git clone https://github.com/averagejoeslab/harness-engineering
cd harness-engineering/shop
export ANTHROPIC_API_KEY=your-key
```

`git checkout .` puts the bug back whenever you need it.

## 1. Model interface

`request_response()` sends a request to the model and returns its response. In [`1_model_interface.py`](./1_model_interface.py):

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

```bash
uv run ../1_model_interface.py
```

The model answers in words, asking us to share the code: it can't see or do anything. And the request is hardcoded.

## 2. Input

`capture_input()` reads what you type. In [`2_input.py`](./2_input.py):

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

```bash
uv run ../2_input.py
```

Now you can ask anything, but it still can only reply in words.

## 3. Output

We give the model one tool, a shell. `handle_output()` runs each command it asks for and prints the result. In [`3_output.py`](./3_output.py):

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

It ran a command, but what it printed never goes back to the model.

## 4. Control flow

`control_flow()` sends each command's result back and goes again, until the model is done. Then it hands back to you. In [`4_control_flow.py`](./4_control_flow.py):

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

```bash
uv run ../4_control_flow.py
```

```
< The tests are failing. Find out why and fix it.
$ ls; git status --short | head; (npm test || pytest || make test || cargo test || go test ./...) 2>&1 | tail -50
  └ …
$ sed -i 's/return round(subtotal - discount, 2)/return round(subtotal * (1 - discount \/ 100), 2)/' prices.py && python -m pytest -q 2>&1 | tail -3
  └ …
> The tests pass now: both of them, when I re-ran `pytest`.
  
  **Cause:** `total()` in `prices.py` subtracted `discount` as a flat amount, even though its docstring and the test treat it as a percentage. With `discount=10` on a 25 subtotal, it returned 15 (25 − 10) instead of 22.5.
<
```

(shortened)

It found the bug and fixed it. **This is an agent.** But it doesn't know what it is, or where.

## 5. Context

`assemble_context()` decides what the model is shown each call: the **system prompt** is its mind (who it is, when and where it was born, how to behave), the **tool** is its body (the shell, and how to use it), and the **messages** are the world, each stamped with the time. In [`harness.py`](./harness.py):

```python
def stamp(text, start=None):                             # current inputs: when it came in, and how long it ran if it ran
    now = datetime.datetime.now()
    ran = f", ran {(now - start).total_seconds():.1f}s" if start else ""
    return f"[{now:%Y-%m-%d %H:%M:%S}{ran}] {text}"

def assemble_context(messages):                          # context: the mind as the system prompt, the body as the tool, the world as the messages
    return {"system": system(), "tools": tools, "messages": messages}
```

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

That's all five primitives. [`harness.py`](./harness.py) is a complete harness: a model inside it is an agent that knows what it is and keeps going until the job is done.
