# Saved for Later reel

`exports/saved-for-later.mp4`: 1920 × 1080, 60 fps, 15.5 s, on a #FCEDBC background. It's built to sit next to the Vision Health reel: the iPhone 17 here has the same outer size and position as the Vision Health phone (414 × 868, centred), and it swipes up from below at the start and up and away at the end, the same way.

The screen is the Saved for Later artifact (claude.ai/artifact/N9RkMtzioecmgYkXGn7SfD) with the same markup, styles, curves and arc maths. It's sized to the phone screen, and its motion is replayed on a fixed timeline so every frame renders exactly:

| Time | What happens |
| --- | --- |
| 0 – 1 s | The phone swipes up from below |
| 0.65 – 2.4 s | "09/26 · What I saved for later in September" rises line by line out of a blur |
| 3.85 s | After the artifact's 2 s hold, the dock springs up |
| 5 – 6.4 s | The pointer glides onto the folder, which lifts on hover, then clicks |
| 6.4 – 8.5 s | The ten saves fan out of the folder along the arc |
| 8.5 – 12.2 s | It scrolls up through the rest of them and back |
| 12.4 – 13.2 s | The pointer moves off and clicks empty space; the cards go back into the folder |
| 14.6 – 15.5 s | The phone swipes up and away |

The only change to the artifact: its stage is 9:16 and the phone screen is taller, so the arc is bent as if the screen were 9:16, which keeps the cards inside the screen.

```sh
node saved/render.mjs                     # → exports/saved-for-later.mp4 (about 2 min)
node saved/render.mjs --stills 6 8 10     # PNG stills to check a moment
```

The timings are in the `T` object in `index.html`. The fonts (Instrument Serif and Instrument Sans, OFL) are embedded in `assets/fonts.js`, so the page renders the same offline.
