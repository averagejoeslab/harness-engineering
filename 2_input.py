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

# ── input ───────────────────────────────────────────────────────────────────
def capture_input(prompt="> "):                          # input: captures what a person types
    while True:
        print(prompt, end="", flush=True)
        line = sys.stdin.readline()
        if not line: return "/q"                         # end of input (Ctrl-D): nothing more is coming
        if line.strip(): return line.rstrip("\n")        # Enter on an empty line: a fresh prompt, as in a terminal
        prompt = "> "
input = capture_input()                                  # input: what a person types while it runs
if input == "/q": sys.exit()

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": input}])
print(output.model_dump_json(indent=2))
