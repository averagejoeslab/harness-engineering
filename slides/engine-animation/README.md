# The Engine Test

A tap-through 3D animation for teaching harness engineering. An engine (the model) turns input into output that piles up on the floor. Then a car body (the harness) is built around it one primitive at a time, made ready for production by swapping in better parts, and driven around a test track.

## Present it

Open `index.html` in Chrome, Edge, Firefox or Safari. No build step and no server needed.

| Action | Keys |
|---|---|
| Next step (or finish the current animation) | click, tap, Space, Enter, → |
| Previous step | ← or Back |
| Start over | Home or Restart |
| Speaker notes | N or Notes |
| Look around | drag |
| Full screen | your browser's full-screen shortcut (F11, or Ctrl+Cmd+F on a Mac) |

## Offline

Three.js r128 is bundled in `vendor/`, so the animation runs offline. The fonts load from Google Fonts. Without a connection the page falls back to system fonts and still works.

## Changing it

Everything lives in `index.html`. The `STEPS` array near the bottom of the script holds each step's caption, speaker note and animation, in order.

## License

The animation is part of the course, under [CC BY 4.0](../../LICENSE-CC-BY-4.0), and its code under the [MIT License](../../LICENSE). See the [README](../../README.md#license). Three.js, in `vendor/three.min.js`, is under its own MIT License.
