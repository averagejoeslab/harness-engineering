# /// script
# dependencies = ["anthropic"]
# ///
import subprocess, sys, os, datetime, json, glob, re, atexit
from anthropic import Anthropic

model = Anthropic(max_retries=3)                         # resilience: retry a request that fails
bash = {"name": "bash", "description": "Run a shell command",
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}
EPISODE = f".quark/episodes/{datetime.datetime.now():%Y-%m-%dT%H-%M-%S}.jsonl"   # persistence: this session, on disk
BOX = f"quark-{os.getpid()}"                             # safety: the container commands run in
RECORD = os.path.expanduser("~/.quark/record.jsonl")     # observability: where each step is written down


def capture_input():
    return " ".join(sys.argv[1:]) or input("\n> ")      # evaluation: a request can come from the command line


def remember(message):                                   # persistence: episodic memory, every message as it happens
    os.makedirs(os.path.dirname(EPISODE), exist_ok=True)
    with open(EPISODE, "a") as file:
        file.write(json.dumps(message, default=lambda block: block.model_dump(exclude_none=True)) + "\n")


def add(conversation, message):                          # persistence: one message, two places, in the request and on disk
    conversation.append(message)
    remember(message)


def facts():                                             # persistence: semantic memory, what stays true
    return open(".quark/memory/memory.md").read().strip() if os.path.exists(".quark/memory/memory.md") else "(none yet)"


def skills():                                            # persistence: procedural memory, an index built from each skill's header
    index = []
    for path in sorted(glob.glob(".quark/skills/*.md")):
        about = re.search(r"^description:\s*(.+)$", open(path).read(), re.M)
        index.append(f"- {path}: {about[1] if about else '(no description)'}")
    return "\n".join(index) or "(none yet)"


def assemble_context(conversation):
    instructions = f"""You are quark, an agent. You act through bash, in {os.getcwd()}. Today is {datetime.date.today()}.
Your commands run in a container that sees only this folder, with no network. The person approves each one, and each is stopped after a minute.

You have four memories:
- Working memory: this conversation.
- Semantic memory: facts that stay true, one per line as "- subject: fact", in .quark/memory/memory.md. When you learn something worth keeping (who someone is, what they prefer, a correction), add it. When a fact changes, replace its line.
- Procedural memory: skills, one file per method that worked, in .quark/skills/<name>.md. Each starts with a "description:" line saying when to use it, then the steps. When you work out a method likely to come up again, write it down.
- Episodic memory: every message of every session, one JSON object per line, in .quark/episodes/. The harness writes it; you search it with grep. This session is {EPISODE}.

Before a task, check what you know: facts first, then skills, then past sessions.

Facts:
{facts()}

Skills:
{skills()}"""
    return {"system": instructions, "tools": [bash], "messages": conversation,
            "cache_control": {"type": "ephemeral"}}      # performance: reuse what was already sent


def request_response(context):
    response = model.messages.create(model="claude-sonnet-5-5", max_tokens=16384, **context)
    usage = response.usage
    record(tokens_in=usage.input_tokens, written=usage.cache_creation_input_tokens, cached=usage.cache_read_input_tokens,
           tokens_out=usage.output_tokens)
    return response


def start_box():                                         # safety: a container that sees this folder and nothing else
    here = os.getcwd()
    subprocess.run(["docker", "run", "-d", "--rm", "--name", BOX, "--network", "none", "--user", f"{os.getuid()}:{os.getgid()}",
                    "-e", "HOME=/tmp", "-v", f"{here}:{here}", "-w", here, "python:3.13", "sleep", "infinity"],
                   check=True, capture_output=True)
    atexit.register(subprocess.run, ["docker", "rm", "-f", BOX], capture_output=True)


def handle_output(response):
    tool_results = []
    for block in response.content:
        if block.type == "text":
            print("< " + block.text.replace("\n", "\n  "))
        if block.type == "tool_use":
            command = block.input["command"]
            print(f"$ {command}")
            if allowed(command):                         # safety: in the box; resilience: stopped after a minute
                ran = subprocess.run(["docker", "exec", BOX, "timeout", "60", "sh", "-c", command], capture_output=True, text=True)
                result = ran.stdout + ran.stderr or "(no output)"
                if ran.returncode == 124:
                    result += "\n[stopped: it ran for over a minute]"
                record(command=command, exit=ran.returncode)
            else:
                result = "The person said no."
                record(command=command, refused=True)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
    return tool_results


def allowed(command):                                    # safety: nothing runs without a yes
    return input("  run this? [y/N] ").strip().lower() == "y"


def record(**step):                                      # observability: one line per step, outside the box
    os.makedirs(os.path.dirname(RECORD), exist_ok=True)
    with open(RECORD, "a") as log:
        log.write(json.dumps({"time": datetime.datetime.now().isoformat(timespec="seconds"), **step}) + "\n")


def resume():                                            # persistence: continue a session that ended mid-task
    global EPISODE
    episodes = sorted(glob.glob(".quark/episodes/*.jsonl"))
    if not episodes or sys.argv[1:]:                     # evaluation: each request from the command line starts fresh
        return []
    conversation = [json.loads(line) for line in open(episodes[-1])]
    last = conversation[-1]
    unfinished = last["role"] == "user" or any(block["type"] == "tool_use" for block in last["content"])
    if not unfinished or input("continue the unfinished session? [y/N] ").strip().lower() != "y":
        return []
    EPISODE = episodes[-1]                               # carry on in the same file
    if last["role"] == "assistant":                      # it stopped while commands were running
        add(conversation, {"role": "user", "content": [{"type": "tool_result", "tool_use_id": block["id"], "is_error": True,
            "content": "[interrupted: it may or may not have run. Check before repeating it.]"} for block in last["content"] if block["type"] == "tool_use"]})
    return conversation


def control_flow():
    start_box()
    conversation = resume()
    while True:
        if not conversation or conversation[-1]["role"] == "assistant":
            add(conversation, {"role": "user", "content": capture_input()})
        while True:
            response = request_response(assemble_context(conversation))
            add(conversation, {"role": "assistant", "content": response.content})
            tool_results = handle_output(response)
            if not tool_results:
                break                                    # done: hand back to the person
            add(conversation, {"role": "user", "content": tool_results})   # a tool ran: go again
        if sys.argv[1:]:
            break                                        # evaluation: a request from the command line runs once


control_flow()
