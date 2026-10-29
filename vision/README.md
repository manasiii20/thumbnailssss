# Vision Health walkthrough reel

`exports/vision-health-walkthrough.mp4`: 1920 × 1080, 60 fps, 30.5 s. It shows screens only. The phone swipes up from the bottom at the start, and everything swipes up and away at the end, so the reel loops smoothly. The whole timeline plays at `SLOW` = 1.25× its scripted speed.

Every screen is rebuilt as real UI, so it stays sharp at full HD. Only the drawn artwork is cut from the captures in `source/`.

| Time | What happens |
| --- | --- |
| 0 – 3 s | The phone swipes up on the splash dot, which becomes the app icon on **Welcome to Vision Health**. Tap **Get Started** |
| 3 – 7 s | **Connect your devices**: searching, the smartwatch card, **CONNECT** → **✓ CONNECTED**, **Cool, let’s move forward** |
| 7 – 15 s | "Aryan, we know nothing…", Question 1, the vision number typed in, Questions 2–5 with the answers collecting at the top |
| 15 – 21 s | **Summary**, then **Analysis** with the screen-distance alert |
| 21 – 25 s | Analysis steps left and the Time in Daylight chart slides in beside it |
| 25 – 29 s | Both slide out; **Sharing** and **Eye Games** slide in |
| 29 – 30.5 s | Everything swipes up and away |

```sh
python3 vision/extract.py                    # after changing anything in source/ → assets/*.png + assets/embedded.js
node vision/render.mjs                       # → exports/vision-health-walkthrough.mp4 (about 3 min)
node vision/render.mjs --stills 3 9.5 15     # PNG stills to check a moment
```

Open `index.html` in Chrome to play and scrub it. All timings are in the TIMELINE section of its script. Each step starts from a time variable (`T_MORPH`, `T_FOUND`, `T_READY`, `STEP`, `T_SPREAD` …), so you can retime a step by changing one number. Builders for screens that aren't in this cut are still in the file: the activity pages, Eye Health Education, Sharing, the Color Match game and Your Experience.

The font is Inter, which is close to SF Pro. If Inter isn't installed, the page falls back to the system font, which is SF Pro on a Mac.
