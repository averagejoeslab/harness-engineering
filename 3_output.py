# /// script
# dependencies = ["anthropic"]
# ///
import subprocess
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

def show(event):                                         # output: the model's words, after <, shown as they're written
    if event.type == "content_block_start" and event.content_block.type == "text": print("< ", end="")
    if event.type == "text": print(event.text.replace("\n", "\n  "), end="", flush=True)
    if event.type == "content_block_stop" and event.content_block.type == "text": print()

def nested(result):                                      # output: what a command printed, nested under it with |_
    return "  |_ " + "\n     ".join(result.rstrip("\n").split("\n"))

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
    while not line.strip(): line = input("> ")           # Enter on an empty line: ask again
    return line
input = capture_input()                                  # input: what a person types while it runs

output = request_response(show, max_tokens=16384, tools=tools, messages=[{"role": "user", "content": input}]).content
results = handle_output(output)                          # what the commands printed: nothing sends it back yet
