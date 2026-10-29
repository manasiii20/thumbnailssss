# Vision Health walkthrough reel

`exports/vision-health-walkthrough.mp4`: 1920 × 1080, 60 fps, 20.1 s. It shows screens only, with no captions or titles. One iPhone, centred, walks through the app in the order of the prototype screen recording. At the end, four phones spread out side by side, in the style of the Claude Design cut.

Every screen is rebuilt as real UI (text, buttons, bars, the color wheel), so it stays sharp at full HD. Only the drawn artwork is cut from the captures in `source/`: the activity icons, the smartwatch, the doctor portraits and the Eye Health Education illustrations. All motion settles with the same soft ease. Nothing floats or wobbles.

| Time | What happens |
| --- | --- |
| 0 – 2.4 s | The phone rises in on the splash dot. The dot sends out two rings, then becomes the app icon on **Welcome to Vision Health**. Tap **Get Started** |
| 2.4 – 5.5 s | **Connect your devices**: the orbits flow while it searches, the Noise ColorFit Ultra 3 card slides up, **CONNECT** turns into **✓ CONNECTED**, then **Cool, let’s move forward** |
| 5.5 – 12.2 s | "Aryan, we know nothing…", then **Okay, I’m ready**. Question 1, the vision number typed in (-0.5 and -0.75, 2 years), then Questions 2 to 5. Each answer is added to the list at the top |
| 12.2 – 13.6 s | **Summary**: the tab bar slides up and the progress bars fill |
| 13.6 – 16.5 s | **Analysis**: the activity bars grow, **iPhone is Too Close** turns into **Screen Distance ✓** |
| 16.5 – 20.1 s | Analysis, Eye Games, Color Match results and Virtual Consultation side by side, then they fade out |

```sh
python3 vision/extract.py                    # after changing anything in source/ → assets/*.png + assets/embedded.js
node vision/render.mjs                       # → exports/vision-health-walkthrough.mp4 (about 3 min)
node vision/render.mjs --stills 3 9.5 15     # PNG stills to check a moment
```

Open `index.html` in Chrome to play and scrub it. All timings are in the TIMELINE section of its script. Each step starts from a time variable (`T_MORPH`, `T_FOUND`, `T_READY`, `STEP`, `T_SPREAD` …), so you can retime a step by changing one number. Builders for screens that aren't in this cut are still in the file: the activity pages, Eye Health Education, Sharing, the Color Match game and Your Experience.

The font is Inter, which is close to SF Pro. If Inter isn't installed, the page falls back to the system font, which is SF Pro on a Mac.
