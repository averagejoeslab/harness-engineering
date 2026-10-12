# /// script
# dependencies = ["anthropic"]
# ///
import subprocess, sys
from anthropic import Anthropic

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
def request_response(each=lambda event: None, **request):   # model interface: requests a response, which streams back piece by piece to each()
    with client.messages.stream(model=MODEL, **request) as stream:
        for event in stream: each(event)
        return stream.get_final_message()

# ── output: the one tool ────────────────────────────────────────────────────
tools = [{"name": "shell", "description": "Run a shell command", "input_schema": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}]

thinking = {"type": "adaptive", "display": "summarized"}  # output: ask for a summary of its thinking, to show

def show(event):                                         # output: its thinking after ∴ in gray, its words after >, shown as they're written
    if event.type == "content_block_start" and event.content_block.type == "thinking": print("\033[90m∴ ", end="")
    if event.type == "content_block_start" and event.content_block.type == "text": print("> ", end="")
    if event.type in ("thinking", "text"): print(getattr(event, event.type).replace("\n", "\n  "), end="", flush=True)
    if event.type == "content_block_stop" and event.content_block.type in ("thinking", "text"): print("\033[0m")

def nested(result):                                      # output: what a command printed, nested under it with └
    return "  └ " + "\n    ".join(result.rstrip("\n").split("\n"))

def handle_output(output):                               # output: handles the model's outputs, running each command it asks for
    results = []
    for block in output:
        if block.type == "tool_use":
            print(f"$ {block.input['cmd']}")
            done = subprocess.run(block.input["cmd"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            result = done.stdout or f"(exit {done.returncode})"
            print(nested(result))
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})  # input: from the world
    return results

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: captures what a person types
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line

# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    chat = len(sys.argv) < 2                             # a request on the command line runs once; otherwise it's a chat
    input = " ".join(sys.argv[1:]) or capture_input()
    messages = [{"role": "user", "content": input}]
    while True:
        output = request_response(show, max_tokens=16384, thinking=thinking, tools=tools, messages=messages).content
        messages.append({"role": "assistant", "content": output})
        results = handle_output(output)
        if results:                                      # a command ran: send back what it printed, and go again
            messages.append({"role": "user", "content": results})
            continue
        if not chat: break                               # stop: a request from the command line is done
        messages.append({"role": "user", "content": capture_input()})   # hand back: the person's next message

control_flow()
