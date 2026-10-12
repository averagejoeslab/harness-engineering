# /// script
# dependencies = ["anthropic"]
# ///
from anthropic import Anthropic

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
def request_response(each=lambda event: None, **request):   # model interface: requests a response, which streams back piece by piece to each()
    with client.messages.stream(model=MODEL, **request) as stream:
        for event in stream: each(event)
        return stream.get_final_message()

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: captures what a person types
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line
input = capture_input()                                  # input: what a person types while it runs

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": input}])
print(output.model_dump_json(indent=2))
