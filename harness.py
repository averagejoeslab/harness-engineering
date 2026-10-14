# /// script
# dependencies = ["anthropic"]
# ///
import subprocess, sys, os, re, datetime, platform
from anthropic import Anthropic, BadRequestError

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
            start = datetime.datetime.now()
            done = subprocess.run(block.input["cmd"], shell=True, executable=SHELL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            result = done.stdout or f"(exit {done.returncode})"
            print(nested(result))
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": stamp(result, start)})  # input: from the world
    return results

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

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: a one-off request on the command line, or what a person types
    if len(sys.argv) > 1: return " ".join(sys.argv[1:])
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line

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
