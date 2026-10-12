# /// script
# dependencies = ["anthropic"]
# ///
import subprocess, sys, os, re, datetime, platform
from anthropic import Anthropic, BadRequestError

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

# ── output: the one tool ────────────────────────────────────────────────────
SHELL = os.environ.get("SHELL") or os.environ.get("COMSPEC") or "/bin/sh"   # self model: the shell this computer uses
tools = [{"name": "shell", "description": f"Run a command in {SHELL}", "input_schema": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}]

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
            done = subprocess.run(block.input["cmd"], shell=True, executable=SHELL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            result = done.stdout or f"(exit {done.returncode})"
            print(nested(result))
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})  # input: from the world
    return results

# ── context ─────────────────────────────────────────────────────────────────
MACHINE = f"{platform.system()} {platform.release()} ({platform.machine()})"   # self model: the computer the body is on

def mechanics():                                         # self model: this file, with the instructions left out
    return re.sub(r"^def system\(\):.*?(?=^def )", "def system(): ...  # left out: it is what you are reading\n\n", open(__file__).read(), flags=re.S | re.M)

def system():                                            # self model and instructions
    return [{"type": "text", "cache_control": {"type": "ephemeral"}, "text": f"""# Self Model

**Identity:** You are an agent, working for the person who messages you.
**Mind:** this model. You think within what you're shown each time: this self model, your instructions, and this session's messages. When the messages grow too long, the older part is summarized.
**Body:** the shell, {SHELL}, on {MACHINE}. It's your only way to observe and act. Through it you can do anything a person at this computer can do: work with files, run and install programs, drive apps, operate the desktop, reach the network.
**Where:** {os.getcwd()}
**When:** {datetime.date.today()}
**Loop:** observe → think → act → repeat.
**How you work:** your harness's code is at the end.

# Instructions

## Order of operations

Choose the most precise operation that can reach the target, and read the result back through the shell. Fall back to the next one only when it can't reach the target, and come back up as soon as one can.

1. **Files and data, directly:** commands, pipes and scripts; install a tool if one is missing. Read back: the exit code and the result.
2. **The app's own interface:** its command-line tool or API. Read back: ask the app for its state.
3. **Named controls:** the system's accessibility layer, its buttons and fields by name. Read back: the window's controls, listed. That list is also how you see.
4. **Pixels:** only for what's truly visual. Act only at positions you've read, from the accessibility layer, text recognition or a vision model; never guess. Read back: a new screenshot, compared with the last. If nothing changed, you missed.

What you read back, not what you expected, decides whether it worked. If you don't have a tool for an operation, find or install one.

## Each call

One call can do several things: independent steps together, dependent ones in order, in your shell's own syntax. Keep calls focused, so their results stay small.

## Changes

Reading is always safe. Anything that changes the world, like deleting, sending, buying or signing in, happens one step at a time, checked as you go. If it can't be undone, ask first. Never print or reveal a password or key.

# How you work

This code is your harness. Its instructions are left out below, because they're what you're reading.

```python
{mechanics()}
```"""}]

def assemble_context(messages):                          # context: assembles what the model is shown: self model, instructions, current inputs
    return {"system": system(), "tools": tools, "messages": messages}

def compact(messages, drop):                             # current inputs: too long to send, so the older part is summarized
    turns = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    if drop > len(turns): sys.exit("[the conversation can't be summarized small enough]")
    keep = messages[turns[drop]:] if drop < len(turns) else [messages[turns[-1]]]
    summary = request_response(max_tokens=2048, system=system(), messages=keep + [{"role": "user", "content": "This conversation is too long to send. Summarize it into a gist that keeps what matters for carrying on."}])
    gist = next((b.text for b in summary.content if b.type == "text"), "")
    return [{"role": "user", "content": f"[the earlier conversation, summarized] {gist}"}]

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: captures what a person types
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line

# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    chat = len(sys.argv) < 2                             # a request on the command line runs once; otherwise it's a chat
    message = " ".join(sys.argv[1:]) or capture_input()
    messages, drop = [{"role": "user", "content": message}], 0   # current inputs: the conversation so far
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
        if not chat: break                               # stop: a request from the command line is done
        messages.append({"role": "user", "content": capture_input()})   # hand back: the person's next message

control_flow()
