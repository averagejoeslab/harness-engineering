# Harness Engineering, Without Code

By **[Chase Dovey](https://cdovey.dev/)** · [Average Joes Lab](https://github.com/averagejoeslab)

## What is an agent?

An **agent** is anything that loops over three steps: it observes, it thinks, and it acts. Then it does it again. You're one: you notice something, you decide what to do, you do it, and you see what happened.

## The mind and the body

A **language model** is only the thinking part. You give it words, and it predicts the next word, over and over, until it predicts it's done. That's all it does. It can't see anything you don't hand it, and nothing it writes happens in the world. It's a mind with no body.

A **harness** is the body: everything around the model that lets it observe and act. **Harness engineering** is building that body, so something that only predicts words can work in the world.

A harness has five parts, and each one does part of the loop:

- **Input** is how the world gets in: what a person asks, and what happens when the agent acts.
- **Context** is what the model is shown each time it thinks: who it is, what it can do, and what's happened so far.
- **The model interface** is how the harness reaches the model: it sends the context and brings back what the model thinks.
- **Output** is how its decisions become actions, like running a command.
- **Control flow** is the loop: it feeds what happened back in, and decides whether to go again, hand back to the person, or stop.

## Building one, a part at a time

Give it a small job: a project with a bug, and the request *"The tests are failing. Find out why and fix it."* Then build the body one part at a time, and watch what each version can do, and what stops it.

### 1. Reach the model

We send it the request, and it answers. It wants to look at the code, and it may even write out a command to do it. But nothing carries that command out, so it's only words. It can think, but it can't act. And the request was written in ahead of time, so no one else can ask it anything.

### 2. Let someone ask

Now a person can type a request. But it still answers only in words.

### 3. Let it act

We give it a tool: a way to ask for a command to be run, and something that actually runs it. Now it looks at the project. But what it sees goes nowhere. It acted once and stopped, like opening a door and never looking through it.

### 4. Let it keep going

We feed what happened back to it, and let it go again. Now it looks, runs the tests, sees which one fails, fixes the bug, and runs them again to check. **This is an agent.**

But ask it who it is, and the model we used said it was a different company's AI, because nothing told it otherwise. It's working without knowing what it is, where it is, or what time it is.

### 5. Tell it what it is

**Context** is the agent's working memory: whatever isn't in it, the agent doesn't have in mind. So each time it thinks, we show it three things:

- **Its mind:** who it is, what drives it, and how careful to be.
- **Its body:** what it can do, and how best to do it.
- **The world:** what's been said, what each action returned, and when, so it always knows what "now" is.

That memory has a limit. When it fills up, the oldest part is summarized to make room.

Now when you ask who it is, it knows, and it checks its surroundings instead of guessing.

## The model is replaceable

Only one part, the model interface, knows which model is inside. Everything else deals in plain things: messages, requests to act, and results. To put a different model in the body, you change how the harness reaches it. The body stays the same.

## What to take away

The model decides what to do. The harness decides what it can see, what it can do, and when it goes again. Most of what makes an agent good or bad, such as what it knows about itself, what it's allowed to touch, and whether it checks its work, is decided in the harness. That's the part you engineer.
