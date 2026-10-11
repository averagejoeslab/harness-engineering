# Harness engineering

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

An agent has two parts: **a model** and **a harness**.

**Agent = Harness(Model)**

## The model

A model predicts. Tokens go in, it returns the most probable next token, and that token is added to the input. It repeats until it predicts `<eos>`, the end-of-sequence token.

```
            ┌──────────── append ◄────────────┐
            ▼                                 │
TokensIn ─► Model ─► most probable next token ─┤
                                               │
                                     is it <eos>? ── yes ─► TokensOut
```

**TokensOut = Model(TokensIn)**

That's all it does.

## The harness

The harness is everything else. It's been called a framework, a scaffold, a runtime and an orchestration layer, and the industry has mostly settled on *harness*.

Think of the model as an engine. On its own, it just turns. The harness is the rest of the vehicle: it's what makes the engine go somewhere.

Every harness does five things. These are its primitives:

| Primitive | What it does |
|---|---|
| **Input** | captures what comes in |
| **Context** | assembles what the model is shown |
| **Model interface** | requests a response from the model |
| **Output** | handles the response: shows it, or runs it as a tool |
| **Control flow** | decides what happens next: go again, hand back, or stop |

```
┌──────────────────────── control flow ─────────────────────────┐
│                                                                │
│  input ─► context ─► model interface ─► output ─┬─► person     │
│    ▲                    (the model)              │             │
│    └────────────────── a tool's result ──────────┘             │
└────────────────────────────────────────────────────────────────┘
```

## quark

A quark is one of the smallest particles there is. **quark** is the smallest agent: the five primitives and nothing more. It's all in [`quark.py`](./quark.py):

```python
def capture_input():
    return input("> ")


def assemble_context(conversation):
    instructions = f"You are quark, an agent. You act through bash, in {os.getcwd()}. Today is {datetime.date.today()}."
    return {"system": instructions, "tools": [bash], "messages": conversation}


def request_response(context):
    return model.messages.create(model="claude-sonnet-5-5", max_tokens=16384, **context)


def handle_output(response):
    tool_results = []
    for block in response.content:
        if block.type == "text":
            print(block.text)
        if block.type == "tool_use":
            ran = subprocess.run(block.input["command"], shell=True, capture_output=True, text=True)
            tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": ran.stdout + ran.stderr or "(no output)"})
    return tool_results


def control_flow():
    conversation = []
    while True:
        conversation.append({"role": "user", "content": capture_input()})
        while True:
            response = request_response(assemble_context(conversation))
            conversation.append({"role": "assistant", "content": response.content})
            tool_results = handle_output(response)
            if not tool_results:
                break                                    # done: hand back to the person
            conversation.append({"role": "user", "content": tool_results})   # a tool ran: go again
```

Each function is one primitive, and `control_flow()` holds the other four. The inner loop is what makes it an agent: while the model asks for tools, the results go back and it goes again.

## Run it

You need [uv](https://docs.astral.sh/uv/) and an [Anthropic API key](https://console.anthropic.com/).

```bash
export ANTHROPIC_API_KEY=your-key
uv run quark.py
```

```
> How many lines are in fruit.txt, and what is today?
`fruit.txt` has 2 lines (according to `wc -l`, which counts newline characters). Today is Wednesday, October 7, 2026.
```

Ctrl-C quits.

> [!WARNING]
> quark runs the model's shell commands without asking. Run it somewhere you can afford to lose.

## From quark to production

quark works, but it isn't ready to run unattended. Getting it there means asking one question of every primitive, for each concern, in turn:

| Concern | The question |
|---|---|
| Persistence | what should outlast the session? |
| Safety | what could do harm here? |
| Resilience | what could fail here? |
| Observability | what should we record here? |
| Performance | what's slow or costly here? |
| Evaluation | how do we know it still works? |

Persistence comes first, because the other concerns depend on what outlasts a session.

### Persistence

When quark stops, everything goes with it: the task in progress, and anything you told it. Persistence gives it memory, in four kinds:

| Memory | What it holds | Where |
|---|---|---|
| **Working** | the conversation, sent with every request | the context |
| **Episodic** | what happened: every message of every session | `.quark/episodes/`, one file per session |
| **Semantic** | what's true: facts, one per line | `.quark/memory/memory.md` |
| **Procedural** | how to do things: one skill per file | `.quark/skills/` |

Two primitives change. It's all in [`quark_persistence.py`](./quark_persistence.py).

**Control flow** writes every message to disk as it happens, so episodic memory is the harness's job, not the model's:

```python
def add(conversation, message):                          # one message, two places: working memory and episodic memory
    conversation.append(message)
    remember(message)
```

It also picks up a session that ended mid-task. A command that was running when it stopped may or may not have run, so quark is told to check:

```python
def resume():                                            # the task in progress: continue a session that ended mid-task
    ...
    if last["role"] == "assistant":                      # it stopped while commands were running
        add(conversation, {"role": "user", "content": [{"type": "tool_result", "tool_use_id": block["id"], "is_error": True,
            "content": "[interrupted: it may or may not have run. Check before repeating it.]"} for block in last["content"] if block["type"] == "tool_use"]})
```

**Context** tells quark what its memories are and how to use them, then shows it what it already knows: its facts, and an index of its skills.

```python
You have four memories:
- Working memory: this conversation.
- Semantic memory: facts that stay true, one per line as "- subject: fact", in .quark/memory/memory.md. ...
- Procedural memory: skills, one file per method that worked, in .quark/skills/<name>.md. ...
- Episodic memory: every message of every session, one JSON object per line, in .quark/episodes/. ...

Before a task, check what you know: facts first, then skills, then past sessions.
```

quark writes facts and skills itself, with bash, the same way it does everything else. No new tools.

```bash
uv run quark_persistence.py
```

### The rest

The other five concerns follow the same pattern: ask the question of each primitive, change what needs changing, then check that the concerns before it still hold.

Claude Code, Cursor and every other agent are these same five primitives, hardened in these ways.
