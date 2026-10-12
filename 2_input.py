# /// script
# dependencies = ["anthropic"]
# ///
import sys
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

# ── input ───────────────────────────────────────────────────────────────────
def capture_input(prompt="> "):                          # input: captures what a person types
    while True:
        print(prompt, end="", flush=True)
        line = sys.stdin.readline()
        if not line: return "/q"                         # end of input (Ctrl-D): nothing more is coming
        if line.strip(): return line.rstrip("\n")        # Enter on an empty line: a fresh prompt, as in a terminal
        prompt = "> "
input = " ".join(sys.argv[1:]) or capture_input()        # input: from the command line, or from a person
if input == "/q": sys.exit()

output = request_response(max_tokens=16384, tools=tools, messages=[{"role": "user", "content": input}])
print(output.model_dump_json(indent=2))
