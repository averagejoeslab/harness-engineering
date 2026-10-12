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

def show(event):                                         # output: text, shown as it's written
    if event.type == "text": print(event.text, end="", flush=True)
    if event.type == "content_block_stop" and event.content_block.type == "text": print()

def handle_output(output):                               # output: handles the model's outputs, running each command it asks for
    results = []
    for block in output:
        if block.type == "tool_use":
            print(f"$ {block.input['cmd']}")
            done = subprocess.run(block.input["cmd"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, errors="replace")
            print(done.stdout)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": done.stdout or f"(exit {done.returncode})"})  # input: from the world
    return results

# ── input ───────────────────────────────────────────────────────────────────
def capture_input(prompt="> "):                          # input: captures what a person types
    while True:
        print(prompt, end="", flush=True)
        line = sys.stdin.readline()
        if not line: return "/q"                         # end of input (Ctrl-D): nothing more is coming
        if line.strip(): return line.rstrip("\n")        # Enter on an empty line: a fresh prompt, as in a terminal
        prompt = "> "

# ── control flow ────────────────────────────────────────────────────────────
def control_flow():                                      # control flow: defines the shape of the loop
    chat = len(sys.argv) < 2                             # a request on the command line runs once; otherwise it's a chat
    input = " ".join(sys.argv[1:]) or capture_input()
    if input == "/q": return
    messages = [{"role": "user", "content": input}]
    while True:
        output = request_response(show, max_tokens=16384, tools=tools, messages=messages).content
        messages.append({"role": "assistant", "content": output})
        results = handle_output(output)
        if results:                                      # a command ran: send back what it printed, and go again
            messages.append({"role": "user", "content": results})
            continue
        if not chat or (input := capture_input("\n> ")) == "/q":
            break                                        # stop: a request from the command line is done, or /q
        messages.append({"role": "user", "content": input})   # hand back: the person's next message

control_flow()
