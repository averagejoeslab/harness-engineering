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

output = request_response(max_tokens=16384, messages=[{"role": "user", "content": "The tests are failing. Find out why and fix it."}])
print(output.model_dump_json(indent=2))
