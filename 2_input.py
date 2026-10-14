# /// script
# dependencies = ["anthropic"]
# ///
import os, sys
from anthropic import Anthropic

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic(base_url="https://api.deepseek.com/anthropic", api_key=os.environ["DEEPSEEK_API_KEY"])   # DeepSeek, in the Anthropic Messages format
MODEL = "deepseek-flash"
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

# ── input ───────────────────────────────────────────────────────────────────
def capture_input():                                     # input: a one-off request on the command line, or what a person types
    if len(sys.argv) > 1: return " ".join(sys.argv[1:])
    line = ""
    while not line.strip(): line = input("< ")           # Enter on an empty line: ask again
    return line
message = capture_input()                                # input: the request, typed or from the command line

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": message}])
print(output.model_dump_json(indent=2))
