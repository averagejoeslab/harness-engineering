# Harness Engineering in a Hurry

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

An **agent** is anything that loops over three steps: observe, think, and act.

An agent built on a language model is made of two primitives. The **model** is its mind, and it only thinks: tokens go in, and it predicts the next one, over and over, until it predicts it should stop. On its own it can't see anything, and it can't do anything with what it writes. The **harness** is its body, and does everything else, through five primitives of its own, each serving part of the loop:

- **Input** observes: it captures what comes in, from a person or from the world.
- **Context** assembles what the model is shown each time: who it is, what it can do, and what it has observed so far.
- **Model interface** sends that to the model, and brings back what it thinks.
- **Output** acts: it carries out what the model decided, like running a command.
- **Control flow** repeats: it sends what happened back around, and decides whether to go again, hand back, or stop.

**Harness engineering** is building that body. Here we'll build a harness around a model, one primitive at a time, outward from the model, until together they make an agent. To prove each step out, the agent needs something to do: [`shop/`](./shop/) is a tiny project whose tests fail, and the request is always *"The tests are failing. Find out why and fix it."*

## Setup

You need [uv](https://docs.astral.sh/uv/) to run the code and a [DeepSeek API key](https://platform.deepseek.com/api_keys). We'll use DeepSeek's `deepseek-flash` model through its support for the Anthropic Messages format, so the code uses Anthropic's Python SDK. Clone this repo, move into the task's folder, and give it your key. Every command from here on runs in `shop/`:

```bash
git clone https://github.com/averagejoeslab/harness-engineering
cd harness-engineering/shop
export DEEPSEEK_API_KEY=your-key
```

The agent will change the task's files as we go. `git checkout .` puts the bug back.

## 1. Reach the model

All we have is a model. The first primitive, the **model interface**, reaches it: `request_response()` sends a request and returns the model's response. Every later step talks to the model through it.

```
┌──────────────────────────── harness ────────────────────────────┐
│                                                                 │
│  request ──────────► ┌───────── model ─────────┐ ─► response    │
│                      │ tokens in ─► next token │                │
│                      │      ▲            │     │                │
│                      │      └── append ◄─┘     │                │
│                      └─────────────────────────┘                │
│                                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

In [`1_model_interface.py`](./1_model_interface.py):

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

We send it the task, hardcoded, and print what comes back:

```bash
uv run ../1_model_interface.py
```

```
{
  "id": "msg_011CfwdKcf8R3kzbrzhHB9jH",
  "container": null,
  "content": [
    {
      "signature": "CAQS7gUKEAgSGAI4AUIIdGhpbmtpbmcSDJIk+AHgupAejxBvxRoMBTI4dWvaxi0cde+mIjDoScOkbnHBSvMRvzc8Gfx7pT+hws0S6Q/RZBsTp1dz4+vuY9hemtCmnBfhCRjC8EEqiwXV26bpUlHFvza0Ev5ehOlExor7m9+9JwsdXYtVt2proN/MOSK6sGX1g6BY60E5870XbxlZU91yWea8VP8iOoLH3U6/btC+Sjm1vErUlDjt82lLuC/fqw7atRHuOgi3+uLwjgJx8FNfdKWJlEb+fakbYVCqbY17MKBAYWUi8EH9ok8M32M3gxGpCV2Dq8yuns8/mrAvNa6utmpME39nt4q28RPU3vefhyMxscDf70m3t4ffC4vkyr/1k5ZnnfavpBSFYEKFSNZU0kCsD8l40z/qG50a7vsZbmEYR9J1I9hhVLWPZ3T/d/x4fsxCPsjpaBQziwI9kWEwBC7x5vHf8Cd7laPyChGqtcrebnedHyAZ5zwPi2hI9I0m3aglNsAetxO8KhQh/YG06zN/STyHtbNYQ8jzRFrCoBCTwDlg6TUmkfbBgvA0SNP4YzBApJOz5QpZBYX8AYoRLhiOK5ByDcfdzQDm/U2Dx+na66Z4qkkrChFSwsaYhECiKFts0P8PNJFXgimTmNvjXrRh4pDUXii/Izn5QLFa9uit88kru21TMb133/0R/xHh565Tv8wPBGTfmX+LZ9taeIhR2KIUEwsYMKwl2w0EOe7E36XWhMreK3ZHWH7IannrjPBPTvpYINC3J52UD61hZ2La582fkDRIfTjM+d/bjZmBzuSTvGdV62SORTeVo1U9LGoztlmDRa+aqe6BLia67g1vE9TmjzdDOerfN7xe8wTKY1VnXerbCXJZgjGsjV904A2jpImhQFl98LI8s6uZdRRB667LcOt65UnMxwp6fHFTzqFpdHt8rJ/ilFw3HPHd4PxBgMl2A8F3ziA5U3rj+2X1OMnZj6IS1ugYGNtZga/nEcwYAQ==",
      "thinking": "",
      "type": "thinking"
    },
    {
      "citations": null,
      "text": "I can't see your code or test output in this conversation, and I don't have tools to look at your repository, so I can't tell yet why the tests are failing. Could you share:\n\n1. **The failing test output**: the full error message and stack trace, copied as text.\n2. **The relevant code**: the function or module under test and the test file itself.\n3. **How you run the tests**: for example `pytest`, `npm test`, or `go test ./...`, plus the language and framework versions if you know them.\n4. **Recent changes**: anything you changed before the failures started, such as dependency upgrades, refactors, or config edits.\n5. **Scope**: whether all tests fail or only some, and whether they fail locally, in CI, or both.\n\nOnce I have the error output and the code involved, I can work out the root cause and suggest a specific fix.",
      "type": "text"
    }
  ],
  "diagnostics": null,
  "model": "claude-sonnet-5-5",
  "role": "assistant",
  "stop_details": null,
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "cache_creation": {
      "ephemeral_1h_input_tokens": 0,
      "ephemeral_5m_input_tokens": 0
    },
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "inference_geo": "global",
    "input_tokens": 24,
    "output_tokens": 313,
    "output_tokens_details": {
      "thinking_tokens": 53
    },
    "server_tool_use": null,
    "service_tier": "standard"
  }
}
```

The model answered, but it can't act, so it asks us to share the code. And the request is hardcoded, so nobody can ask anything else. We'll fix both by following the data's flow, starting where it begins: input.

## 2. Let someone ask

Next in the flow is **input**, which captures what comes in. `capture_input()` reads what a person types into the terminal while the program runs, or takes a one-off request from the command line:

```
┌──────────────────────────── harness ────────────────────────────┐
│                                                                 │
│  input ────────────► ┌───────── model ─────────┐ ─► response    │
│                      │ tokens in ─► next token │                │
│                      │      ▲            │     │                │
│                      │      └── append ◄─┘     │                │
│                      └─────────────────────────┘                │
│                                                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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
  "id": "msg_011CfwdLwSGGgRTKfS7MC3FG",
  "container": null,
  "content": [
    {
      "signature": "CAQSiAYKEAgSGAI4AUIIdGhpbmtpbmcSDHegbheOv/DDScA6SBoMrgtYIbWD2QAMFMh8IjBeOyac3IAts3rkcA0wp7+pFVrnNicZICq4PNBQbjnBh+qmGYPd2JaESXMtni3p3DAqpQW9WxksIYGIzykJ9SO3+N/NydbN9vxTES5gIVScgqaAGSfrD2GktETL8YYn3WTMBycuA3ls6K7nqKXpRDH+hcrcNLNNdAqNwaJ/ygen8d+nqnegi9+MLxTLW+BENLubc6VjOvs2HkZdOvUGqTOudBOqb2ooaGYWpACcHb09J7mFqFg2BE6zkcyM8aF1y2kU66onX6nCKqZXktjcIRjE5IKiMpZEt9BvjpOphT5U49t1J5wlITdPQl9gvbFMx8/LMTimlCp0jGI1FcO0i649fUQkVkUIXRyOj2pplmwCBEE6M7UWIa4neotKrE9KZPMnjJxE0dBkE6fMRTu6Xawb/S+LiP3YAUmf+sqcb/IX8TzuGX6m66LD/oHaKKh4P4CEYCbj/OC0EfPu4x084OalEwIDU25KaLFxMJoajQQHsttSwOFhfuVIFXxGZfjzJ2LZMPirwnl6MRRP1sIpti3qDxKlBhzS6zoiO+OPoJBD16eYmPNZxb2hiaPs7ndDgylKGCtpc+rPQoDO4fPAteDF3SYpBCX4fbW6u8Wj78jB4ZLKKBij2d25bLF3q+hY6u0eQx2RAlnBtmWLQVTQxxK+mZz//byyD5hXAeiWlWBuyn1Y0CWIldrpIaoehyxcTYMnf8zB/q/IM3Y/rRIi0EsAit+h8Qo9kmAibmQyGsfXEtcCWADKYm9PJUK04rHC2ROyGzSGlfIHykcbKlagFpM35n9VBZEVOTmtuVVw2pcv8ThrvvPNCAV6rX7Qexbk73DrYrBi6wyB9NKmN3ScX12wI2oTC1nDdSdb0APDahCwH2RKhc2nGkaHTlKhnEy1jH/Xn3fGNejuFmcNrxfz14N42JUpOMNRolBRVnZd1IdCql9eJJCI1GWzCaQLwITBjBYuZirs0bJ9dRgB",
      "thinking": "",
      "type": "thinking"
    },
    {
      "citations": null,
      "text": "I can't see your code or test output in this conversation, so I can't tell yet why the tests are failing. Could you share:\n\n1. **The failing test output**: the full error message and stack trace (copy-paste, not a screenshot if possible).\n2. **The relevant code**: the test file and the source file(s) it exercises.\n3. **How you run the tests**: e.g. `pytest`, `npm test`, `go test ./...`, `cargo test`.\n4. **Recent changes**: anything you changed before they started failing, such as dependency upgrades, refactors, or config changes.\n5. **Environment details** (if relevant): language/runtime version, OS, and whether the failure also happens in CI or only locally.\n\nIf you can paste the output of the test command, that's usually enough for me to find the cause. If the project is small, pasting the failing test and the function it covers will help me suggest a concrete fix.",
      "type": "text"
    }
  ],
  "diagnostics": null,
  "model": "claude-sonnet-5-5",
  "role": "assistant",
  "stop_details": null,
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "type": "message",
  "usage": {
    "cache_creation": {
      "ephemeral_1h_input_tokens": 0,
      "ephemeral_5m_input_tokens": 0
    },
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0,
    "inference_geo": "global",
    "input_tokens": 24,
    "output_tokens": 350,
    "output_tokens_details": {
      "thinking_tokens": 64
    },
    "server_tool_use": null,
    "service_tier": "standard"
  }
}
```

Now anyone can ask, but the model can still only reply in words: it asks us to share the code, because it can't act. That's next in the flow: output.

## 3. Let it act

Next in the flow is **output**, which handles what the model sends back. We describe one tool, `shell`, so the model can ask to run a command. `handle_output()` runs each command it asks for. `show()` prints the model's words after `>`, and `nested()` puts what a command printed under it, after `└`:

```
┌──────────────────────────── harness ────────────────────────────┐
│                                                                 │
│  input ────────────► ┌───────── model ─────────┐ ─► output ─┬───┼─► person
│                      │ tokens in ─► next token │            │   │
│                      │      ▲            │     │            │   │
│                      │      └── append ◄─┘     │            │   │
│                      └─────────────────────────┘            │   │
│                      runs a tool; its result goes nowhere ◄─┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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

We run it, and type the task at the `<` prompt. Its commands run in `shop/`, on your machine, without asking. From here on, `<` is what you typed, `>` is what the model said, `$` is a command it ran, and `└` is what that command printed:

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

Here it went straight to a command, so there's no `>` line. When it writes something first, that shows after `>`.

It ran a command, but what the command printed goes nowhere. That's new input, from the world, and nothing sends it back to the model, so it can't take the next step. Sending it back and going again is next in the flow: control flow.

## 4. Let it keep going

Next in the flow is **control flow**, which defines the shape of the loop. `control_flow()` sends back what the commands printed, and goes again until the model is done. Then it hands back to you for your next message, or stops if the request was a one-off from the command line. Ctrl-C stops it.

```
┌──────────────────────────── harness ────────────────────────────┐
│                                                                 │
│  input ────────────► ┌───────── model ─────────┐ ─► output ─┬───┼─► person
│    ▲                 │ tokens in ─► next token │            │   │
│    │                 │      ▲            │     │            │   │
│    │                 │      └── append ◄─┘     │            │   │
│    │                 └─────────────────────────┘            │   │
│    └───────────────────── a tool's result ◄─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

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
  └ prices.py
    test_prices.py
    npm error code ENOENT
    npm error syscall open
    npm error path /home/user/harness-engineering/shop/package.json
    npm error errno -2
    npm error enoent Could not read package.json: Error: ENOENT: no such file or directory, open '/home/user/harness-engineering/shop/package.json'
    npm error enoent This is related to npm not being able to find a file.
    npm error enoent
    npm error A complete log of this run can be found in: /root/.npm/_logs/2026-10-12T03_24_47_234Z-debug-0.log
    ============================= test session starts ==============================
    platform linux -- Python 3.13.16, pytest-9.1.1, pluggy-1.6.0
    rootdir: /home/user/harness-engineering/shop
    collected 2 items
    
    test_prices.py .F                                                        [100%]
    
    =================================== FAILURES ===================================
    ________________________ TestTotal.test_ten_percent_off ________________________
    
    self = <test_prices.TestTotal testMethod=test_ten_percent_off>
    
        def test_ten_percent_off(self):
    >       self.assertEqual(total([(10, 2), (5, 1)], discount=10), 22.5)
    E       AssertionError: 15 != 22.5
    
    test_prices.py:10: AssertionError
    =========================== short test summary info ============================
    FAILED test_prices.py::TestTotal::test_ten_percent_off - AssertionError: 15 !...
    ========================= 1 failed, 1 passed in 0.02s ==========================
    make: *** No rule to make target 'test'.  Stop.
    error: could not find `Cargo.toml` in `/home/user/harness-engineering/shop` or any parent directory
    # ./...
    pattern ./...: directory prefix . does not contain main module or its selected dependencies
    FAIL	./... [setup failed]
    FAIL
$ cat prices.py test_prices.py
  └ def total(items, discount=0):
        """Add up (price, quantity) pairs, then take off a percentage discount."""
        subtotal = sum(price * quantity for price, quantity in items)
        return round(subtotal - discount, 2)
    import unittest
    from prices import total
    
    
    class TestTotal(unittest.TestCase):
        def test_no_discount(self):
            self.assertEqual(total([(10, 2), (5, 1)]), 25)
    
        def test_ten_percent_off(self):
            self.assertEqual(total([(10, 2), (5, 1)], discount=10), 22.5)
    
    
    if __name__ == "__main__":
        unittest.main()
> The docstring says the discount is a percentage, but the code subtracts it as a flat amount. I'll fix the code.
$ sed -i 's/return round(subtotal - discount, 2)/return round(subtotal * (1 - discount \/ 100), 2)/' prices.py && python -m pytest -q 2>&1 | tail -3
  └ /root/.cache/uv/environments-v2/4-control-flow-9aa046ecf9801748/bin/python: No module named pytest
$ pytest -q 2>&1 | tail -3; cat prices.py
  └ ..                                                                       [100%]
    2 passed in 0.01s
    def total(items, discount=0):
        """Add up (price, quantity) pairs, then take off a percentage discount."""
        subtotal = sum(price * quantity for price, quantity in items)
        return round(subtotal * (1 - discount / 100), 2)
> The tests pass now: both of them, when I re-ran `pytest`.
  
  **Cause:** `total()` in `prices.py` subtracted `discount` as a flat amount, even though its docstring and the test treat it as a percentage. With `discount=10` on a 25 subtotal, it returned 15 (25 − 10) instead of 22.5.
  
  **Fix:** it now takes the percentage off the subtotal:
  ```python
  return round(subtotal * (1 - discount / 100), 2)
  ```
< 
````

The task is done. **This is an agent:** it keeps going until the task is finished, then hands back to you.

But it doesn't know what it is, what its body is, or how best to use it. Ask, and it has to go looking:

```bash
uv run ../4_control_flow.py
```

```
< Who are you, and where are you working?
> I'll check the environment first so I can answer the second part.
$ pwd
  └ /home/user/harness-engineering/shop
$ whoami
  └ root
$ hostname
  └ vm
$ uname -a
  └ Linux vm 6.18.44-fc-v114 #1 SMP PREEMPT_DYNAMIC @0 x86_64 x86_64 x86_64 GNU/Linux
> I'm an AI assistant. I can run shell commands on your behalf, and I just used that to look at the environment.
  
  - **Working directory:** `/home/user/harness-engineering/shop`
  - **User:** `root`
  - **Host:** a Linux machine named `vm`, running kernel 6.18.44-fc-v114 on x86_64
  
  The directory name suggests a project called "shop" inside a "harness-engineering" folder. I haven't looked at the contents yet. I can list the files or read the README if you want to know what the project is.
< 
```

The last primitive, **context**, fixes that.

## 5. Give it context

Next is **context**: what the model is shown on each call. It's best understood from the agent's perspective. Context is its working memory, everything it has in mind at this moment. Whatever isn't in its context, the agent doesn't have in mind, so what we put there, and how, shapes everything it does.

Once we know which chunks we want in context, how we organize them is decided by the roles available and their hierarchy of authority. Every chunk has to sit in a role, and the model learned in training how much authority each role carries. For DeepSeek, the roles look like this:

```
system      the mind: who it is, its drives, how it operates   ▲ most authority
tools       the body: what it can do, and how                  │
user        the world: people and programs reaching it         │
assistant   the self, acting: its words and actions            │
user        a tool's result: what the world returned           ▼ least
```

Underneath, roles are tokens too. Each chunk is wrapped in role markers the model learned in training, so it knows who is speaking, writes only its own turn, and stops at the end of it. That's what makes it more than autocomplete. Here is a short context in DeepSeek's published format, every token real:

```
<｜begin▁of▁sentence｜>You are an agent.<｜User｜>Which files are in this folder?<｜Assistant｜></think>
```

`<｜User｜>` and `<｜Assistant｜>` mark the roles, and `</think>` switches its thinking off. The model writes on from the end, one token at a time, and stops with its end token. These are the markers `deepseek-flash` reads. The harness doesn't write them itself: it sends a request in the Anthropic Messages format, and DeepSeek turns it into tokens like these. Later in this step we show that request.

To place a chunk, we ask: who does it serve, how much does it matter, and where did it come from? The answers pick its role, and its role should never give it more authority than its source.

With our chunks organized, one limit remains: the window they go into has a fixed size. The harness assembles context fresh on each call, and as a session grows, the window fills. It can count tokens to see that coming, or simply wait for the "too long" error. Either way, it has to make room:

| Strategy | What it does | Keeps | Loses |
|---|---|---|---|
| Sliding window | drops the oldest messages | the recent | the start, maybe the task |
| Compaction | summarizes the oldest part | the gist | the detail |
| Cherry-picked assembly | includes only what this moment needs | focus | the rest, until it's fetched |

```
┌──────────────────────────── harness ────────────────────────────┐
│                                                                 │
│  input ─► context ─► ┌───────── model ─────────┐ ─► output ─┬───┼─► person
│    ▲                 │ tokens in ─► next token │            │   │
│    │                 │      ▲            │     │            │   │
│    │                 │      └── append ◄─┘     │            │   │
│    │                 └─────────────────────────┘            │   │
│    └───────────────────── a tool's result ◄─────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

In [`harness.py`](./harness.py), context is assembled like this:

- **System, the mind:** who it is, what drives it, the model it thinks with, its loop, when and where it was born, how carefully to change things, and its own harness code.
- **Tools, the body:** the shell, named for this computer, with how to use it.
- **User, the world:** what you type, stamped with when it came in, and each command's result, stamped with how long it ran, so it always knows "now".
- **Assistant, the self acting:** its words and commands, as they came back.
- **Size:** it waits for the "too long" error, then compacts: `compact()` summarizes the oldest part into a user message.

The tool's description centers on an order of operations: use the most precise operation that can reach the target, read the result back, and fall back only when it can't. The shop task only needs the first.

| | Operation | How it checks the result |
|---|---|---|
| 1 | Work on files and data directly, with commands and scripts | the exit code and the result |
| 2 | Use the app's own interface: its command-line tool or API | ask the app for its state |
| 3 | Use named controls: the system's accessibility layer, its buttons and fields by name | list the window's controls |
| 4 | Use pixels, only for what's truly visual | compare a new screenshot with the last |

Here's what DeepSeek is sent on the task's second request, after its first command came back. The mind and the body are cut after their first lines:

```json
{
  "model": "claude-sonnet-5-5",
  "max_tokens": 16384,
  "system": [
    {
      "type": "text",
      "cache_control": {
        "type": "ephemeral"
      },
      "text": "# Mind\n\n**Identity:** You are an agent, working for the person who messages you.\n…"
    }
  ],
  "tools": [
    {
      "name": "shell",
      "description": "Run a command in /bin/bash, on Linux 6.18.44-fc-v114 (x86_64). This shell is your body: your only way to observe and act. …",
      "input_schema": {
        "type": "object",
        "properties": {
          "cmd": {
            "type": "string"
          }
        },
        "required": [
          "cmd"
        ]
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "[2026-10-12 06:09:17] The tests are failing. Find out why and fix it."
    },
    {
      "role": "assistant",
      "content": [
        {
          "id": "toolu_01VkuB9rUksVeTg4w2sqvv1H",
          "caller": {
            "type": "direct"
          },
          "input": {
            "cmd": "ls -la; git status 2>&1 | head; ls tests test 2>&1 | head"
          },
          "name": "shell",
          "type": "tool_use"
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "tool_result",
          "tool_use_id": "toolu_01VkuB9rUksVeTg4w2sqvv1H",
          "content": "[2026-10-12 06:09:19, ran 0.0s] total 16\ndrwxr-xr-x 2 root root 4096 Oct 12 05:56 .\ndrwxr-xr-x 6 root root 4096 Oct 12 03:44 ..\n-rw-r--r-- 1 root root  216 Oct 12 05:56 prices.py\n-rw-r--r-- 1 root root  322 Oct 11 03:54 test_prices.py\nOn branch main\nYour branch is up to date with 'origin/main'.\n\nnothing to commit, working tree clean\nls: cannot access 'tests': No such file or directory\nls: cannot access 'test': No such file or directory\n"
        }
      ]
    }
  ]
}
```

`stamp()`, `system()`, `assemble_context()` and `compact()` are added:

````python
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
    return [{"type": "text", "cache_control": {"type": "ephemeral"}, "text": f"""# Mind

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
```"""}]

def assemble_context(messages):                          # context: the mind as the system prompt, the body as the tool, the world as the messages
    return {"system": system(), "tools": tools, "messages": messages}

def compact(messages, drop):                             # current inputs: too long to send, so the older part is summarized
    turns = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    if drop > len(turns): sys.exit("[the conversation can't be summarized small enough]")
    keep = messages[turns[drop]:] if drop < len(turns) else [messages[turns[-1]]]
    summary = request_response(max_tokens=2048, system=system(), messages=keep + [{"role": "user", "content": "This conversation is too long to send. Summarize it into a gist that keeps what matters for carrying on."}])
    gist = next((b.text for b in summary.content if b.type == "text"), "")
    return [{"role": "user", "content": f"[the earlier conversation, summarized] {gist}"}]
````

Output and control flow change to use them. Output's tool becomes the body: the shell, named for this computer, with a description of what it can do and how, which is the order of operations. It runs every command with that shell, and stamps each result. Control flow stamps what you type, sends what context assembles, and calls `compact()` when a request is too long:

```python
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

def handle_output(output):                               # output: handles the model's outputs, running each command it asks for
    results = []
    for block in output:
        if block.type == "text": show(block.text)
        if block.type == "tool_use":
            print(f"$ {block.input['cmd']}")
            start = datetime.datetime.now()
            done = subprocess.run(block.input["cmd"], shell=True, executable=SHELL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            result = done.stdout or f"(exit {done.returncode})"
            print(nested(result))
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": stamp(result, start)})  # input: from the world
    return results

# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    messages, drop = [{"role": "user", "content": stamp(capture_input())}], 0   # current inputs: the conversation so far
    while True:
        try:
            if drop: messages, drop = compact(messages, drop), 0
            output = request_response(max_tokens=16384, **assemble_context(messages)).content
        except BadRequestError as e:                     # too long to send: summarize on the next pass
            if "prompt is too long" not in str(e): raise
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
