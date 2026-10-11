# /// script
# dependencies = ["anthropic"]
# ///
import subprocess, os, datetime, json, glob, re
from anthropic import Anthropic

model = Anthropic()
bash = {"name": "bash", "description": "Run a shell command",
        "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}}
EPISODE = f".quark/episodes/{datetime.datetime.now():%Y-%m-%dT%H-%M-%S}.jsonl"


def capture_input():
    return input("> ")


def remember(message):                                   # episodic memory: the harness writes every message as it happens
    os.makedirs(os.path.dirname(EPISODE), exist_ok=True)
    with open(EPISODE, "a") as file:
        file.write(json.dumps(message, default=lambda block: block.model_dump(exclude_none=True)) + "\n")


def add(conversation, message):                          # one message, two places: working memory and episodic memory
    conversation.append(message)
    remember(message)


def facts():                                             # semantic memory: what stays true
    return open(".quark/memory/memory.md").read().strip() if os.path.exists(".quark/memory/memory.md") else "(none yet)"


def skills():                                            # procedural memory: an index built from each skill's header
    index = []
    for path in sorted(glob.glob(".quark/skills/*.md")):
        about = re.search(r"^description:\s*(.+)$", open(path).read(), re.M)
        index.append(f"- {path}: {about[1] if about else '(no description)'}")
    return "\n".join(index) or "(none yet)"


def assemble_context(conversation):
    instructions = f"""You are quark, an agent. You act through bash, in {os.getcwd()}. Today is {datetime.date.today()}.

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
    return {"system": instructions, "tools": [bash], "messages": conversation}


def request_response(context):
    return model.messages.create(model="claude-sonnet-5-5", max_tokens=16384, **context)


def handle_output(response):
    tool_results = []
    for block in response.content:
        if block.type == "text":
            print(block.text)
        if block.type == "tool_use":
            ran = subprocess.run(block.input["command"], shell=True, capture_output=True, text=True)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": ran.stdout + ran.stderr or "(no output)"})
    return tool_results


def resume():                                            # the task in progress: continue a session that ended mid-task
    global EPISODE
    episodes = sorted(glob.glob(".quark/episodes/*.jsonl"))
    if not episodes:
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


control_flow()
