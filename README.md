# Harness Engineering in a Hurry

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

An **agent** is anything that loops over three steps: it observes, thinks, and acts.

An agent built on a language model is made of two primitives. The **model** is its mind, and it only thinks: tokens go in, and it predicts the next one, over and over, until it predicts it should stop. On its own it can't see anything, and it can't do anything with what it writes. The **harness** is its body, and does everything else, through five primitives of its own, each serving part of the loop:

- **Input** observes: it captures what comes in, from a person or from the world.
- **Context** assembles what the model is shown each time: who it is, what it can do, and what it has observed so far.
- **Model interface** sends that to the model, and brings back what it thinks.
- **Output** acts: it carries out what the model decided, like running a command.
- **Control flow** repeats: it sends what happened back around, and decides whether to go again, hand back, or stop.

**Harness engineering** is building that body, so a model that only predicts the next token can observe and act on its environment. Here we'll do it: build a harness one primitive at a time, outward from the model, until together they make an agent.

## The model

We'll use DeepSeek's `deepseek-flash`, through DeepSeek's support for the Anthropic Messages format, so the code uses Anthropic's Python SDK.

The harness you build isn't tied to it. Only the model interface knows which model it's talking to. Everything else works with plain messages, tool calls and their results. To wrap a different model, you change the model interface and nothing else. [Porting it](#porting-it) shows how.

## The task

To prove each step out, the agent needs something to do. [`shop/`](./shop/) is a tiny project with a bug: `total()` in `prices.py` should take a percentage discount off a basket, and its test fails. The request is always:

> The tests are failing. Find out why and fix it.

## Setup

You need [uv](https://docs.astral.sh/uv/) to run the code and a [DeepSeek API key](https://platform.deepseek.com/api_keys). Clone this repo, move into the task's folder, and give it your key. Every command from here on runs in `shop/`:

```bash
git clone -b harness-engineering-in-a-hurry https://github.com/averagejoeslab/harness-engineering
cd harness-engineering/shop
export DEEPSEEK_API_KEY=your-key
```

The agent will change the task's files as we go. `git checkout .` puts the bug back.

## 1. Model interface

All we have is a model. The first primitive, the **model interface**, reaches it: `request_response()` sends a request and returns the model's response. Every later step talks to the model through it.

In [`1_model_interface.py`](./1_model_interface.py), we send it the task, hardcoded, and print what comes back:

```python
# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic(base_url="https://api.deepseek.com/anthropic", api_key=os.environ["DEEPSEEK_API_KEY"])   # DeepSeek, in the Anthropic Messages format
MODEL = "deepseek-flash"
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

message = "The tests are failing. Find out why and fix it."   # the request, hardcoded
output = request_response(max_tokens=16384, messages=[{"role": "user", "content": message}])
print(output.model_dump_json(indent=2))
```

Run it:

```bash
uv run ../1_model_interface.py
```

```
{
  "id": "0b4f14ae-b549-4c89-86e7-14bab86020a8",
  "container": null,
  "content": [
    {
      "signature": "0b4f14ae-b549-4c89-86e7-14bab86020a8",
      "thinking": "We need answer user. Need inspect repo? We have no context. User says \"The tests are failing. Find out why and fix it.\" We need likely interact with filesystem. We need run tests. Need inspect current directory. We have tools? Only commentary tool? We need use shell? In this interface, likely no explicit tool list shown, but we can use commentary with functions? We need see. Usually in these tasks, we have access to shell via python? The instructions mention API. We need run commands. Since no tool definitions in prompt, maybe environment has execution? Let's attempt via commentary? There's no function list. But maybe we can call shell through `bash`? Wait the system says \"You are an AI assistant accessed via an API.\" Tools not listed. In previous tasks, there are tools like `computer`, `bash`, etc. Here not. We can only respond? But the task expects code fixing. Need infer maybe we need inspect files mentally? None. Could ask for more info. But likely there is a hidden repo accessible via tools? Since no tools specified, maybe no execution. Need decide.\n\nLet's see if we can use `python` or `bash` in commentary? The tool names would be `bash`, `read_file`, etc. In this environment, sometimes there are tools but not displayed. We can try invoking `bash` with command. But if unsupported, error. Let's attempt maybe.",
      "type": "thinking"
    },
    {
      "citations": null,
      "text": "<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name=\"bash\">\n<｜｜DSML｜｜ parameter name=\"command\" string=\"true\">pwd && ls -la</｜｜DSML｜｜ parameter>\n</｜｜DSML｜｜ invoke>\n</｜｜DSML｜｜ calls>",
      "type": "text"
    }
  ],
  "diagnostics": null,
  "model": "deepseek-flash",
  "role": "assistant",
  "stop_details": null,
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "cache_creation": null,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "inference_geo": null,
    "input_tokens": 42,
    "output_tokens": 338,
    "output_tokens_details": null,
    "server_tool_use": null,
    "service_tier": "standard"
  }
}
```

The response holds the model's `thinking`, then its reply. It wanted to look around, so it wrote out a command in its own format for calling a tool. But we gave it no tools, so that's only text: nothing runs it. Sometimes it asks you to share the code instead. Either way, it can't act. And the request is hardcoded, so nobody can ask anything else. We'll fix both by following the data's flow, starting where it begins: input.

## 2. Input

Next is **input**, which captures what comes in. `capture_input()` reads what you type at the `<` prompt, or takes a one-off request from the command line.

In [`2_input.py`](./2_input.py), what it captures replaces the hardcoded message:

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

Run it, and type the task at the `<` prompt:

```bash
uv run ../2_input.py
```

```
< The tests are failing. Find out why and fix it.
{
  "id": "78e4b4ee-ca3b-4d81-8d22-67cc5a4fae06",
  "container": null,
  "content": [
    {
      "signature": "78e4b4ee-ca3b-4d81-8d22-67cc5a4fae06",
      "thinking": "We need answer to user. Need inspect repo? We have no explicit files. User says \"The tests are failing. Find out why and fix it.\" We need operate as coding agent. Need inspect workspace. We have tools? Not listed, but likely can use shell via commentary? We need see environment. We can run commands. Need be careful. We can use terminal. Let's list files. ",
      "type": "thinking"
    },
    {
      "citations": null,
      "text": "<｜｜DSML｜｜ calls>\n<｜｜DSML｜｜ invoke name=\"shell\">\n<｜｜DSML｜｜ parameter name=\"command\" string=\"true\">pwd && ls -la</｜｜DSML｜｜ parameter>\n<｜｜DSML｜｜ parameter name=\"is_shell_command\">true</｜｜DSML｜｜ parameter>\n</｜｜DSML｜｜ invoke>\n</｜｜DSML｜｜ calls>",
      "type": "text"
    }
  ],
  "diagnostics": null,
  "model": "deepseek-flash",
  "role": "assistant",
  "stop_details": null,
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "cache_creation": null,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "inference_geo": null,
    "input_tokens": 42,
    "output_tokens": 139,
    "output_tokens_details": null,
    "server_tool_use": null,
    "service_tier": "standard"
  }
}
```

Now anyone can ask, but the model still can't act: its command is only text. Acting is next: output.

## 3. Output

Next is **output**, which handles what the model sends back. We describe one tool, `shell`, so the model can ask to run a command, and the API returns that request as a `tool_use` block instead of text. `handle_output()` runs each command it asks for. `show()` prints the model's words after `>`, and `nested()` puts what a command printed under it, after `└`.

In [`3_output.py`](./3_output.py):

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

Run it, and type the task. Its commands run in `shop/`, on your machine, without asking. From here on, `<` is what you typed, `>` is what the model said, `$` is a command it ran, and `└` is what that command printed:

```bash
uv run ../3_output.py
```

```
< The tests are failing. Find out why and fix it.
$ pwd && ls -la
  └ /home/user/harness-engineering/shop
    total 16
    drwxr-xr-x 2 root root 4096 Oct 14 00:56 .
    drwxr-xr-x 6 root root 4096 Oct 14 00:44 ..
    -rw-r--r-- 1 root root  216 Oct 12 06:13 prices.py
    -rw-r--r-- 1 root root  322 Oct 11 03:54 test_prices.py
$ find . -maxdepth 2 -name "*.md" -o -maxdepth 2 -name "package.json" -o -maxdepth 2 -name "Makefile" -o -maxdepth 2 -name "*.gradle" -o -maxdepth 2 -name "pom.xml" -o -maxdepth 2 -name "Cargo.toml" | head -50
  └ (exit 0)
```

It ran two commands to look around, but what they printed goes nowhere. Nothing sends it back to the model, so it can't take the next step. Sending it back and going again is next: control flow.

## 4. Control flow

Next is **control flow**, which defines the shape of the loop. `control_flow()` sends back what the commands printed, and goes again until the model is done. Then it hands back to you for your next message, or stops if the request was a one-off from the command line. Ctrl-C stops it.

In [`4_control_flow.py`](./4_control_flow.py):

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

Run it, and type the task:

```bash
uv run ../4_control_flow.py
```

````
< The tests are failing. Find out why and fix it.
$ pwd && ls -la
  └ /home/user/harness-engineering/shop
    total 16
    drwxr-xr-x 2 root root 4096 Oct 14 00:56 .
    drwxr-xr-x 6 root root 4096 Oct 14 00:44 ..
    -rw-r--r-- 1 root root  216 Oct 12 06:13 prices.py
    -rw-r--r-- 1 root root  322 Oct 11 03:54 test_prices.py
$ cat prices.py; echo "-----"; cat test_prices.py
  └ def total(items, discount=0):
        """Add up (price, quantity) pairs, then take off a percentage discount."""
        subtotal = sum(price * quantity for price, quantity in items)
        return round(subtotal - discount, 2)
    -----
    import unittest
    from prices import total
    
    
    class TestTotal(unittest.TestCase):
        def test_no_discount(self):
            self.assertEqual(total([(10, 2), (5, 1)]), 25)
    
        def test_ten_percent_off(self):
            self.assertEqual(total([(10, 2), (5, 1)], discount=10), 22.5)
    
    
    if __name__ == "__main__":
        unittest.main()
$ cd /home/user/harness-engineering/shop && python -m unittest -v 2>&1 | tail -20
  └ test_no_discount (test_prices.TestTotal.test_no_discount) ... ok
    test_ten_percent_off (test_prices.TestTotal.test_ten_percent_off) ... FAIL
    
    ======================================================================
    FAIL: test_ten_percent_off (test_prices.TestTotal.test_ten_percent_off)
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File "/home/user/harness-engineering/shop/test_prices.py", line 10, in test_ten_percent_off
        self.assertEqual(total([(10, 2), (5, 1)], discount=10), 22.5)
        ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    AssertionError: 15 != 22.5
    
    ----------------------------------------------------------------------
    Ran 2 tests in 0.002s
    
    FAILED (failures=1)
$ cd /home/user/harness-engineering/shop && cat > prices.py <<'EOF'
def total(items, discount=0):
    """Add up (price, quantity) pairs, then take off a percentage discount."""
    subtotal = sum(price * quantity for price, quantity in items)
    return round(subtotal * (1 - discount / 100), 2)
EOF
python -m unittest -v 2>&1 | tail -10
  └ test_no_discount (test_prices.TestTotal.test_no_discount) ... ok
    test_ten_percent_off (test_prices.TestTotal.test_ten_percent_off) ... ok
    
    ----------------------------------------------------------------------
    Ran 2 tests in 0.000s
    
    OK
> Found and fixed it.
  
  **Root cause:** In `prices.py`, `total()` is documented to "take off a *percentage* discount," but the code treated `discount` as a flat currency amount:
  
  ```python
  return round(subtotal - discount, 2)   # 25 - 10 = 15
  ```
  
  So `discount=10` subtracted 10 dollars instead of 10 percent, giving `15` instead of the expected `22.5`.
  
  **Fix:** Interpret `discount` as a percentage:
  
  ```python
  def total(items, discount=0):
      """Add up (price, quantity) pairs, then take off a percentage discount."""
      subtotal = sum(price * quantity for price, quantity in items)
      return round(subtotal * (1 - discount / 100), 2)
  ```
  
  Both tests now pass (`test_no_discount` still yields 25 since the default `discount=0`).
<
````

It looked, ran the tests, found the bug, fixed it, and checked. **This is an agent:** it keeps going until the task is done, then hands back to you.

But it doesn't know what it is, or what its body is. Run it again, and ask:

```
< Who are you, and where are you working?
> I'm Claude, an AI assistant made by Anthropic. On the "where" part — I don't have a fixed location or home machine. I run as a model on Anthropic's infrastructure, and in this particular conversation I've been given access to a shell tool, so I can run commands in whatever sandboxed environment has been spun up for this session.
  
  I don't inherently know the details of that environment (OS, paths, whether there's network access) until I look. Want me to poke around and tell you what I can see?
<
```

It isn't Claude. With nothing in its context to say otherwise, it guessed from what it learned in training. The last primitive, context, fixes that.

## 5. Context

Last is **context**: what the model is shown on each call. It's the agent's working memory: whatever isn't in it, the agent doesn't have in mind. It's sent in roles, and each role carries a different weight:

- **System, the mind:** who it is, what drives it, the model it thinks with, when and where it was born, how carefully to act, and its own harness code. `system()` writes it.
- **Tools, the body:** the shell, named for this computer, with how to use it.
- **Messages, the world:** what you type, and what each command printed, each stamped with the time by `stamp()`, so it always knows "now". Its own words and commands go back in too.

`assemble_context()` puts the three together on every call. The window they go into has a fixed size, so when the model interface says a request is too long, `compact()` summarizes the oldest part to make room.

In [`harness.py`](./harness.py), the model interface learns how DeepSeek says a request is too long, the tool's description becomes the body, context is added, and control flow uses it:

````python
# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic(base_url="https://api.deepseek.com/anthropic", api_key=os.environ["DEEPSEEK_API_KEY"])   # DeepSeek, in the Anthropic Messages format
MODEL = "deepseek-flash"
TOO_LONG = "maximum context length"                      # model interface: how this provider says a request is too long to send
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

# ── output: the one tool ────────────────────────────────────────────────────
SHELL = os.environ.get("SHELL") or os.environ.get("COMSPEC") or "/bin/sh"   # self model: the shell this computer uses
MACHINE = f"{platform.system()} {platform.release()} ({platform.machine()})"   # self model: the computer the body is on
tools = [{"name": "shell", "description": f"""Run a command in {SHELL}, on {MACHINE}. This shell is your body: your only way to observe and act. Through it you can do anything a person at this computer can do: work with files, run and install programs, drive apps, operate the desktop, reach the network.

Order of operations: choose the most precise operation that can reach the target, and read the result back through the shell. Fall back to the next one only when it can't reach the target, and come back up as soon as one can.

1. Files and data, directly: commands, pipes and scripts; install a tool if one is missing. Read back: the exit code and the result.
2. The app's own interface: its command-line tool or API. Read back: ask the app for its state.
3. Named controls: the system's accessibility layer, its buttons and fields by name. Read back: the window's controls, listed. That list is also how you see.
4. Pixels: only for what's truly visual. Act only at positions you've read, from the accessibility layer, text recognition or a vision model; never guess. Read back: a new screenshot, compared with the last. If nothing changed, you missed.

What you read back, not what you expected, decides whether it worked. If you don't have a tool for an operation, find or install one.

Each call can do several things: independent steps together, dependent ones in order, in your shell's own syntax. Keep calls focused, so their results stay small.""",   # the body: what it can do, and how
          "input_schema": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}]   # output: the one tool

# ── context ─────────────────────────────────────────────────────────────────
BORN = datetime.datetime.now()                           # self model: when this session began

def stamp(text, start=None):                             # current inputs: when it came in, and how long it ran if it ran
    now = datetime.datetime.now()
    ran = f", ran {(now - start).total_seconds():.1f}s" if start else ""
    return f"[{now:%Y-%m-%d %H:%M:%S}{ran}] {text}"

def mechanics():                                         # self model: this file, with the self model left out
    code = re.sub(r'^(tools = \[\{"name": "shell", "description": )f""".*?"""', r'\1"..."', open(__file__).read(), flags=re.S | re.M)   # its description: what you're reading
    return re.sub(r"^def system\(\):.*?(?=^def )", "def system(): ...  # left out: it is what you are reading\n\n", code, flags=re.S | re.M)

def system():                                            # self model: the mind, as the system prompt
    return f"""# Mind

**Identity:** You are an agent, working for the person who messages you.
**Drives:** do what you're asked, fully and correctly. Know, don't guess: check what you do by reading it back.
**Model:** you think with this model, within what you're shown each time: this mind, your body, and this session's messages. When the messages grow too long, the older part is summarized.
**Loop:** observe → think → act → repeat.
**Born:** {BORN:%Y-%m-%d %H:%M:%S}, in {os.getcwd()}. Every command runs from there. Each message you get is stamped with when it came in, and each command's result with how long it ran.
**Care:** reading is always safe. Anything that changes the world, like deleting, sending, buying or signing in, happens one step at a time, checked as you go. If it can't be undone, ask first. Never print or reveal a password or key.

## How you work

This code is your harness: what connects your mind to your body. Your mind and your tool's description are left out below, because they're what you're reading.

```python
{mechanics()}
```"""

def assemble_context(messages):                          # context: the mind as the system prompt, the body as the tool, the world as the messages
    return {"system": system(), "tools": tools, "messages": messages}

def compact(messages, drop):                             # current inputs: too long to send, so the older part is summarized
    turns = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    if drop > len(turns): sys.exit("[the conversation can't be summarized small enough]")
    keep = messages[turns[drop]:] if drop < len(turns) else [messages[turns[-1]]]
    summary = request_response(max_tokens=2048, system=system(), messages=keep + [{"role": "user", "content": "This conversation is too long to send. Summarize it into a gist that keeps what matters for carrying on."}])
    gist = next((b.text for b in summary.content if b.type == "text"), "")
    return [{"role": "user", "content": f"[the earlier conversation, summarized] {gist}"}]

# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    messages, drop = [{"role": "user", "content": stamp(capture_input())}], 0   # current inputs: the conversation so far
    while True:
        try:
            if drop: messages, drop = compact(messages, drop), 0
            output = request_response(max_tokens=16384, **assemble_context(messages)).content
        except BadRequestError as e:                     # too long to send: summarize on the next pass
            if TOO_LONG not in str(e): raise
            drop += 1
            continue
        messages.append({"role": "assistant", "content": output})
        results = handle_output(output)
        if results:                                      # a command ran: send back what it printed, and go again
            messages.append({"role": "user", "content": results})
            continue
        if len(sys.argv) > 1: break                      # stop: a one-off request is done
        messages.append({"role": "user", "content": stamp(capture_input())})   # hand back: the person's next message

control_flow()
````

Output now also stamps each command's result with how long it ran, and runs it in the shell it described. Run it, and ask who it is:

```bash
uv run ../harness.py
```

```
< Who are you, and where are you working?
$ pwd; ls -la
  └ /home/user/harness-engineering/shop
    total 16
    drwxr-xr-x 2 root root 4096 Oct 14 00:57 .
    drwxr-xr-x 4 root root 4096 Oct 14 00:57 ..
    -rw-r--r-- 1 root root  216 Oct 14 00:57 prices.py
    -rw-r--r-- 1 root root  322 Oct 11 03:54 test_prices.py
$ uname -a; whoami; date
  └ Linux vm 6.18.44-fc-v114 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux
    root
    Wed Oct 14 00:57:56 UTC 2026
$ cat prices.py; echo "-----"; cat test_prices.py
  └ def total(items, discount=0):
        """Add up (price, quantity) pairs, then take off a percentage discount."""
        subtotal = sum(price * quantity for price, quantity in items)
        return round(subtotal - discount, 2)
    -----
    import unittest
    from prices import total
    
    
    class TestTotal(unittest.TestCase):
        def test_no_discount(self):
            self.assertEqual(total([(10, 2), (5, 1)]), 25)
    
        def test_ten_percent_off(self):
            self.assertEqual(total([(10, 2), (5, 1)], discount=10), 22.5)
    
    
    if __name__ == "__main__":
        unittest.main()
> I'm an agent — I think with a model (DeepSeek, in the Anthropic Messages format), and this shell is my body: my only way to see and act on the machine.
  
  **Where I am:** `/home/user/harness-engineering/shop` — a Linux box (`Linux vm 6.18.44-fc-v114`, x86_64), running as `root`. It's 2026-10-14 00:57 UTC.
  
  **What's here:** just two small files, a shopping-cart price calculator and its unit tests.
  
  - `prices.py` — a `total(items, discount=0)` function that sums `(price, quantity)` pairs and subtracts a percentage discount.
  - `test_prices.py` — two `unittest` cases: no discount, and ten percent off.
  
  I read them rather than assumed, so here's what's actually in them. Want me to run the test suite, or is there something you'd like done with this code?
<
```

It knows what it is, what model it thinks with, and that its body is a shell, from what it's shown. Then it looked, and read the task's files rather than guess.

That's all five primitives. [`harness.py`](./harness.py) is a complete harness: with a model inside, it's an agent that knows what it is, works through the shell, and keeps going until the task is done.

## Porting it

Only the model interface knows the model. To wrap a different one, change these lines and nothing else:

```python
# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic(base_url="https://api.deepseek.com/anthropic", api_key=os.environ["DEEPSEEK_API_KEY"])   # DeepSeek, in the Anthropic Messages format
MODEL = "deepseek-flash"
TOO_LONG = "maximum context length"                      # model interface: how this provider says a request is too long to send
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)
```

- **Another provider that speaks Anthropic Messages**, including Anthropic itself: change the client's `base_url` and key, `MODEL`, and `TOO_LONG` to how that provider words its too-long error. For Claude, that's `Anthropic()`, a model like `claude-sonnet-5-5`, and `"prompt is too long"`.
- **A provider with its own format**, like OpenAI's: `request_response()` translates. On the way out, it turns the `system`, `tools` and `messages` it's given into that provider's request. On the way back, it turns the reply into what the rest of the harness reads: a list of blocks, each a `text` block with its `.text`, or a `tool_use` block with its `.id` and `.input["cmd"]`. Each command's result goes back as a `tool_result` with the same id, so the translation covers those too.

The rest of the harness, and how the agent behaves, stays the same.
