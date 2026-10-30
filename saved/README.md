# Saved for Later reel

`exports/saved-for-later.mp4`: 1920 × 1080, 60 fps, a 9.4 s seamless loop on a #FCEDBC background. The iPhone 17 stays still in the frame and has the same size and position as the Vision Health phone (414 × 868, centred).

The screen is the Saved for Later artifact (claude.ai/artifact/N9RkMtzioecmgYkXGn7SfD) with the same markup, styles, curves and arc maths, replayed on a fixed timeline:

| Time | What happens |
| --- | --- |
| 0.35 – 1.75 s | "09/26 · What I saved for later in September" rises line by line out of a blur |
| 1.8 s | The dock springs up right after |
| 2.8 – 3.85 s | The pointer glides onto the folder, which lifts, then clicks |
| 3.85 – 6.6 s | The ten saves fan out of the folder along the arc and rest there |
| 6.6 s | Click the folder again: the cards fly back in, the same way they came out |
| 7.7 – 9.4 s | The pointer leaves, the dock drops and the headline fades, back to the first frame |

The only change to the artifact: its stage is 9:16 and the phone screen is taller, so the arc is bent as if the screen were 9:16, which keeps the cards inside the screen.

```sh
node saved/render.mjs                     # → exports/saved-for-later.mp4 (about 2 min)
node saved/render.mjs --stills 6 8 10     # PNG stills to check a moment
```

The timings are in the `T` object in `index.html`. The fonts (Instrument Serif and Instrument Sans, OFL) are embedded in `assets/fonts.js`, so the page renders the same offline.
