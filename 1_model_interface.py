# /// script
# dependencies = ["anthropic"]
# ///
from anthropic import Anthropic

# ── model interface ─────────────────────────────────────────────────────────
client = Anthropic()
MODEL = "claude-sonnet-5-5"
def request_response(**request):                         # model interface: requests a response from the model
    return client.messages.create(model=MODEL, **request)

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": "The tests are failing. Find out why and fix it."}])
print(output.model_dump_json(indent=2))
