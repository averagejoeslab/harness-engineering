# /// script
# dependencies = ["anthropic"]
# ///
# One harness, many agents, one person moving between them: human in the orchestration.
# uv run harness_orchestrated.py <agent> [request]
# Each agent has a folder, agents/<agent>/, in the folder you run from. You write charter.md. The harness keeps the rest:
#   episodes.jsonl  the trace: every message, as it happens
#   gist.md         the whole conversation, summarized after every turn, in the background
#   work/           what the agent makes
# Agents know of each other and read each other's folders with the shell. Nothing is pushed between them.
import subprocess, sys, os, re, json, glob, threading, datetime, platform
from anthropic import Anthropic, BadRequestError

# ── agent ───────────────────────────────────────────────────────────────────
NAME = sys.argv[1] if len(sys.argv) > 1 else sys.exit("usage: uv run harness_orchestrated.py <agent> [request]")
ONE_OFF = len(sys.argv) > 2                              # a request on the command line: do it, then stop
HOME = f"agents/{NAME}"
CHARTER, EPISODE, GIST, WORK = f"{HOME}/charter.md", f"{HOME}/episodes.jsonl", f"{HOME}/gist.md", f"{HOME}/work"
if not os.path.exists(CHARTER): sys.exit(f"no charter: write {CHARTER} first")
os.makedirs(WORK, exist_ok=True)
LIMIT = int(os.environ.get("HARNESS_CONTEXT_LIMIT_CHARS", "0"))   # test hook: pretend the API said "prompt is too long" past this many characters

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
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

Each call can do several things: independent steps together, dependent ones in order, in your shell's own syntax. Keep calls focused, so their results stay small. Each command is stopped after two minutes: give network commands a timeout of their own.

Other agents

Other agents work for the same person, in this same folder. You can read what they did, with the shell. Each has a folder, agents/<name>/:
- charter.md: what the agent is for
- gist.md: its whole conversation, summarized. Rewritten after every turn of its, so it can lag a turn behind while the agent is working.
- episodes.jsonl: its trace, every message of its conversation, written as it happens. One JSON message per line, long lines.
- work/: the files it made

Read moves:
- who is here: `ls agents/`, and `head -n 3 agents/*/charter.md`
- how fresh a gist is: `ls -la --time-style=full-iso agents/*/gist.md`
- read a gist or a file: `cat agents/<name>/gist.md`, `ls -la agents/<name>/work`
- the actions an agent took: `grep -o '"cmd": "[^"]*"' agents/<name>/episodes.jsonl`
- how it ended: `tail -n 2 agents/<name>/episodes.jsonl | cut -c1-600`
- find something it said or saw: `grep -i "topic" agents/<name>/episodes.jsonl | cut -c1-400`

Recall ladder: go from the gist, to its files, to its trace, and stop as soon as you have what you need. The gist is a summary, so it can be wrong or leave things out: check it against the files or the trace before you rely on it for something that matters.

Rules: never edit another agent's files. If something of theirs should change, tell the person.""",   # the body: what it can do, and how
          "input_schema": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}]   # output: the one tool

def show(text):                                          # output: the model's words, after >
    print("> " + text.replace("\n", "\n  "))

def nested(result):                                      # output: what a command printed, nested under it with └
    return "  └ " + "\n    ".join(result.rstrip("\n").split("\n"))

def run(cmd, env):                                       # output: runs one command; resilience: two minutes at most, and whatever it started stops with it
    p = subprocess.Popen(cmd, shell=True, executable=SHELL, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace", start_new_session=os.name == "posix")
    try: out, _ = p.communicate(timeout=120)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, 9) if os.name == "posix" else p.kill()
        out = (p.communicate()[0] or "") + "\n[stopped: it ran for over two minutes]"
    return out, p.returncode

def handle_output(output):                               # output: handles the model's outputs, running each command it asks for
    results = []
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}   # security: the key stays out of the shell's environment
    for block in output:
        if block["type"] == "text": show(block["text"])
        if block["type"] == "tool_use":
            print(f"$ {block['input']['cmd']}")
            start = datetime.datetime.now()
            out, code = run(block["input"]["cmd"], env)
            result = out or f"(exit {code})"
            print(nested(result))
            results.append({"type": "tool_result", "tool_use_id": block["id"], "content": stamp(result, start)})  # input: from the world
    return results

# ── context ─────────────────────────────────────────────────────────────────
BORN = datetime.datetime.now()                           # self model: when this session began

def stamp(text, start=None):                             # current inputs: when it came in, and how long it ran if it ran
    now = datetime.datetime.now()
    ran = f", ran {(now - start).total_seconds():.1f}s" if start else ""
    return f"[{now:%Y-%m-%d %H:%M:%S}{ran}] {text}"

def peers():                                             # self model: the other agents here when this one was born
    found = [f"- **{p.split('/')[1]}**: {open(p).read().strip().splitlines()[0]}" for p in sorted(glob.glob("agents/*/charter.md")) if p.split("/")[1] != NAME]
    return "\n".join(found) or "(none yet)"

def mechanics():                                         # self model: this file, with the self model left out
    code = re.sub(r'^(tools = \[\{"name": "shell", "description": )f""".*?"""', r'\1"..."', open(__file__).read(), flags=re.S | re.M)   # its description: what you're reading
    return re.sub(r"^def system\(\):.*?(?=^def )", "def system(): ...  # left out: it is what you are reading\n\n", code, flags=re.S | re.M)

def system():                                            # self model: the mind, as the system prompt
    return [{"type": "text", "cache_control": {"type": "ephemeral"}, "text": f"""# Mind

**Identity:** You are **{NAME}**, an agent working for the person who messages you. Other agents work for the same person, in the same folder.
**Charter:** {open(CHARTER).read().strip()}
**Drives:** do what you're asked, fully and correctly. Know, don't guess: check what you do by reading it back.
**Model:** you think with this model, within what you're shown each time: this mind, your body, and this conversation. When the conversation grows too long, the older part is summarized; every message is still in your trace.
**Loop:** observe → think → act → repeat.
**Born:** {BORN:%Y-%m-%d %H:%M:%S}, in {os.getcwd()}. Every command runs from there. Each message you get is stamped with when it came in, and each command's result with how long it ran.
**Yours:** your files go in `{WORK}/`. Your trace is `{EPISODE}`. Your gist is `{GIST}`, rewritten after every turn of yours, for the others to read. Your conversation carries on across the times the person comes back to you.
**Peers:** here when you were born:
{peers()}
Others may have appeared since: list `agents/`. Nothing of theirs is loaded for you: read what you need before you rely on it. See "Other agents" in your tool.
**Care:** reading is always safe. Anything that changes the world, like deleting, sending, buying or signing in, happens one step at a time, checked as you go. If it can't be undone, ask first. Never print or reveal a password or key. Never edit another agent's files.

## How you work

This code is your harness: what connects your mind to your body. Your mind and your tool's description are left out below, because they're what you're reading.

```python
{mechanics()}
```"""}]

def assemble_context(messages):                          # context: the mind as the system prompt, the body as the tool, the world as the messages
    return {"system": system(), "tools": tools, "messages": messages}

def summarize(messages, drop):                           # current inputs: the gist of the conversation, from its drop-th operator message on
    turns = [i for i, m in enumerate(messages) if m["role"] == "user" and isinstance(m["content"], str)]
    if drop > len(turns): sys.exit("[the conversation can't be summarized small enough]")
    keep = messages[turns[drop]:] if drop < len(turns) else [messages[turns[-1]]]
    for _ in range(3):                                   # resilience: the model sometimes stops after an empty thinking block with no text, so thinking is off here and an empty reply is asked for again
        summary = request_response(max_tokens=2048, system=system(), thinking={"type": "between_tools"}, messages=keep + [{"role": "user", "content": "This conversation is too long to send. Summarize it into a gist that keeps what matters for carrying on."}])
        gist = next((b.text for b in summary.content if b.type == "text" and b.text.strip()), "")
        if gist: break
    return gist

COMPACTED = "[the earlier conversation, summarized"      # persistence: how a compaction reads in the trace
def compact(messages, drop):                             # current inputs: too long to send, so the older part is summarized
    return [{"role": "user", "content": f"{COMPACTED}; every message is in {EPISODE}] {summarize(messages, drop)}"}]

# ── persistence: the trace, and the gist for the others ─────────────────────
def blocks(content):                                     # persistence: a response as plain data: what's said and what's asked, nothing else
    return [{"type": "text", "text": b.text} if b.type == "text" else {"type": "tool_use", "id": b.id, "name": b.name, "input": b.input}
            for b in content if b.type in ("text", "tool_use")]

def remember(message):                                   # persistence: the trace, every message as it was
    with open(EPISODE, "a") as f: f.write(json.dumps(message) + "\n")

def add(messages, message):                              # persistence: one message, two places: the conversation and the trace
    messages.append(message); remember(message)

def resume():                                            # persistence: the conversation so far, from the last compaction on
    if not os.path.exists(EPISODE): return []
    messages = [json.loads(line) for line in open(EPISODE)]
    start = max([i for i, m in enumerate(messages) if isinstance(m["content"], str) and m["content"].startswith(COMPACTED)] or [0])
    messages = messages[start:]
    last = messages[-1] if messages else None
    if last and last["role"] == "assistant" and any(b["type"] == "tool_use" for b in last["content"]):   # it stopped while commands were running
        add(messages, {"role": "user", "content": [{"type": "tool_result", "tool_use_id": b["id"], "is_error": True,
            "content": "[interrupted: it may or may not have run. Check before repeating it.]"} for b in last["content"] if b["type"] == "tool_use"]})
    return messages

gist_lock, gist_job = threading.Lock(), {"next": None, "running": False}
def write_gist(messages):                                # the gist: the whole conversation so far, summarized the way compaction summarizes it
    gist = summarize(messages, 0)
    if not gist: return
    with open(GIST + ".tmp", "w") as f: f.write(f"# gist of {NAME}, as of {datetime.datetime.now():%Y-%m-%d %H:%M:%S}, {len(messages)} messages in its conversation. Every message is in {EPISODE}.\n\n{gist}\n")
    os.replace(GIST + ".tmp", GIST)                      # readers never see half a gist

def gist_worker():                                       # the gist: one at a time, newest state wins
    while True:
        with gist_lock:
            messages, gist_job["next"] = gist_job["next"], None
            if messages is None: gist_job["running"] = False; return
        try: write_gist(messages)
        except Exception as e: print(f"[gist not written: {e}]", file=sys.stderr)

def refresh_gist(messages):                              # the gist: after every turn, in the background, so the loop doesn't wait for it
    with gist_lock:
        gist_job["next"] = list(messages)
        if gist_job["running"]: return
        gist_job["running"] = True
    gist_job["thread"] = threading.Thread(target=gist_worker); gist_job["thread"].start()

def finish_gist():                                       # the gist: the last one is written before the process ends, while this file is still whole
    if gist_job.get("thread"): gist_job["thread"].join()

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: a one-off request on the command line, or what a person types
    if ONE_OFF: return " ".join(sys.argv[2:])
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line

# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    messages, drop = resume(), 0                         # current inputs: the conversation so far
    add(messages, {"role": "user", "content": stamp(capture_input())})
    while True:
        if LIMIT and not drop and len(json.dumps(messages)) > LIMIT: drop += 1; continue   # test hook: as if the API had said "prompt is too long"
        try:
            if drop:
                messages, drop = compact(messages, drop), 0
                remember(messages[0])                    # persistence: the trace marks where the conversation was summarized
            output = blocks(request_response(max_tokens=16384, **assemble_context(messages)).content)
        except BadRequestError as e:                     # too long to send: summarize on the next pass
            if "prompt is too long" not in str(e): raise
            drop += 1
            continue
        add(messages, {"role": "assistant", "content": output})   # persistence: on disk before any command runs
        results = handle_output(output)
        if results:                                      # a command ran: send back what it printed, and go again
            add(messages, {"role": "user", "content": results})
            refresh_gist(messages)                       # the gist: a turn is done
            continue
        refresh_gist(messages)                           # the gist: a turn is done
        if ONE_OFF: break                                # stop: a one-off request is done
        add(messages, {"role": "user", "content": stamp(capture_input())})   # hand back: the person's next message

try: control_flow()
finally: finish_gist()
