# /// script
# dependencies = ["anthropic"]
# ///
from anthropic import Anthropic

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: captures what a person types
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line
message = capture_input()                                # input: what a person types while it runs

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": message}])
print(output.model_dump_json(indent=2))
