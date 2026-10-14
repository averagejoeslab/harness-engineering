# Slides

Slide decks for teaching this repo, built from its code and its real runs. There's a master deck with everything, and four cut from it for a purpose:

| Deck | Slides | For | Present | Print |
|---|---|---|---|---|
| **Master** | 71 | everything, in the README's order | [master.html](./master.html) | [master.pdf](./pdf/master.pdf) |
| **Lightning talk** | 12 | 10 minutes: Agent = Harness(Model), the five primitives, and the six questions | [lightning.html](./lightning.html) | [lightning.pdf](./pdf/lightning.pdf) |
| **Conference talk** | 40 | 30 to 40 minutes: one slide per build step, then evaluation and Safety & Security in depth | [conference.html](./conference.html) | [conference.pdf](./pdf/conference.pdf) |
| **Workshop** | 76 | half a day: everything, plus an agenda, a setup check, and three hands-on labs | [workshop.html](./workshop.html) | [workshop.pdf](./pdf/workshop.pdf) |
| **Video series** | 74 | nine episodes, one per video, each opening on its own title card | [video.html](./video.html) | [video.pdf](./pdf/video.pdf) |

Each build step uses the same four slides: what the primitive is, its code, a real run, and what it still can't do. Every slide has speaker notes.

## Presenting

Open a deck's `.html` file in a browser. The arrow keys, space, or a click move between slides; **N** shows the speaker notes; **F** goes full screen. The address ends in the slide's number, so you can link to one. The slides use IBM Plex Sans and JetBrains Mono from Google Fonts, so present online, or use the PDF.

## Changing them

The slides are written in Python, in [`src/`](./src/): `lib.py` holds the look and the slide kinds, and each `s_*.py` holds one part of the course. [`build.py`](./build.py) chooses which slides go in each deck, then writes:

- `<deck>.html`, to present from;
- `decks/<deck>/project/`, the same deck in the Slides format of Claude's artifacts: a `deck.json` index and one `<section>` per slide.

```bash
python3 build.py                                  # every deck, as .html and in decks/
for d in master lightning conference workshop video; do node print.js $d.html pdf/$d.pdf; done   # the PDFs (needs Playwright)
```

Change a slide in `src/` and rebuild: every deck that uses it changes too.

## License

The slides are under [CC BY 4.0](../LICENSE-CC-BY-4.0), and the code that builds them under the [MIT License](../LICENSE). See the [README](../README.md#license).
