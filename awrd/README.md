# Are We Really Deciding? reel

482 × 326, rendered at 2x (964 × 652), 60 fps. It's a 15.1 s seamless loop on a white frame with a thin red border and the five pale guide lines from the design.

| Time | What happens |
| --- | --- |
| 0.35 – 2.0 s | "so, do you think / about your thinking?" types out |
| 2.25 s | The first character drops in from the top and pushes the text down |
| 3.15 s | The character sinks to the row; the text slides out of the bottom |
| 3.6 – 4.4 s | Four more characters drop in from the top, one after another |
| 4.65 – 5.6 s | "meet your work biases!" types out under them |
| 6.05 s | The characters rise; the text backspaces away |
| 6.65 s | A dark-theme Google search bar appears, as wide as the row of characters |
| 7.15 – 8.4 s | "decision sprint \| Miroverse" types into it |
| 8.85 s | The Miroverse Decision Sprint page slides up |
| 9.5 – 10.3 s | The cursor glides to **Use template** and clicks |
| 10.45 s | The page zooms in and the board opens on Day 1 |
| 11.55 s | The board swipes left to Day 2 |
| 12.65 s | The board swipes up to Assess your thinking |
| 14.15 s | Everything swipes up off the frame; the white frame is back, and the loop starts again |

Miro's own toolbars stay fixed while the board swipes underneath them.

The lettering and the characters are your own pixels, cut from the design frames. Typing reveals the monospace lettering one 17.75 px cell at a time. The search text uses Roboto.

```sh
python3 awrd/embed.py      # after changing anything in assets/
node awrd/render.mjs       # → exports/are-we-really-deciding@2x.mp4 (906 frames)
```

All timings are in the `t` object at the top of the script in `index.html`.
